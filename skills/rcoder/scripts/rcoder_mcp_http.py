#!/usr/bin/env python3
"""Optional stateless Streamable HTTP transport for the RCoder modern MCP endpoint."""
from __future__ import annotations

import argparse
import base64
import hmac
import json
import os
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rcoder_contract as contract  # noqa: E402
import runtime_bootstrap  # noqa: E402

MODERN_SERVER = Path(__file__).resolve().with_name("rcoder_mcp_modern.py")
VALID_ACCEPT = {"application/json", "text/event-stream"}
NAME_METHODS = {"tools/call": "name", "resources/read": "uri", "prompts/get": "name"}
HEADER_MISMATCH = -32020


def worker_environment(token_env: str) -> dict[str, str]:
    """Remove the HTTP bearer token and prevent one-shot workers from spawning sidecars."""
    environment = {key: value for key, value in os.environ.items() if key != token_env}
    environment["RCODER_RUNTIME_DISABLE"] = "1"
    return environment


def encode_json(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def rpc_error(request_id, code: int, message: str, data=None) -> dict:
    error = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": request_id, "error": error}


def accept_types(value: str) -> set[str]:
    return {part.split(";", 1)[0].strip().lower() for part in value.split(",") if part.strip()}


def decode_mcp_name(value: str) -> str:
    """Decode the protocol Base64 sentinel and reject unsafe plain HTTP header values."""
    prefix, suffix = "=?base64?", "?="
    if value.startswith(prefix) and value.endswith(suffix):
        encoded = value[len(prefix):-len(suffix)]
        try:
            result = base64.b64decode(encoded, validate=True).decode("utf-8")
        except (ValueError, UnicodeDecodeError) as error:
            raise ValueError("invalid Base64-encoded Mcp-Name header") from error
        if base64.b64encode(result.encode("utf-8")).decode("ascii") != encoded:
            raise ValueError("non-canonical Base64-encoded Mcp-Name header")
        return result
    if not value or value[0] in " \\t" or value[-1] in " \\t":
        raise ValueError("Mcp-Name with leading or trailing whitespace must use Base64 sentinel encoding")
    if any(not (0x20 <= ord(char) <= 0x7E or ord(char) == 0x09) for char in value):
        raise ValueError("Mcp-Name must be visible ASCII or use Base64 sentinel encoding")
    return value


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, handler, *, root, token, token_env, allowed_origins,
                 timeout, max_request_bytes, max_response_bytes, profile, tools, endpoint_path):
        super().__init__(address, handler)
        self.root = str(root)
        self.token = token
        self.token_env = token_env
        self.allowed_origins = frozenset(allowed_origins)
        self.request_timeout = timeout
        self.max_request_bytes = max_request_bytes
        self.max_response_bytes = max_response_bytes
        self.profile = profile
        self.tools = tools
        self.endpoint_path = endpoint_path


class Handler(BaseHTTPRequestHandler):
    server_version = "RCoder-MCP"
    sys_version = ""

    def log_message(self, fmt, *args):
        sys.stderr.write("rcoder-mcp-http: " + (fmt % args) + "\n")

    def _send(self, status: int, body: bytes = b"", *, origin=None, headers=None):
        self.send_response(status)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(body)))
        if body:
            self.send_header("Content-Type", "application/json")
        if origin is not None:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _check_origin(self):
        origin = self.headers.get("Origin")
        if origin is None:
            return None, None
        if origin not in self.server.allowed_origins:
            return None, (403, {"error": "Origin is not allowed"})
        return origin, None

    def do_OPTIONS(self):
        origin, problem = self._check_origin()
        if problem:
            status, payload = problem
            return self._send(status, encode_json(payload))
        self._send(204, b"", origin=origin, headers={
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type, Accept, "
                "MCP-Protocol-Version, Mcp-Method, Mcp-Name",
            "Access-Control-Max-Age": "600",
        })

    def do_GET(self):
        self._send(405, encode_json({"error": "GET streams and MCP sessions are not supported"}))

    def do_PUT(self):
        self._send(405, encode_json({"error": "only POST is supported"}))

    def do_DELETE(self):
        self._send(405, encode_json({"error": "MCP sessions are not supported"}))

    def do_POST(self):
        if urlsplit(self.path).path != self.server.endpoint_path:
            return self._send(404, encode_json({"error": "endpoint not found"}))
        origin, problem = self._check_origin()
        if problem:
            status, payload = problem
            return self._send(status, encode_json(payload))
        expected = ("Bearer " + self.server.token).encode("utf-8")
        supplied = self.headers.get("Authorization", "").encode("utf-8")
        if not hmac.compare_digest(supplied, expected):
            return self._send(401, encode_json({"error": "unauthorized"}), origin=origin,
                              headers={"WWW-Authenticate": "Bearer"})
        content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if content_type != "application/json":
            return self._send(415, encode_json({"error": "Content-Type must be application/json"}), origin=origin)
        if not VALID_ACCEPT.issubset(accept_types(self.headers.get("Accept", ""))):
            return self._send(406, encode_json({
                "error": "Accept must include application/json and text/event-stream"
            }), origin=origin)
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            return self._send(411, encode_json({"error": "Content-Length is required"}), origin=origin)
        if length <= 0 or length > self.server.max_request_bytes:
            return self._send(413, encode_json({"error": "request body is empty or exceeds the configured limit"}), origin=origin)
        try:
            request = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return self._send(400, encode_json(rpc_error(None, -32700, "parse error")), origin=origin)
        if not isinstance(request, dict) or request.get("jsonrpc") != "2.0" \
                or not isinstance(request.get("method"), str):
            return self._send(400, encode_json(rpc_error(None, -32600, "invalid request")), origin=origin)
        request_id = request.get("id")
        params = request.get("params") or {}
        if not isinstance(params, dict):
            return self._send(400, encode_json(rpc_error(request_id, -32602, "params must be an object")), origin=origin)
        # For protocol 2026-07-28 the notification response is 202 with no body.
        # Mirrored method/name/version headers are required for requests carrying an id.
        if "id" not in request:
            return self._send(202, b"", origin=origin)
        meta = params.get("_meta")
        requested_version = meta.get("io.modelcontextprotocol/protocolVersion") if isinstance(meta, dict) else None
        if requested_version != contract.MODERN_PROTOCOL:
            return self._send(400, encode_json(rpc_error(request_id, -32022,
                "protocol version metadata is missing or unsupported",
                {"supported": [contract.MODERN_PROTOCOL, *contract.LEGACY_PROTOCOLS],
                 "requested": requested_version})), origin=origin)
        if self.headers.get("MCP-Protocol-Version") != requested_version:
            return self._send(400, encode_json(rpc_error(request_id, HEADER_MISMATCH,
                "MCP-Protocol-Version header must match request metadata")), origin=origin)
        method = request["method"]
        if self.headers.get("Mcp-Method") != method:
            return self._send(400, encode_json(rpc_error(request_id, HEADER_MISMATCH,
                "Mcp-Method header must match JSON-RPC method")), origin=origin)
        name_key = NAME_METHODS.get(method)
        if name_key:
            expected_name = params.get(name_key)
            supplied_name = self.headers.get("Mcp-Name")
            if not isinstance(expected_name, str) or supplied_name is None:
                return self._send(400, encode_json(rpc_error(request_id, HEADER_MISMATCH,
                    "Mcp-Name header is required and must match request name or URI")), origin=origin)
            try:
                decoded_name = decode_mcp_name(supplied_name)
            except ValueError as error:
                return self._send(400, encode_json(rpc_error(request_id, HEADER_MISMATCH, str(error))), origin=origin)
            if decoded_name != expected_name:
                return self._send(400, encode_json(rpc_error(request_id, HEADER_MISMATCH,
                    "Mcp-Name header must match request name or URI")), origin=origin)
        command = [sys.executable, str(MODERN_SERVER), "--root", self.server.root,
                   "--profile", self.server.profile]
        if self.server.tools:
            command.extend(["--tools", self.server.tools])
        # HTTP workers are one-request children; only the long-lived HTTP server owns a session.
        worker_env = worker_environment(self.server.token_env)
        try:
            worker = subprocess.run(
                command, input=json.dumps(request, ensure_ascii=False) + "\n",
                text=True, encoding="utf-8", errors="replace",
                capture_output=True, timeout=self.server.request_timeout, check=False,
                cwd=self.server.root,
                env=worker_env,
            )
        except subprocess.TimeoutExpired:
            return self._send(504, encode_json(rpc_error(request_id, -32603, "MCP request timed out")), origin=origin)
        if worker.returncode != 0:
            sys.stderr.write("rcoder-mcp-http worker failed: " + worker.stderr[-2000:] + "\n")
            return self._send(502, encode_json(rpc_error(request_id, -32603, "MCP worker failed")), origin=origin)
        responses = [line for line in worker.stdout.splitlines() if line.strip()]
        if len(responses) != 1:
            sys.stderr.write("rcoder-mcp-http: worker returned an invalid response count\n")
            return self._send(502, encode_json(rpc_error(request_id, -32603, "invalid MCP worker response")), origin=origin)
        try:
            response = json.loads(responses[0])
        except json.JSONDecodeError:
            return self._send(502, encode_json(rpc_error(request_id, -32603, "invalid MCP worker JSON")), origin=origin)
        payload = encode_json(response)
        if len(payload) > self.server.max_response_bytes:
            return self._send(502, encode_json(rpc_error(request_id, -32603, "MCP response exceeds configured size limit")), origin=origin)
        status = 404 if response.get("error", {}).get("code") == -32601 else 200
        self._send(status, payload, origin=origin)


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--path", default="/mcp")
    parser.add_argument("--root", default=".")
    parser.add_argument("--profile", choices=("full", "minimal"), default="full")
    parser.add_argument("--tools", default="")
    parser.add_argument("--token-env", default="RCODER_MCP_TOKEN")
    parser.add_argument("--allowed-origin", action="append", default=[])
    parser.add_argument("--request-timeout", type=int, default=30)
    parser.add_argument("--max-request-bytes", type=int, default=1024 * 1024)
    parser.add_argument("--max-response-bytes", type=int, default=32 * 1024 * 1024)
    parser.add_argument("--version", action="version", version=f"RCoder MCP HTTP {contract.PRODUCT_VERSION}")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.host != "127.0.0.1":
        raise SystemExit("security error: RCoder MCP HTTP may bind only to 127.0.0.1")
    if not args.path.startswith("/") or "?" in args.path or "#" in args.path:
        raise SystemExit("invalid endpoint path")
    if (
        args.port < 0
        or args.port > 65535
        or args.request_timeout < 1
        or args.max_request_bytes < 1
        or args.max_response_bytes < 1
    ):
        raise SystemExit("invalid port, timeout, or request/response size limit")
    token = os.environ.get(args.token_env, "")
    if len(token) < 32:
        raise SystemExit(f"security error: set {args.token_env} to a random token of at least 32 characters")
    root = Path(args.root).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise SystemExit("root must be an existing directory")
    try:
        runtime_bootstrap.start_runtime_companion(root)
    except Exception:  # noqa: BLE001 - Runtime must never prevent HTTP MCP startup
        if os.environ.get("RCODER_RUNTIME_DEBUG") == "1":
            sys.stderr.write("RCoder Runtime companion startup failed; MCP remains available.\n")
    server = Server(
        (args.host, args.port), Handler, root=root, token=token, token_env=args.token_env,
        allowed_origins=args.allowed_origin, timeout=args.request_timeout,
        max_request_bytes=args.max_request_bytes, max_response_bytes=args.max_response_bytes,
        profile=args.profile, tools=args.tools.strip(),
        endpoint_path=args.path,
    )
    sys.stderr.write(f"RCoder MCP HTTP listening on http://127.0.0.1:{server.server_port}{args.path}\n")
    sys.stderr.flush()
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
