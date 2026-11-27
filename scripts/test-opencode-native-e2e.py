#!/usr/bin/env python3
"""Native OpenCode end-to-end regression with a local mock model provider.

This test starts the installed OpenCode executable, loads the real RCoder
plugin from an isolated workspace, connects the configured RCoder MCP server,
and captures the actual HTTP request bodies sent to a local mock provider.
No public model API or real credential is used.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS = ROOT / "skills" / "rcoder" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

from context_fabric import ContextFabric  # noqa: E402
from platform_runtime import (  # noqa: E402
    isolated_host_environment,
    link_or_copy,
    portable_temp_root,
    resolve_host_command,
    resolve_node_command,
)

MOCK_KEY = "local-fixture-key"


def runtime_binary() -> Optional[str]:
    explicit = os.environ.get("RCODER_RUNTIME_PATH")
    candidates = [explicit] if explicit else []
    on_path = shutil.which("rcoder-runtime")
    if on_path:
        candidates.append(on_path)
    candidates.append(str(ROOT / "runtime" / "target" / "debug" / "rcoder-runtime"))
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(Path(candidate).resolve())
    cargo = shutil.which("cargo")
    if not cargo:
        return None
    try:
        subprocess.run(
            [cargo, "build", "--manifest-path", str(ROOT / "runtime" / "Cargo.toml"),
             "-p", "rcoder-runtime"],
            capture_output=True, text=True, timeout=240, check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    built = ROOT / "runtime" / "target" / "debug" / "rcoder-runtime"
    return str(built) if built.is_file() else None


class QuietHTTPServer(ThreadingHTTPServer):
    def handle_error(self, request: object, client_address: object) -> None:
        pass


class MockProvider:
    def __init__(self) -> None:
        self.requests: list[dict] = []
        self.lock = threading.Lock()
        self.server = QuietHTTPServer(("127.0.0.1", 0), self.handler())
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    @property
    def port(self) -> int:
        return int(self.server.server_address[1])

    def handler(self):
        owner = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *_args: object) -> None:
                pass

            def _send(self, payload: object, content_type: str = "application/json") -> None:
                body = json.dumps(payload).encode()
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self) -> None:
                self._send({"data": [{"id": "e2e-model", "object": "model"}]})

            def do_POST(self) -> None:
                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length)
                try:
                    parsed = json.loads(raw)
                except (ValueError, UnicodeDecodeError):
                    parsed = {"raw": raw.decode("utf-8", "replace")}
                with owner.lock:
                    owner.requests.append(parsed)
                completion = {
                    "id": "mock-1", "object": "chat.completion", "created": 1,
                    "model": "e2e-model",
                    "choices": [{"index": 0, "message": {"role": "assistant",
                                "content": "E2E_OK"}, "finish_reason": "stop"}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                }
                if parsed.get("stream"):
                    chunk = {"id": "mock-1", "object": "chat.completion.chunk", "created": 1,
                             "model": "e2e-model", "choices": [{"index": 0,
                             "delta": {"content": "E2E_OK"}, "finish_reason": None}]}
                    end = {"id": "mock-1", "object": "chat.completion.chunk", "created": 1,
                           "model": "e2e-model", "choices": [{"index": 0, "delta": {},
                           "finish_reason": "stop"}]}
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream")
                    self.send_header("Cache-Control", "no-cache")
                    self.end_headers()
                    for payload in (chunk, end):
                        self.wfile.write(f"data: {json.dumps(payload)}\n\n".encode())
                    self.wfile.write(b"data: [DONE]\n\n")
                    self.wfile.flush()
                    return
                self._send(completion)

        return Handler

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()


class NativeOpenCodeE2ETests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.binary = runtime_binary()
        if cls.binary is None:
            raise unittest.SkipTest("rcoder-runtime binary is unavailable")
        cls.host = resolve_host_command("opencode")
        if not cls.host:
            raise unittest.SkipTest("OpenCode executable is unavailable")
        cls.node = resolve_node_command()

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(
            prefix="rcoder-native-e2e-", dir=str(portable_temp_root("opencode")))
        self.root = Path(self.temp.name).resolve()
        self.test_id = uuid.uuid4().hex[:10]
        self.rfc_marker = f"RFC_E2E_MARKER_{self.test_id}"
        self.runtime_marker = f"RUNTIME_E2E_MARKER_{self.test_id}"
        self.session = f"ses-e2e-{self.test_id}"
        self.provider = MockProvider()
        self._fixture()

    def tearDown(self) -> None:
        self.provider.close()
        if os.environ.get("RCODER_E2E_KEEP_FIXTURE") == "1":
            self.temp._finalizer.detach()
            print("E2E fixture retained:", self.root)
            return
        self.temp.cleanup()

    def _config(self) -> dict:
        return {
            "$schema": "https://opencode.ai/config.json",
            "model": "mock/e2e-model",
            "providers": {"mock": {
                "name": "Local Mock",
                "env": ["MOCK_API_KEY"],
                "package": "@opencode/ai/providers/openai-compatible",
                "settings": {"baseURL": f"http://127.0.0.1:{self.provider.port}/v1"},
                "models": {"e2e-model": {"name": "Local Mock E2E", "attachment": False}},
            }},
            "mcp": {"rcoder": {
                "type": "local",
                "command": [*self.node, str(ROOT / "launcher" / "rcoder-mcp.mjs"),
                            "--root", str(self.root)],
                "cwd": str(self.root),
                "environment": {
                    "RCODER_PYTHON": sys.executable,
                    "RCODER_RUNTIME_PATH": self.binary,
                },
            }},
        }

    def _fixture(self, *, seed_rfc: bool = True, runtime_path: Optional[str] = None) -> None:
        plugins = self.root / ".opencode" / "plugins"
        plugins.mkdir(parents=True)
        shutil.copy2(ROOT / ".opencode" / "plugins" / "rcoder.js", plugins / "rcoder.js")
        link_or_copy(ROOT / "skills", self.root / "skills")
        config = self._config()
        (self.root / "opencode.jsonc").write_text(json.dumps(config, indent=2), encoding="utf-8")
        (self.root / ".opencode" / "opencode.jsonc").write_text(
            json.dumps(config, indent=2), encoding="utf-8")

        if seed_rfc:
            fabric = ContextFabric(self.root)
            fabric.ensure_session(self.session)
            fabric.store_context(self.session, "objective", "E2E RFC marker", self.rfc_marker,
                                 source_ref="e2e-fixture", now=1000)

        self.env = isolated_host_environment(
            self.root, mock_key=MOCK_KEY, python_command=[sys.executable])

        task = self._cli("task", "create", "--project", str(self.root), "--objective",
                         f"{self.runtime_marker}: confirm runtime context reaches the model request",
                         "--acceptance", "Marker delivered", "--risk", "low", "--json")
        self._cli("task", "transition", "--project", str(self.root), "--id", task["id"],
                  "--to", "active", "--json")
        (self.root / ".rcoder").mkdir(exist_ok=True)
        self._set_workspace_options(
            runtime_path=runtime_path or str(self.binary),
            rfc_disabled=False,
            runtime_disabled=False,
        )

    def _cli(self, *args: str) -> dict:
        result = subprocess.run([self.binary, *args], capture_output=True, text=True,
                                timeout=30, env={**self.env, "HOME": str(self.root)})
        result.check_returncode()
        return json.loads(result.stdout)

    def _set_workspace_options(self, *, runtime_path: Optional[str],
                               rfc_disabled: bool, runtime_disabled: bool) -> None:
        options: dict = {}
        if runtime_path:
            options["runtime_path"] = runtime_path
        if rfc_disabled:
            options["rfc_disabled"] = True
        if runtime_disabled:
            options["runtime_disabled"] = True
        (self.root / ".rcoder" / "opencode.json").write_text(
            json.dumps(options), encoding="utf-8")

    def _run_host(self, *, rfc_disabled: bool = False, runtime_disabled: bool = False,
                  prompt: str = "Reply with E2E_OK only.", session: Optional[str] = None,
                  runtime_path: Optional[str] = None) -> tuple[subprocess.CompletedProcess, list[dict], str]:
        self._set_workspace_options(runtime_path=runtime_path or str(self.binary),
                                    rfc_disabled=rfc_disabled, runtime_disabled=runtime_disabled)
        before = len(self.provider.requests)
        log = self.root / f"host-log-{uuid.uuid4().hex[:6]}.txt"
        command = [*self.host, "run", "--standalone", "--session", session or self.session,
                   "--model", "mock/e2e-model", "--log-level", "debug", "--print-logs", prompt]
        with log.open("wb") as handle:
            result = subprocess.run(command, cwd=str(self.root), env=self.env,
                                    stdout=subprocess.PIPE, stderr=handle, timeout=150)
        with self.provider.lock:
            captured = list(self.provider.requests[before:])
        return result, captured, log.read_text(encoding="utf-8", errors="replace")

    @staticmethod
    def _system_text(requests: list[dict]) -> str:
        parts = []
        for request in requests:
            for message in request.get("messages", []):
                if message.get("role") == "system":
                    content = message.get("content")
                    parts.append(content if isinstance(content, str) else json.dumps(content))
        return "\n".join(parts)

    def test_native_host_delivers_both_markers_in_one_request(self) -> None:
        result, requests, log = self._run_host()
        self.assertEqual(result.returncode, 0, result.stdout.decode("utf-8", "replace")[-500:])
        self.assertGreaterEqual(len(requests), 1)
        self.assertIn("E2E_OK", result.stdout.decode("utf-8", "replace"))
        system = self._system_text(requests)
        self.assertIn(self.rfc_marker, system)
        self.assertIn(self.runtime_marker, system)
        self.assertIn("RFC-ACK", system)
        self.assertTrue(any(self.rfc_marker in self._system_text([request])
                            and self.runtime_marker in self._system_text([request])
                            for request in requests), "markers must share one model request")
        self.assertIn("mcp connected", log)
        self.assertIn("server=rcoder", log)
        self.assertIn(f"loading plugin", log)
        self.assertIn(str(self.root / ".opencode" / "plugins" / "rcoder.js"), log)
        self.assertNotIn(str(ROOT / ".opencode" / "plugins" / "rcoder.js"), log)
        self.assertNotIn((ROOT / ".opencode" / "plugins" / "rcoder.js").as_posix(), log)

        sessions = list((self.root / ".rcoder" / "runtime" / "sessions").glob("*.json"))
        self.assertEqual(len(sessions), 1, "exactly one lifecycle companion")
        state = None
        for _ in range(20):
            state = json.loads(sessions[0].read_text(encoding="utf-8"))
            if state["state"] == "stopped":
                break
            threading.Event().wait(0.5)
        self.assertEqual(state["state"], "stopped")
        self.assertEqual(state["project_root"], str(self.root))

    def test_subsystem_independence(self) -> None:
        cases = [
            (False, False, self.rfc_marker, self.runtime_marker),
            (True, False, None, self.runtime_marker),
            (False, True, self.rfc_marker, None),
            (True, True, None, None),
        ]
        for index, (rfc_disabled, runtime_disabled, want_rfc, want_runtime) in enumerate(cases):
            with self.subTest(rfc_disabled=rfc_disabled, runtime_disabled=runtime_disabled):
                session = f"ses-e2e-{self.test_id}-{index}"
                fabric = ContextFabric(self.root)
                fabric.ensure_session(session)
                fabric.store_context(session, "objective", "E2E RFC marker", self.rfc_marker,
                                     source_ref="e2e-fixture", now=1000)
                result, requests, _log = self._run_host(
                    rfc_disabled=rfc_disabled, runtime_disabled=runtime_disabled,
                    session=session, prompt="Reply with E2E_OK only.")
                self.assertEqual(result.returncode, 0)
                system = self._system_text(requests)
                self.assertEqual(self.rfc_marker in system, want_rfc is not None)
                self.assertEqual(self.runtime_marker in system, want_runtime is not None)

    def test_missing_context_and_retry_do_not_fabricate_delivery(self) -> None:
        first, requests, _ = self._run_host(prompt="Reply with E2E_OK only.")
        self.assertEqual(first.returncode, 0)
        self.assertIn(self.rfc_marker, self._system_text(requests))
        retry, retried, _ = self._run_host(prompt="Retry the same request.")
        self.assertEqual(retry.returncode, 0)
        system = self._system_text(retried)
        self.assertIn(self.rfc_marker, system)
        all_text = self._system_text(requests) + "\n" + system
        canaries = [line for line in all_text.splitlines() if "RFC-ACK:" in line]
        self.assertEqual(len(canaries), 2, "each request must use a fresh prompt identity")
        self.assertNotEqual(canaries[0], canaries[1])

        fresh = f"ses-e2e-{self.test_id}-missing"
        result, requests, _ = self._run_host(session=fresh, prompt="Reply with E2E_OK only.")
        self.assertEqual(result.returncode, 0)
        self.assertNotIn(self.rfc_marker, self._system_text(requests),
                         "missing context must not be reported as delivered")

    def _set_mcp_runtime_path(self, path: str) -> None:
        config = json.loads((self.root / "opencode.jsonc").read_text(encoding="utf-8"))
        config["mcp"]["rcoder"]["environment"]["RCODER_RUNTIME_PATH"] = path
        text = json.dumps(config, indent=2)
        (self.root / "opencode.jsonc").write_text(text, encoding="utf-8")
        (self.root / ".opencode" / "opencode.jsonc").write_text(text, encoding="utf-8")

    def test_runtime_startup_failure_fails_open(self) -> None:
        missing = "/nonexistent/rcoder-runtime-binary"
        self._set_mcp_runtime_path(missing)
        result, requests, _ = self._run_host(
            runtime_path=missing, prompt="Reply with E2E_OK only.")
        self.assertEqual(result.returncode, 0)
        system = self._system_text(requests)
        self.assertIn(self.rfc_marker, system)
        self.assertNotIn(self.runtime_marker, system)
        self.assertFalse(list((self.root / ".rcoder" / "runtime" / "sessions").glob("*.json")))

    def test_direct_mcp_json_rpc_lifecycle_and_tool_call(self) -> None:
        environment = dict(self.env)
        environment["RCODER_RUNTIME_PATH"] = self.binary
        process = subprocess.Popen(
            [*self.node, str(ROOT / "launcher" / "rcoder-mcp.mjs"), "--root", str(self.root),
             "--profile", "minimal"],
            cwd=str(self.root), env=environment, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        assert process.stdin is not None
        try:
            def request(payload: dict) -> dict:
                process.stdin.write(json.dumps(payload) + "\n")
                process.stdin.flush()
                while True:
                    line = process.stdout.readline()
                    if not line:
                        raise AssertionError("MCP stdout closed unexpectedly")
                    message = json.loads(line)
                    if message.get("id") == payload.get("id"):
                        return message

            init = request({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
                "protocolVersion": "2024-11-05", "capabilities": {},
                "clientInfo": {"name": "e2e-test", "version": "1"}}})
            self.assertIsInstance(init.get("result", {}).get("protocolVersion"), str)
            process.stdin.write(json.dumps({"jsonrpc": "2.0", "method":
                                            "notifications/initialized", "params": {}}) + "\n")
            process.stdin.flush()
            tools = request({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
            names = {item["name"] for item in tools["result"]["tools"]}
            self.assertIn("rcoder_scan", names)
            called = request({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
                "name": "rcoder_list_specialists", "arguments": {}}})
            self.assertFalse(called.get("error"))
            content = called["result"]["content"][0]["text"]
            payload = json.loads(content) if isinstance(content, str) else content
            self.assertGreater(payload["count"], 0)
            self.assertTrue(payload["modules"])
        finally:
            process.stdin.close()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.terminate()
                process.wait(timeout=10)
            stderr = process.stderr.read() if process.stderr else ""
            if process.stderr:
                process.stderr.close()
            if process.stdout:
                process.stdout.close()
        self.assertLess(len(stderr), 8192, "MCP stderr must stay bounded")
        sessions = list((self.root / ".rcoder" / "runtime" / "sessions").glob("*.json"))
        self.assertEqual(len(sessions), 1)
        for _ in range(20):
            state = json.loads(sessions[0].read_text(encoding="utf-8"))["state"]
            if state == "stopped":
                break
            threading.Event().wait(0.5)
        self.assertEqual(state, "stopped")


if __name__ == "__main__":
    unittest.main(verbosity=2)
