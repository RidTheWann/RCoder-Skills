#!/usr/bin/env python3
"""Black-box conformance tests for the optional RCoder Streamable HTTP transport."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SERVER = ROOT / "skills" / "rcoder" / "scripts" / "rcoder_mcp_http.py"
TOKEN = "rcoder-test-token-" + "a" * 48
ORIGIN = "http://localhost:3000"
PROTOCOL = "2026-07-28"


def request(port, method, params=None, *, token=TOKEN, origin=ORIGIN, protocol=PROTOCOL,
            method_header=None, name=None, accept="application/json, text/event-stream",
            path="/mcp", body_override=None):
    rpc = {"jsonrpc": "2.0", "id": 1, "method": method, "params": dict(params or {})}
    if protocol is not None:
        rpc["params"].setdefault("_meta", {})["io.modelcontextprotocol/protocolVersion"] = protocol
    data = json.dumps(rpc).encode("utf-8") if body_override is None else body_override
    headers = {"Content-Type": "application/json", "Accept": accept}
    if token is not None:
        headers["Authorization"] = "Bearer " + token
    if origin is not None:
        headers["Origin"] = origin
    if protocol is not None:
        headers["MCP-Protocol-Version"] = protocol
    headers["Mcp-Method"] = method if method_header is None else method_header
    if name is not None:
        headers["Mcp-Name"] = name
    elif method == "tools/call":
        headers["Mcp-Name"] = (params or {}).get("name", "")
    elif method == "resources/read":
        headers["Mcp-Name"] = (params or {}).get("uri", "")
    elif method == "prompts/get":
        headers["Mcp-Name"] = (params or {}).get("name", "")
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=data,
                                 headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status, response.headers, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.headers, error.read()


def main():
    with tempfile.TemporaryDirectory(prefix="rcoder-http-test-") as temp:
        env = dict(os.environ, RCODER_MCP_TOKEN=TOKEN)
        process = subprocess.Popen(
            [sys.executable, str(SERVER), "--root", temp, "--port", "0",
             "--allowed-origin", ORIGIN],
            cwd=ROOT, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE, text=True, encoding="utf-8",
        )
        try:
            line = process.stderr.readline().strip()
            assert line.startswith("RCoder MCP HTTP listening on http://127.0.0.1:"), line
            port = int(line.split(":")[2].split("/")[0])

            status, headers, body = request(port, "server/discover")
            assert status == 200 and headers.get_content_type() == "application/json"
            discover = json.loads(body)["result"]
            assert discover["supportedVersions"] == [PROTOCOL]
            assert headers.get("Cache-Control") == "no-store"
            assert headers.get("Access-Control-Allow-Origin") == ORIGIN

            status, _, body = request(port, "tools/list")
            listing = json.loads(body)["result"]
            assert status == 200 and len(listing["tools"]) == 10
            assert listing["nextCursor"]
            status, _, body = request(port, "tools/list", {"cursor": listing["nextCursor"]})
            second = json.loads(body)["result"]
            assert status == 200 and second["tools"] and len(second["tools"]) <= 10

            status, _, body = request(port, "tools/call",
                                      {"name": "rcoder_doctor", "arguments": {}},
                                      name="rcoder_doctor")
            structured = json.loads(body)["result"]
            assert status == 200 and "structuredContent" in structured

            status, _, body = request(port, "skills/list")
            skills = json.loads(body)["result"]["skills"]
            assert status == 200 and len(skills) == 1
            assert skills[0]["resources"] and skills[0]["resources"][0]["digest"].startswith("sha256:")

            assert request(port, "server/discover", token=None)[0] == 401
            assert request(port, "server/discover", origin="http://evil.example")[0] == 403
            assert request(port, "server/discover", protocol="2025-06-18")[0] == 400
            assert request(port, "server/discover", method_header="tools/list")[0] == 400
            assert request(port, "server/discover", accept="application/json")[0] == 406
            assert request(port, "server/discover", path="/wrong")[0] == 404
            assert request(port, "server/discover", protocol=None)[0] == 400
            assert request(port, "tools/call",
                           {"name": "rcoder_doctor", "arguments": {}}, name="wrong")[0] == 400

            note = {
                "jsonrpc": "2.0", "method": "notifications/initialized",
                "params": {"_meta": {"io.modelcontextprotocol/protocolVersion": PROTOCOL}},
            }
            status, _, body = request(port, "notifications/initialized", note["params"],
                                      body_override=json.dumps(note).encode("utf-8"))
            assert status == 202 and body == b""

            get_request = urllib.request.Request(f"http://127.0.0.1:{port}/mcp", method="GET")
            try:
                urllib.request.urlopen(get_request, timeout=5)
            except urllib.error.HTTPError as error:
                assert error.code == 405
            else:
                raise AssertionError("GET stream must not be exposed by the stateless adapter")
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
    print("PASS MCP Streamable HTTP: token, Origin, headers, pagination, structured output, inline manifest")


if __name__ == "__main__":
    main()
