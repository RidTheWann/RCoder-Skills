#!/usr/bin/env python3
"""Deterministic tests for the dual-era RCoder MCP entry point (rcoder_mcp_modern.py).

The adapter runs as a real subprocess over stdio. The tests prove stateless 2026-07-28
behavior, Skills-over-MCP manifests (digests recomputed independently from disk), and that
legacy handshake sessions are unchanged. They do not prove that any host uses these features.
"""
import base64
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / "skills" / "rcoder"
ADAPTER = SKILL_DIR / "scripts" / "rcoder_mcp_modern.py"
VERSION = re.search(r'version:\s*"(\d+\.\d+\.\d+)"', (SKILL_DIR / "SKILL.md").read_text(
    encoding="utf-8")).group(1)
MODERN = "2026-07-28"
META = {"io.modelcontextprotocol/protocolVersion": MODERN,
        "io.modelcontextprotocol/clientInfo": {"name": "test", "version": "0"},
        "io.modelcontextprotocol/clientCapabilities": {}}
SERVER_INFO_KEY = "io.modelcontextprotocol/serverInfo"
MUTATING_TOOLS = {"rcoder_apply_verify", "rcoder_learn"}
LEGACY_INIT = {"jsonrpc": "2.0", "id": 0, "method": "initialize",
               "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                          "clientInfo": {"name": "test", "version": "0"}}}


def modern(request_id, method, params=None):
    return {"jsonrpc": "2.0", "id": request_id, "method": method,
            "params": {**(params or {}), "_meta": dict(META)}}


def session(messages, root, extra_args=()):
    payload = "\n".join(json.dumps(item) for item in messages) + "\n"
    done = subprocess.run([sys.executable, str(ADAPTER), "--root", str(root), *extra_args],
                          input=payload, text=True, encoding="utf-8", errors="replace",
                          capture_output=True, timeout=120, check=False)
    assert done.returncode == 0, done.stderr
    parsed = [json.loads(line) for line in done.stdout.splitlines() if line.strip()]
    return {item.get("id"): item for item in parsed if "id" in item}, parsed, done.stderr


def expected_manifest():
    """Recompute the skill manifest from disk without using any adapter code."""
    files = [SKILL_DIR / "SKILL.md"]
    for subtree in ("references", "assets"):
        base = SKILL_DIR / subtree
        if base.is_dir():
            files += sorted((path for path in base.rglob("*") if path.is_file() and not path.is_symlink()
                             and not any(part.startswith(".") for part in path.relative_to(SKILL_DIR).parts)),
                            key=lambda path: path.as_posix())
    return {f"skill://rcoder/{path.relative_to(SKILL_DIR).as_posix()}":
            ("sha256:" + hashlib.sha256(path.read_bytes()).hexdigest(), len(path.read_bytes()))
            for path in files}


def main():
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)

        # --- server/discover and stateless framing --------------------------------------------
        by_id, parsed, stderr = session([modern(1, "server/discover")], root)
        result = by_id[1]["result"]
        assert result["resultType"] == "complete" and result["supportedVersions"] == [MODERN]
        assert {"tools", "resources", "prompts"} <= set(result["capabilities"])
        assert result["capabilities"]["extensions"]["io.modelcontextprotocol/skills"] == {"directoryRead": False}
        info = result["_meta"][SERVER_INFO_KEY]
        assert info["name"] == "rcoder" and info["version"] == VERSION
        assert isinstance(result["ttlMs"], int) and result["ttlMs"] > 0
        assert result["cacheScope"] in ("public", "private") and result["instructions"]
        assert len(parsed) == 1 and stderr == "", "stdout must be protocol-only and stderr quiet"

        by_id, parsed, _ = session([
            modern(1, "server/discover"),
            {"jsonrpc": "2.0", "method": "notifications/cancelled",
             "params": {"requestId": 99, "_meta": dict(META)}},
            {"jsonrpc": "2.0", "id": 2, "method": "server/discover",
             "params": {"_meta": {**META, "io.modelcontextprotocol/protocolVersion": "1900-01-01"}}},
            {"jsonrpc": "2.0", "id": 3, "method": "server/discover",
             "params": {"_meta": {**META, "io.modelcontextprotocol/protocolVersion": 7}}},
            modern(4, "ping"), modern(5, "initialize", {"protocolVersion": "2025-06-18"}),
            modern(6, "no/such/method"),
        ], root)
        assert len(parsed) == 6, "a notification must not produce a response"
        assert by_id[2]["error"]["code"] == -32022 and by_id[2]["error"]["data"]["requested"] == "1900-01-01"
        assert MODERN in by_id[2]["error"]["data"]["supported"]
        assert by_id[3]["error"]["code"] == -32602
        assert by_id[4]["error"]["code"] == -32601 and by_id[5]["error"]["code"] == -32601
        assert by_id[6]["error"]["code"] == -32601

        # --- delegated methods gain resultType, serverInfo, and cache hints --------------------
        by_id, _, _ = session([
            modern(1, "tools/list"), modern(2, "tools/list"),
            modern(3, "tools/call", {"name": "rcoder_doctor", "arguments": {}}),
            modern(4, "tools/call", {"name": "nope", "arguments": {}}),
            modern(5, "resources/list"), modern(6, "resources/templates/list"), modern(7, "prompts/list"),
            modern(8, "resources/read", {"uri": "rcoder://specialist/not-a-module"}),
            modern(9, "resources/read", {"uri": "rcoder://references/mcp-transport-engineering"}),
            modern(10, "resources/read", {"uri": "rcoder://templates/adr-template"}),
        ], root)
        listing = by_id[1]["result"]
        assert listing["tools"] == by_id[2]["result"]["tools"], "tools/list order must be deterministic"
        assert listing["resultType"] == "complete" and listing["ttlMs"] > 0 and listing["cacheScope"]
        assert listing["tools"] and all(
            tool.get("title") and tool["annotations"]["readOnlyHint"] is (tool["name"] not in MUTATING_TOOLS)
            for tool in listing["tools"]
        )
        call = by_id[3]["result"]
        assert call["resultType"] == "complete" and "structuredContent" in call and not call.get("isError")
        assert call["_meta"][SERVER_INFO_KEY]["name"] == "rcoder"
        assert by_id[4]["error"]["code"] == -32602
        for request_id in (5, 6, 7):
            assert by_id[request_id]["result"]["resultType"] == "complete"
            assert by_id[request_id]["result"]["ttlMs"] > 0
        assert by_id[8]["error"]["code"] == -32602, "modern resource-not-found is Invalid params"
        assert by_id[9]["result"]["contents"][0]["text"].startswith("# MCP")
        assert by_id[10]["result"]["contents"][0]["text"].startswith("# ")

        # --- legacy sessions are unchanged -------------------------------------------------------
        by_id, parsed, _ = session([
            LEGACY_INIT, {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 1, "method": "ping"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "resources/read",
             "params": {"uri": "rcoder://specialist/not-a-module"}},
            modern(4, "server/discover"),
            {"jsonrpc": "2.0", "id": 5, "method": "ping"},
        ], root)
        assert by_id[0]["result"]["protocolVersion"] == "2025-06-18"
        assert by_id[1]["result"] == {} and by_id[5]["result"] == {}
        assert "resultType" not in by_id[2]["result"] and "ttlMs" not in by_id[2]["result"]
        assert by_id[3]["error"]["code"] == -32002, "legacy not-found code must not change"
        assert by_id[4]["result"]["resultType"] == "complete", "eras may interleave in one process"

        # --- Skills over MCP -------------------------------------------------------------------------
        manifest = expected_manifest()
        assert 1 <= len(manifest) <= 512 and all("/scripts/" not in uri for uri in manifest)
        by_id, _, _ = session([modern(1, "skills/list"), modern(2, "skills/get", {"uri": "skill://rcoder/SKILL.md"})],
                              root)
        listed = by_id[1]["result"]
        assert listed["resultType"] == "complete" and listed["ttlMs"] > 0 and listed["cacheScope"]
        assert "nextCursor" not in listed and len(listed["skills"]) == 1
        entry = listed["skills"][0]
        assert entry["uri"] == "skill://rcoder/SKILL.md" and by_id[2]["result"]["skill"] == entry
        assert entry["frontmatter"]["name"] == "rcoder" and entry["frontmatter"]["description"]
        assert entry["frontmatter"]["metadata"]["version"] == VERSION
        assert entry["resources"][0]["uri"] == "skill://rcoder/SKILL.md", "SKILL.md must lead the manifest"
        served = {item["uri"]: (item["digest"], item["size"]) for item in entry["resources"]}
        assert served == manifest and len(served) == len(entry["resources"])
        try:
            import yaml  # optional independent check of the frontmatter parser
        except ImportError:
            print("note: PyYAML unavailable; frontmatter parser cross-check skipped")
        else:
            text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
            assert entry["frontmatter"] == yaml.safe_load(text.split("---")[1]), "frontmatter must match YAML"

        reads = [modern(10 + index, "resources/read", {"uri": uri}) for index, uri in enumerate(manifest)]
        by_id, _, _ = session(reads, root)
        for index, uri in enumerate(manifest):
            read = by_id[10 + index]["result"]
            assert read["resultType"] == "complete" and read["ttlMs"] > 0
            content = read["contents"][0]
            assert content["uri"] == uri and content["mimeType"]
            data = content["text"].encode("utf-8") if "text" in content else base64.b64decode(content["blob"])
            assert "sha256:" + hashlib.sha256(data).hexdigest() == manifest[uri][0], uri
            assert len(data) == manifest[uri][1], uri

        hostile = ["skill://rcoder/../scripts/rcoder_mcp.py", "skill://rcoder/scripts/rsaver.py",
                   "skill://rcoder/references/../SKILL.md/../../README.md", "skill://other/SKILL.md",
                   "skill://rcoder", "skill://rcoder/references/.env", "skill://rcoder/references/link.md"]
        by_id, _, _ = session([modern(20 + i, "resources/read", {"uri": uri}) for i, uri in enumerate(hostile)]
                              + [modern(40 + i, "skills/get", {"uri": uri}) for i, uri in enumerate(hostile)]
                              + [modern(60, "skills/get", {"uri": 5}), modern(61, "skills/get"),
                                 modern(62, "skills/list", {"cursor": "abc"})], root)
        for index, uri in enumerate(hostile):
            if uri in manifest:
                continue  # a real, listed file such as a symlink-free duplicate must not exist here
            assert by_id[20 + index]["error"]["code"] == -32602, uri
            assert by_id[40 + index]["error"]["code"] == -32602, uri
        assert all(by_id[i]["error"]["code"] == -32602 for i in (60, 61, 62))

        # --- CLI surface -------------------------------------------------------------------------------
        done = subprocess.run([sys.executable, str(ADAPTER), "--print-config", "generic", "--command", "python3"],
                              capture_output=True, text=True, timeout=30)
        assert done.returncode == 0 and "rcoder_mcp_modern.py" in done.stdout, done.stdout
        assert "mcpServers" in json.loads(done.stdout)
        done = subprocess.run([sys.executable, str(ADAPTER), "--version"], capture_output=True, text=True, timeout=30)
        assert done.returncode == 0 and VERSION in done.stdout
        done = subprocess.run([sys.executable, str(ADAPTER), "--root", "/definitely/not/here"],
                              capture_output=True, text=True, input="", timeout=30)
        assert done.returncode == 2

    print("RCoder modern MCP tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
