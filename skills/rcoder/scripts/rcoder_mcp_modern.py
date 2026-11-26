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
COMMANDS_DIR = core.SKILL_DIR.parents[1] / "commands"
PROMPT_PREFIX = "rcoder_cmd_"
ELICITATION_METHOD = "elicitation/create"
DESTRUCTIVE_PATH_RE = re.compile(
    r"(?i)(auth|credential|secret|token|migration|schema|delete|remove|drop)"
)
LIVE_RESOURCES = {
    "rcoder://repo/map": (
        "repo-map", "Repository symbol map",
        "PageRank-ranked bounded symbol map produced by repo_map.py.", "text/markdown",
    ),
    "rcoder://memory/recall": (
        "memory-recall", "Episodic memory recall",
        "Recent decisions, fixes, invariants, and FTS5 recall from rcoder_memory.py.",
        "application/json",
    ),
    "rcoder://capsule/latest": (
        "capsule-latest", "Latest context capsule",
        "Bounded path and Git snapshot produced by context_snapshot.py.", "text/markdown",
    ),
}
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


# ---------------------------------------------------------------- live resources

def _parse_command_md(md_path: Path) -> tuple[str, str]:
    text = md_path.read_text(encoding="utf-8")
    desc = f"Run RCoder {md_path.stem} workflow"
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            frontmatter, body = parts[1], parts[2].strip()
            match = re.search(r'^description:\s*["\']?(.+?)["\']?\s*$', frontmatter, re.M)
            if match:
                desc = match.group(1).strip()
    return desc, body.strip()


def _command_parser():
    script_dir = Path(__file__).resolve().parents[3] / "scripts"
    if script_dir.is_dir() and str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))
    try:
        from sync_plugins import parse_command_md
        return parse_command_md
    except ImportError:
        return _parse_command_md


def client_supports_elicitation(params: dict) -> bool:
    meta = params.get("_meta")
    if not isinstance(meta, dict):
        return False
    capabilities = meta.get("capabilities")
    return isinstance(capabilities, dict) and "elicitation" in capabilities


def destructive_gate(params: dict) -> dict | None:
    if not client_supports_elicitation(params) or params.get("name") != "rcoder_apply_verify":
        return None
    arguments = params.get("arguments")
    if not isinstance(arguments, dict) or bool(arguments.get("confirm_destructive")):
        return None
    edits = arguments.get("edits")
    if not isinstance(edits, list):
        return None
    sensitive = sorted({
        str(edit.get("path", "")) for edit in edits
        if isinstance(edit, dict) and DESTRUCTIVE_PATH_RE.search(str(edit.get("path", "")))
    })
    if not sensitive:
        return None
    message = (
        "The requested edits touch sensitive code paths: " + ", ".join(sensitive) +
        ". Confirm the exact diff before RCoder applies it."
    )
    return {
        "content": [{"type": "text", "text": message}],
        "isError": True,
        "structuredContent": {
            "ok": False,
            "error": {
                "code": "CONFIRMATION_REQUIRED",
                "message": message,
                "recovery_hint": (
                    "Review the diff, then repeat tools/call with confirm_destructive=true "
                    "after elicitation/create returns an acceptance."
                ),
            },
            "elicitation": {
                "method": ELICITATION_METHOD,
                "params": {
                    "message": message,
                    "requestedSchema": {
                        "type": "object",
                        "properties": {
                            "confirm": {"type": "boolean", "description": "Apply the reviewed diff."}
                        },
                        "required": ["confirm"],
                    },
                    "sensitive_paths": sensitive,
                },
            },
        },
    }


def live_resources() -> list:
    return [
        {"uri": uri, "name": name, "title": title, "description": description, "mimeType": mime}
        for uri, (name, title, description, mime) in LIVE_RESOURCES.items()
    ]


def read_live_resource(uri: str) -> dict:
    meta = LIVE_RESOURCES.get(uri)
    if meta is None:
        raise core.RpcError(ERR_INVALID_PARAMS, f"unknown live resource: {uri}")
    if uri in ("rcoder://repo/map", "rcoder://capsule/latest"):
        script, arguments = (
            ("repo_map.py", ["--root", str(core.State.root), "--budget", "2048", "--format", "default"])
            if uri == "rcoder://repo/map" else
            ("context_snapshot.py", [str(core.State.root), "--max-paths", "80"])
        )
        code, stdout, stderr = core.run_helper(script, arguments)
        if code != 0:
            raise core.RpcError(ERR_INVALID_PARAMS, f"{script} failed: {stderr.strip()}")
        text = stdout
    else:
        from rcoder_memory import RCoderMemoryStore
        store = RCoderMemoryStore(core.State.root)
        text = json.dumps(
            {
                "tool": "RCoder",
                "resource": "memory/recall",
                "episodes": store.recent(10),
                "recall": store.recall_for_context(query=core.State.root.name, limit=6),
            },
            ensure_ascii=False,
            indent=2,
        )
    return {"uri": uri, "mimeType": meta[3], "text": core.clip(text)}


def command_prompts() -> dict:
    if not COMMANDS_DIR.is_dir():
        return {}
    parser = _command_parser()
    prompts = {}
    for md_file in sorted(COMMANDS_DIR.glob("*.md")):
        name = f"{PROMPT_PREFIX}{md_file.stem}"
        description, _ = parser(md_file)
        prompts[name] = {
            "name": name,
            "description": description,
            "arguments": [{
                "name": "args",
                "description": "Arguments or target for the RCoder command.",
                "required": False,
            }],
        }
    return prompts


def build_command_prompt(name: str, arguments: dict) -> dict | None:
    prompts = command_prompts()
    if name not in prompts:
        return None
    md_file = COMMANDS_DIR / f"{name[len(PROMPT_PREFIX):]}.md"
    _, body = _command_parser()(md_file)
    value = str(arguments.get("args", "")).strip() if isinstance(arguments, dict) else ""
    text = body.replace("$ARGUMENTS", value or "(no arguments supplied)")
    return {
        "description": prompts[name]["description"],
        "messages": [{"role": "user", "content": {"type": "text", "text": text}}],
    }


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
    elif method == "tools/call":
        blocked = destructive_gate(params)
        if blocked is not None:
            return blocked
        if client_supports_elicitation(params) and isinstance(params.get("arguments"), dict) \
                and "confirm_destructive" in params["arguments"]:
            params = dict(params)
            params["arguments"] = {
                key: value for key, value in params["arguments"].items()
                if key != "confirm_destructive"
            }
        previous = core.State.protocol
        core.State.protocol = MODERN_PROTOCOL
        try:
            return core.handle(method, params)
        finally:
            core.State.protocol = previous
    elif method == "resources/list":
        return contract.paginate_result(
            method, {"resources": live_resources() + core.resource_index()}, params
        )
    elif method == "prompts/list":
        prompts = list(command_prompts().values())
        prompts.extend({"name": key, **value} for key, value in core.PROMPTS.items())
        return contract.paginate_result(method, {"prompts": prompts}, params)
    elif method == "prompts/get":
        name = params.get("name")
        if isinstance(name, str) and name.startswith(PROMPT_PREFIX):
            built = build_command_prompt(name, params.get("arguments") or {})
            if built is None:
                raise core.RpcError(ERR_INVALID_PARAMS, f"unknown prompt: {name}")
            return built
        previous = core.State.protocol
        core.State.protocol = MODERN_PROTOCOL
        try:
            return core.handle(method, params)
        finally:
            core.State.protocol = previous
    else:
        uri = params.get("uri")
        if method == "resources/read" and isinstance(uri, str) and uri.startswith("skill://"):
            result = {"contents": [read_skill_file(uri)]}
        elif method == "resources/read" and isinstance(uri, str) and uri in LIVE_RESOURCES:
            result = {"contents": [read_live_resource(uri)]}
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
    # D-022: the shared core already paginates these collections; re-paginating here
    # would page an already-truncated page and drop a valid nextCursor.
    # The shared core paginates these for real; re-paginating would page an
    # already-truncated page and drop a valid nextCursor. skills/* keep the
    # modern path because the legacy core has no skills extension.
    if method != "skills/list" and method in core.PAGINATED_METHODS:
        return result
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
