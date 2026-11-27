#!/usr/bin/env python3
"""Regression tests for Claude Code RFC host injection and response capture."""
from __future__ import annotations

import ast
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = ROOT / "skills" / "rcoder" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import context_fabric_host as host  # noqa: E402
from context_fabric import ContextFabric  # noqa: E402


class ContextFabricHostTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="rfc-host-")
        self.root = Path(self.temp.name)
        self.fabric = ContextFabric(self.root)
        self.session_id = "claude-session-001"
        self.prompt_id = "claude-prompt-001"
        self.fabric.store_context(
            self.session_id, "objective", "Active objective",
            "Preserve the RFC host handoff and verify the canary.",
            source_ref="test-fixture", now=100,
        )
        self.event = {
            "hook_event_name": "UserPromptSubmit",
            "session_id": self.session_id,
            "prompt_id": self.prompt_id,
            "cwd": str(self.root),
            "prompt": "Continue the active objective.",
        }

    def tearDown(self):
        self.temp.cleanup()

    def token_path(self, prompt_id=None):
        return host._canary_path(
            self.root, self.session_id, prompt_id or self.prompt_id, create=False
        )

    def test_user_prompt_submit_injects_a_fresh_context_for_exact_prompt(self):
        output = host.handle_user_prompt_submit(self.event)
        self.assertIsNotNone(output)
        specific = output["hookSpecificOutput"]
        self.assertEqual(specific["hookEventName"], "UserPromptSubmit")
        payload = specific["additionalContext"]
        self.assertIn("Active objective", payload)
        self.assertIn(self.session_id, payload)
        self.assertIn(self.prompt_id, payload)

        token_path = self.token_path()
        self.assertTrue(token_path.is_file())
        token = token_path.read_text(encoding="utf-8").strip()
        self.assertGreaterEqual(len(token), 24)
        self.assertIn(token, payload)

        conn = sqlite3.connect(self.fabric.db_path)
        try:
            stored_digest = conn.execute(
                "SELECT ack_token_sha256 FROM prompt_deliveries WHERE session_id=? AND prompt_id=?",
                (self.session_id, self.prompt_id),
            ).fetchone()[0]
        finally:
            conn.close()
        self.assertEqual(stored_digest, hashlib.sha256(token.encode("utf-8")).hexdigest())
        self.assertNotEqual(stored_digest, token)

    def test_stop_captures_response_and_exports_no_canary(self):
        host.handle_user_prompt_submit(self.event)
        token = self.token_path().read_text(encoding="utf-8").strip()
        response = f"Task result is ready.\n<!-- RFC-ACK: {token} -->"
        result = host.handle_stop({
            "hook_event_name": "Stop",
            "session_id": self.session_id,
            "prompt_id": self.prompt_id,
            "cwd": str(self.root),
            "last_assistant_message": response,
        })
        self.assertTrue(result["acknowledged"])
        self.assertTrue(self.token_path().exists())
        exported = self.fabric.export_transcript(self.session_id, self.prompt_id)
        serialized = json.dumps(exported, ensure_ascii=False)
        self.assertTrue(exported["acknowledged"])
        self.assertNotIn(token, serialized)
        self.assertIn("Task result is ready", serialized)
        self.assertIn("<!-- RFC-ACK:  -->", serialized)
        host.handle_session_end({"session_id": self.session_id, "cwd": str(self.root)})
        self.assertFalse(self.token_path().exists())

    def test_repeated_stop_events_capture_each_continuation_for_the_same_delivery(self):
        host.handle_user_prompt_submit(self.event)
        token = self.token_path().read_text(encoding="utf-8").strip()
        for message in ("First completion attempt.", "Final completion after the stop gate."):
            result = host.handle_stop({
                "hook_event_name": "Stop",
                "session_id": self.session_id,
                "prompt_id": self.prompt_id,
                "cwd": str(self.root),
                "last_assistant_message": f"{message} <!-- RFC-ACK: {token} -->",
                "stop_hook_active": message.startswith("Final"),
            })
            self.assertTrue(result["acknowledged"])
        exported = self.fabric.export_transcript(self.session_id, self.prompt_id)
        self.assertEqual(len(exported["messages"]), 2)
        self.assertIn("Final completion after the stop gate.", json.dumps(exported))
        self.assertTrue(self.token_path().exists())
        host.handle_session_end({"session_id": self.session_id, "cwd": str(self.root)})
        self.assertFalse(self.token_path().exists())

    def test_next_prompt_cleans_an_interrupted_prior_delivery(self):
        host.handle_user_prompt_submit(self.event)
        old_token_path = self.token_path()
        next_event = {**self.event, "prompt_id": "claude-prompt-002"}
        self.assertIsNotNone(host.handle_user_prompt_submit(next_event))
        self.assertFalse(old_token_path.exists())
        self.assertTrue(self.token_path("claude-prompt-002").exists())

    def test_successive_prompts_receive_distinct_single_use_canaries(self):
        first = host.handle_user_prompt_submit(self.event)
        first_token = self.token_path().read_text(encoding="utf-8").strip()
        second_event = {**self.event, "prompt_id": "claude-prompt-002"}
        second = host.handle_user_prompt_submit(second_event)
        second_path = self.token_path("claude-prompt-002")
        second_token = second_path.read_text(encoding="utf-8").strip()
        self.assertIn(first_token, first["hookSpecificOutput"]["additionalContext"])
        self.assertIn(second_token, second["hookSpecificOutput"]["additionalContext"])
        self.assertNotEqual(first_token, second_token)
        conn = sqlite3.connect(self.fabric.db_path)
        try:
            count = conn.execute(
                "SELECT COUNT(*) FROM prompt_deliveries WHERE session_id=?", (self.session_id,)
            ).fetchone()[0]
        finally:
            conn.close()
        self.assertEqual(count, 2)

    def test_first_prompt_without_host_prompt_id_uses_private_runtime_identity(self):
        event = {key: value for key, value in self.event.items() if key != "prompt_id"}
        output = host.handle_user_prompt_submit(event)
        self.assertIsNotNone(output)
        payload = output["hookSpecificOutput"]["additionalContext"]
        generated_id = next(
            line.split(": ", 1)[1]
            for line in payload.splitlines()
            if line.startswith("prompt_id: ")
        )
        self.assertRegex(generated_id, r"^rfc-[0-9]+-[a-f0-9]{16}$")
        token_path = self.token_path(generated_id)
        token = token_path.read_text(encoding="utf-8").strip()
        result = host.handle_stop({
            "hook_event_name": "Stop",
            "session_id": self.session_id,
            "prompt_id": "a-later-assigned-host-id",
            "cwd": str(self.root),
            "last_assistant_message": f"First response.\n<!-- RFC-ACK: {token} -->",
        })
        self.assertTrue(result["acknowledged"])
        exported = self.fabric.export_transcript(self.session_id, generated_id)
        self.assertTrue(exported["acknowledged"])
        self.assertTrue(token_path.exists())
        host.handle_session_end({"session_id": self.session_id, "cwd": str(self.root)})
        self.assertFalse(token_path.exists())

    def test_response_without_canary_is_recorded_as_unacknowledged(self):
        host.handle_user_prompt_submit(self.event)
        result = host.handle_stop({
            "hook_event_name": "Stop",
            "session_id": self.session_id,
            "prompt_id": self.prompt_id,
            "cwd": str(self.root),
            "last_assistant_message": "A response that omitted the delivery marker.",
        })
        self.assertFalse(result["acknowledged"])
        exported = self.fabric.export_transcript(self.session_id, self.prompt_id)
        self.assertFalse(exported["acknowledged"])
        self.assertIn("omitted the delivery marker", json.dumps(exported))
        self.assertTrue(self.token_path().exists())

    def test_wrong_prompt_stop_cannot_capture_another_delivery(self):
        host.handle_user_prompt_submit(self.event)
        token_file = self.token_path()
        untouched = host.handle_stop({
            "hook_event_name": "Stop",
            "session_id": self.session_id,
            "prompt_id": "claude-prompt-other",
            "cwd": str(self.root),
            "last_assistant_message": "not the matching prompt",
        })
        self.assertIsNone(untouched)
        self.assertTrue(token_file.is_file())
        token = token_file.read_text(encoding="utf-8").strip()
        result = host.handle_stop({
            "hook_event_name": "Stop",
            "session_id": self.session_id,
            "prompt_id": self.prompt_id,
            "cwd": str(self.root),
            "last_assistant_message": token,
        })
        self.assertTrue(result["acknowledged"])

    def test_missing_last_assistant_message_does_not_destroy_pending_canary(self):
        host.handle_user_prompt_submit(self.event)
        token_file = self.token_path()
        self.assertIsNone(host.handle_stop({
            "session_id": self.session_id, "prompt_id": self.prompt_id, "cwd": str(self.root)
        }))
        self.assertTrue(token_file.is_file())

    def test_duplicate_prompt_identity_is_rejected_without_overwriting_canary(self):
        host.handle_user_prompt_submit(self.event)
        token_file = self.token_path()
        original = token_file.read_text(encoding="utf-8")
        self.assertIsNone(host.handle_user_prompt_submit(self.event))
        self.assertEqual(token_file.read_text(encoding="utf-8"), original)

    def test_opt_in_requires_an_existing_context_fabric_database(self):
        with tempfile.TemporaryDirectory(prefix="rfc-host-optin-") as temp:
            root = Path(temp)
            event = {**self.event, "cwd": str(root)}
            self.assertIsNone(host.handle_user_prompt_submit(event))
            self.assertFalse((root / ".rcoder").exists())

    def test_missing_or_malformed_identity_fails_open(self):
        for event in (
            {},
            {**self.event, "session_id": "../outside"},
            {**self.event, "prompt_id": "contains spaces"},
            {**self.event, "cwd": ""},
        ):
            self.assertIsNone(host.handle_user_prompt_submit(event))

    def test_disabled_environment_switches_off_injection_and_capture(self):
        with patch.dict(os.environ, {"RCODER_RFC_DISABLE": "1"}):
            self.assertIsNone(host.handle_user_prompt_submit(self.event))
            self.assertIsNone(host.handle_stop(self.event))

    def test_session_end_cli_cleans_private_pending_delivery_state(self):
        host.handle_user_prompt_submit(self.event)
        completed = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "context_fabric_host.py"), "session-end"],
            input=json.dumps({"session_id": self.session_id, "cwd": str(self.root)}),
            capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(completed.returncode, 0)
        self.assertFalse(self.token_path().exists())

    def test_host_cli_uses_documented_hook_json_contract_and_fails_open(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "context_fabric_host.py"), "user-prompt-submit"],
            input=json.dumps(self.event), capture_output=True, text=True, timeout=20,
            cwd=self.root,
        )
        self.assertEqual(completed.returncode, 0)
        result = json.loads(completed.stdout)
        self.assertEqual(result["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit")
        malformed = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "context_fabric_host.py"), "user-prompt-submit"],
            input="not json", capture_output=True, text=True, timeout=20,
            cwd=self.root,
        )
        self.assertEqual(malformed.returncode, 0)
        self.assertEqual(malformed.stdout, "")

    def test_adapter_is_standard_library_and_has_no_process_or_network_side_effects(self):
        tree = ast.parse((SCRIPT_DIR / "context_fabric_host.py").read_text(encoding="utf-8"))
        imported = set()
        forbidden_calls = {"eval", "exec", "system", "popen", "Popen", "run", "call", "check_output", "__import__"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add((node.module or "").split(".")[0])
            elif isinstance(node, ast.Call):
                target = node.func
                name = target.id if isinstance(target, ast.Name) else getattr(target, "attr", "")
                self.assertNotIn(name, forbidden_calls)
                self.assertFalse(any(keyword.arg == "shell" for keyword in node.keywords))
        self.assertFalse(imported & {
            "subprocess", "socket", "ssl", "urllib", "http", "requests", "asyncio", "ctypes", "pickle"
        })


if __name__ == "__main__":
    unittest.main(verbosity=2)
