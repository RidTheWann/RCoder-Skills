#!/usr/bin/env python3
"""RCoder MCP server, dual-era entry point.

Serves the stateless MCP revision 2026-07-28 (per-request ``_meta``, ``server/discover``,
``resultType``, cache hints) and the Skills-over-MCP extension, while delegating every
legacy ``initialize``-based session (2025-06-18, 2025-03-26, 2024-11-05) to the unchanged
``rcoder_mcp`` core. A request is modern only when its params carry
``_meta["io.modelcontextprotocol/protocolVersion"]``; everything else takes the legacy path
byte for byte. Standard library only, read-only, no network, every path confined as in core.
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import mimetypes
import re
import sys
from base64 import b64encode
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rcoder_mcp as core  # noqa: E402  (sibling module; path set above)
import rcoder_contract as contract  # noqa: E402

MODERN_PROTOCOL = contract.MODERN_PROTOCOL
META_VERSION = "io.modelcontextprotocol/protocolVersion"
META_SERVER_INFO = "io.modelcontextprotocol/serverInfo"
SKILLS_EXTENSION = "io.modelcontextprotocol/skills"
ERR_UNSUPPORTED_VERSION = -32022
ERR_INVALID_PARAMS = -32602
ERR_METHOD_NOT_FOUND = -32601
ERR_INTERNAL = -32603
LEGACY_NOT_FOUND = -32002
CACHE_SCOPE = "private"
TTL_MS = {
    "server/discover": 3_600_000, "tools/list": 3_600_000, "prompts/list": 3_600_000,
    "resources/templates/list": 3_600_000, "resources/list": 60_000, "resources/read": 60_000,
    "skills/list": 300_000, "skills/get": 300_000,
}
REMOVED_IN_MODERN = {"initialize", "ping", "logging/setLevel", "resources/subscribe",
                     "resources/unsubscribe"}
INSTRUCTIONS = ("Read-only RCoder helpers. Call rcoder_scan at session start, route with "
                "rcoder_list_specialists and rcoder_validate_selection, and load only the "
                "specialist sections you need. The RCoder skill itself is served through "
                "skills/list and skills/get.")
SKILL_SUBTREES = ("references", "assets")
SKILL_MAX_FILES = 512
SKILL_MAX_BYTES = 16 * 1024 * 1024
# Plain YAML scalars that a YAML parser would type as non-strings: refuse rather than mismatch.
YAML_TYPED_RE = re.compile(
    r"(?i)(true|false|yes|no|on|off|y|n|null|~|[-+]?[0-9][0-9_.:eE+-]*|[-+]?\.[0-9]+|0x[0-9a-f]+|"
    r"[-+]?\.(inf|nan))")


class SkillError(Exception):
    """The bundled skill cannot be exposed faithfully; the extension is then not advertised."""


# ------------------------------------------------------------------ frontmatter

def parse_scalar(value: str):
    if value.startswith('"'):
        parsed = json.loads(value)
        if not isinstance(parsed, str):
            raise ValueError("unsupported quoted scalar")
        return parsed
    if value.startswith("'"):
        if len(value) < 2 or not value.endswith("'"):
            raise ValueError("unterminated single-quoted scalar")
        return value[1:-1].replace("''", "'")
    if value[0] in "[{|>&*!%@`#" or ": " in value or " #" in value or YAML_TYPED_RE.fullmatch(value):
        raise ValueError(f"unsupported plain scalar: {value!r}")
    return value


def parse_frontmatter(text: str) -> dict:
    """Parse flat string fields plus one level of nested string maps; anything else is refused."""
    lines = text.lstrip("\ufeff").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("SKILL.md must begin with YAML frontmatter")
    try:
        end = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration:
        raise ValueError("unterminated frontmatter") from None
    data, current = {}, None
    for raw in lines[1:end]:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        key, separator, value = raw.strip().partition(":")
        key, value = key.strip(), value.strip()
        if not separator or not key or "\t" in raw[:indent]:
            raise ValueError(f"unsupported frontmatter line: {raw!r}")
        if indent == 0:
            if value:
                data[key], current = parse_scalar(value), None
            else:
                data[key], current = {}, key
        else:
            if current is None or not value:
                raise ValueError(f"unsupported nested frontmatter line: {raw!r}")
            data[current][key] = parse_scalar(value)
    return data


# ----------------------------------------------------------------------- skill

def skill_paths():
    """Return (name, frontmatter, {uri: Path}) for the bundled skill, SKILL.md first."""
    skill_md = core.SKILL_DIR / "SKILL.md"
    try:
        frontmatter = parse_frontmatter(skill_md.read_bytes().decode("utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as error:
        raise SkillError(f"cannot expose SKILL.md: {error}") from error
    name = frontmatter.get("name")
    if not isinstance(name, str) or not core.NAME_RE.match(name) \
            or not isinstance(frontmatter.get("description"), str):
        raise SkillError("SKILL.md frontmatter needs a lowercase-hyphen name and a description")
    found = [("SKILL.md", skill_md)]
    for subtree in SKILL_SUBTREES:
        base = core.SKILL_DIR / subtree
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*"), key=lambda item: item.as_posix()):
            relative = path.relative_to(core.SKILL_DIR)
            if path.is_symlink() or not path.is_file() or core.is_sensitive(relative) \
                    or any(part.startswith(".") for part in relative.parts):
                continue
            found.append((relative.as_posix(), path))
    if len(found) > SKILL_MAX_FILES:
        raise SkillError(f"skill has more than {SKILL_MAX_FILES} files")
    return name, frontmatter, {f"skill://{name}/{relative}": path for relative, path in found}


def skill_entry() -> dict:
    name, frontmatter, files = skill_paths()
    manifest, total = [], 0
    for uri, path in files.items():
        data = path.read_bytes()
        total += len(data)
        manifest.append({"uri": uri, "digest": "sha256:" + hashlib.sha256(data).hexdigest(),
                         "size": len(data)})
    if total > SKILL_MAX_BYTES:
        raise SkillError("skill is larger than 16 MiB")
    return {"uri": f"skill://{name}/SKILL.md", "frontmatter": frontmatter, "resources": manifest}


def skills_available() -> bool:
    try:
        skill_paths()
    except SkillError as error:
        sys.stderr.write(f"rcoder-mcp: skills extension disabled: {error}\n")
        return False
    return True


def require_skills() -> None:
    try:
        skill_paths()
    except SkillError as error:
        raise core.RpcError(ERR_METHOD_NOT_FOUND, f"skills extension unavailable: {error}") from error


def skills_list(params: dict) -> dict:
    require_skills()
    return {"skills": [skill_entry()]}


def skills_get(params: dict) -> dict:
    require_skills()
    uri = params.get("uri")
    if not isinstance(uri, str):
        raise core.RpcError(ERR_INVALID_PARAMS, "skills/get requires a string uri")
    entry = skill_entry()
    if uri != entry["uri"]:
        raise core.RpcError(ERR_INVALID_PARAMS, f"unknown skill: {uri}")
    return {"skill": entry}


def read_skill_file(uri: str) -> dict:
    require_skills()
    path = skill_paths()[2].get(uri)
    if path is None:
        raise core.RpcError(ERR_INVALID_PARAMS, f"unknown skill resource: {uri}")
    data = path.read_bytes()
    mime = "text/markdown" if path.suffix == ".md" else \
        (mimetypes.guess_type(path.name)[0] or "application/octet-stream")
    try:
        return {"uri": uri, "mimeType": mime, "text": data.decode("utf-8")}
    except UnicodeDecodeError:
        return {"uri": uri, "mimeType": mime, "blob": b64encode(data).decode("ascii")}


# -------------------------------------------------------------------- protocol

def server_info() -> dict:
    return {"name": core.SERVER_NAME, "version": core.product_version()}


def discover() -> dict:
    capabilities = {"tools": {}, "resources": {}, "prompts": {}, "completions": {}}
    if skills_available():
        capabilities["extensions"] = {SKILLS_EXTENSION: {"directoryRead": False}}
    return {"supportedVersions": [MODERN_PROTOCOL], "capabilities": capabilities,
            "instructions": INSTRUCTIONS}


def modern_result(method: str, params: dict) -> dict:
    if method == "server/discover":
        result = discover()
    elif method == "skills/list":
        result = skills_list(params)
    elif method == "skills/get":
        result = skills_get(params)
    else:
        uri = params.get("uri")
        if method == "resources/read" and isinstance(uri, str) and uri.startswith("skill://"):
            result = {"contents": [read_skill_file(uri)]}
        else:
            previous = core.State.protocol
            core.State.protocol = MODERN_PROTOCOL  # unlocks titles and structuredContent in core
            try:
                result = core.handle(method, params)
            except core.RpcError as error:
                if method == "resources/read" and error.code == LEGACY_NOT_FOUND:
                    raise core.RpcError(ERR_INVALID_PARAMS, error.message) from error
                raise
            finally:
                core.State.protocol = previous
    return contract.paginate_result(method, result, params)


def finalize(method: str, result: dict) -> dict:
    result = dict(result)
    result.setdefault("resultType", "complete")
    meta = dict(result.get("_meta") or {})
    meta[META_SERVER_INFO] = server_info()
    result["_meta"] = meta
    if method in TTL_MS:
        result.setdefault("ttlMs", TTL_MS[method])
        result.setdefault("cacheScope", CACHE_SCOPE)
    return result


def reply_error(request_id, code: int, message: str, data=None) -> None:
    error = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    core.respond({"jsonrpc": "2.0", "id": request_id, "error": error})


def is_modern(request) -> bool:
    if not isinstance(request, dict) or request.get("jsonrpc") != "2.0" \
            or not isinstance(request.get("method"), str) or "id" not in request:
        return False
    params = request.get("params")
    meta = params.get("_meta") if isinstance(params, dict) else None
    return isinstance(meta, dict) and META_VERSION in meta


def serve_modern(request: dict) -> None:
    request_id, method, params = request["id"], request["method"], request["params"]
    version = params["_meta"][META_VERSION]
    if not isinstance(version, str):
        return reply_error(request_id, ERR_INVALID_PARAMS, "protocol version must be a string")
    if version != MODERN_PROTOCOL:
        return reply_error(request_id, ERR_UNSUPPORTED_VERSION, "Unsupported protocol version",
                           {"supported": [MODERN_PROTOCOL, *core.PROTOCOLS], "requested": version})
    if method in REMOVED_IN_MODERN:
        return reply_error(request_id, ERR_METHOD_NOT_FOUND,
                           f"method not found in protocol {MODERN_PROTOCOL}: {method}")
    try:
        result = finalize(method, modern_result(method, params))
    except core.RpcError as error:
        return reply_error(request_id, error.code, error.message)
    except ValueError as error:
        return reply_error(request_id, ERR_INVALID_PARAMS, str(error))
    except Exception as error:  # noqa: BLE001 - last-resort protocol guard, as in core
        sys.stderr.write(f"rcoder-mcp internal error: {error!r}\n")
        return reply_error(request_id, ERR_INTERNAL, "internal error")
    core.respond({"jsonrpc": "2.0", "id": request_id, "result": result})


_legacy_process_line = core.process_line


def process_line(line: str) -> None:
    try:
        request = json.loads(line)
    except ValueError:
        request = None
    if is_modern(request):
        serve_modern(request)
    else:
        _legacy_process_line(line)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    core.process_line = process_line  # core.serve() resolves this name at call time
    if "--print-config" in args:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = core.main(args)
        sys.stdout.write(buffer.getvalue().replace("rcoder_mcp.py", Path(__file__).name))
        return code
    return core.main(args)


if __name__ == "__main__":
    raise SystemExit(main())
