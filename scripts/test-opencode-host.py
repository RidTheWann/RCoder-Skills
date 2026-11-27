#!/usr/bin/env python3
"""Regression tests for the OpenCode V2 RFC/Runtime bridge."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from typing import Optional
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = ROOT / "skills" / "rcoder" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import opencode_host  # noqa: E402
from context_fabric import ContextFabric  # noqa: E402


class OpenCodeHostTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="rcoder-opencode-host-")
        self.root = Path(self.temp.name).resolve()
        self.fabric = ContextFabric(self.root)
        self.session_id = "opencode-session-001"
        self.fabric.store_context(
            self.session_id,
            "objective",
            "OpenCode delivery objective",
            "Hydrate this exact model request and verify its canary.",
            source_ref="test-fixture",
            now=100,
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def event(self, request_id: str = "oc-request-001", **extra: object) -> dict:
        return {
            "cwd": str(self.root),
            "session_id": self.session_id,
            "request_id": request_id,
            **extra,
        }

    def token_path(self, request_id: str = "oc-request-001") -> Path:
        token, _metadata = opencode_host._delivery_paths(
            self.root, self.session_id, request_id, create=False
        )
        assert token is not None
        return token

    def metadata_path(self, request_id: str = "oc-request-001") -> Path:
        _token, metadata = opencode_host._delivery_paths(
            self.root, self.session_id, request_id, create=False
        )
        assert metadata is not None
        return metadata

    def token(self, request_id: str = "oc-request-001") -> str:
        return self.token_path(request_id).read_text(encoding="utf-8").strip()

    def test_context_creates_one_unique_delivery_with_a_digest_only_in_sqlite(self) -> None:
        result = opencode_host.handle_context(self.event())
        self.assertNotIn("runtime", result)
        rfc = result["rfc"]
        self.assertEqual(rfc["prompt_id"], "oc-request-001")
        self.assertIn("OpenCode delivery objective", rfc["text"])
        token = self.token()
        self.assertIn(token, rfc["text"])
        self.assertNotIn(token, self.metadata_path().read_text(encoding="utf-8"))

        conn = sqlite3.connect(self.fabric.db_path)
        try:
            digest = conn.execute(
                "SELECT ack_token_sha256 FROM prompt_deliveries WHERE session_id=? AND prompt_id=?",
                (self.session_id, "oc-request-001"),
            ).fetchone()[0]
        finally:
            conn.close()
        self.assertEqual(digest, hashlib.sha256(token.encode("utf-8")).hexdigest())
        self.assertNotEqual(digest, token)

    def test_each_model_request_gets_a_distinct_delivery(self) -> None:
        first = opencode_host.handle_context(self.event("oc-request-001"))
        second = opencode_host.handle_context(self.event("oc-request-002"))
        self.assertNotEqual(first["rfc"]["payload_sha256"], second["rfc"]["payload_sha256"])
        self.assertNotEqual(self.token("oc-request-001"), self.token("oc-request-002"))
        self.assertNotEqual(
            first["rfc"]["text"].split("RFC-ACK: ", 1)[1].split(" ", 1)[0],
            second["rfc"]["text"].split("RFC-ACK: ", 1)[1].split(" ", 1)[0],
        )

    def test_duplicate_request_identity_does_not_rotate_the_canary(self) -> None:
        opencode_host.handle_context(self.event())
        token = self.token()
        self.assertEqual(opencode_host.handle_context(self.event()), {})
        self.assertEqual(self.token(), token)
        conn = sqlite3.connect(self.fabric.db_path)
        try:
            count = conn.execute(
                "SELECT COUNT(*) FROM prompt_deliveries WHERE session_id=?", (self.session_id,)
            ).fetchone()[0]
        finally:
            conn.close()
        self.assertEqual(count, 1)

    def test_response_is_attributed_to_the_matching_delivery_only(self) -> None:
        opencode_host.handle_context(self.event("oc-request-001"))
        opencode_host.handle_context(self.event("oc-request-002"))
        first_token = self.token("oc-request-001")

        result = opencode_host.handle_response(
            {**self.event("oc-request-001"), "response": f"Done.\n<!-- RFC-ACK: {first_token} -->"}
        )
        self.assertTrue(result["recorded"])
        self.assertTrue(result["acknowledged"])
        self.assertEqual(result["prompt_id"], "oc-request-001")

        first = self.fabric.export_transcript(self.session_id, "oc-request-001")
        second = self.fabric.export_transcript(self.session_id, "oc-request-002")
        self.assertTrue(first["acknowledged"])
        self.assertFalse(second["acknowledged"])
        self.assertEqual(len(first["messages"]), 1)
        self.assertEqual(len(second["messages"]), 0)
        serialized = json.dumps(first, ensure_ascii=False)
        self.assertNotIn(first_token, serialized)
        self.assertIn("Done.", serialized)
        self.assertTrue(self.token_path("oc-request-001").exists())

    def test_explicit_request_identity_records_an_omitted_canary_without_guessing(self) -> None:
        opencode_host.handle_context(self.event("oc-request-001"))
        opencode_host.handle_context(self.event("oc-request-002"))
        result = opencode_host.handle_response(
            {
                **self.event("oc-request-001"),
                "response": "Completed without echoing the delivery marker.",
            }
        )
        self.assertTrue(result["recorded"])
        self.assertFalse(result["acknowledged"])
        self.assertEqual(result["prompt_id"], "oc-request-001")
        first = self.fabric.export_transcript(self.session_id, "oc-request-001")
        second = self.fabric.export_transcript(self.session_id, "oc-request-002")
        self.assertEqual(len(first["messages"]), 1)
        self.assertEqual(second["messages"], [])
        self.assertTrue(self.token_path("oc-request-001").exists())
        self.assertTrue(self.token_path("oc-request-002").exists())

    def test_canary_from_another_delivery_is_not_attributed(self) -> None:
        opencode_host.handle_context(self.event("oc-request-001"))
        opencode_host.handle_context(self.event("oc-request-002"))
        second_token = self.token("oc-request-002")
        result = opencode_host.handle_response(
            {
                **self.event("oc-request-001"),
                "response": f"Wrong step.\n<!-- RFC-ACK: {second_token} -->",
            }
        )
        self.assertTrue(result.get("ambiguous"))
        for request_id in ("oc-request-001", "oc-request-002"):
            exported = self.fabric.export_transcript(self.session_id, request_id)
            self.assertEqual(exported["messages"], [])

    def test_response_without_a_canary_is_recorded_as_unacknowledged(self) -> None:
        opencode_host.handle_context(self.event())
        result = opencode_host.handle_response(
            {**self.event(), "response": "A response that omitted the delivery marker."}
        )
        self.assertTrue(result["recorded"])
        self.assertFalse(result["acknowledged"])
        exported = self.fabric.export_transcript(self.session_id, "oc-request-001")
        self.assertFalse(exported["acknowledged"])
        self.assertIn("omitted the delivery marker", json.dumps(exported))
        self.assertTrue(self.token_path().exists())

    def test_response_containing_two_canaries_is_not_attributed(self) -> None:
        opencode_host.handle_context(self.event("oc-request-001"))
        opencode_host.handle_context(self.event("oc-request-002"))
        response = f"{self.token('oc-request-001')}\n{self.token('oc-request-002')}"
        result = opencode_host.handle_response({**self.event(), "response": response})
        self.assertTrue(result.get("ambiguous"))
        for request_id in ("oc-request-001", "oc-request-002"):
            exported = self.fabric.export_transcript(self.session_id, request_id)
            self.assertFalse(exported["acknowledged"])
            self.assertEqual(exported["messages"], [])

    def test_repeated_events_for_one_delivery_do_not_remove_the_canary(self) -> None:
        opencode_host.handle_context(self.event())
        token = self.token()
        for message in ("First completion.", "Second completion."):
            result = opencode_host.handle_response(
                {**self.event(), "response": f"{message} <!-- RFC-ACK: {token} -->"}
            )
            self.assertTrue(result["acknowledged"])
        self.assertTrue(self.token_path().exists())
        exported = self.fabric.export_transcript(self.session_id, "oc-request-001")
        self.assertEqual(len(exported["messages"]), 2)
        self.assertNotIn(token, json.dumps(exported, ensure_ascii=False))

    def test_session_cleanup_removes_private_delivery_state(self) -> None:
        opencode_host.handle_context(self.event())
        self.assertTrue(self.token_path().exists())
        self.assertEqual(opencode_host.handle_cleanup(self.event()), {"cleaned": True})
        self.assertFalse(self.token_path().exists())
        self.assertFalse(self.metadata_path().exists())

    def test_age_cleanup_preserves_a_fresh_delivery_and_collects_an_interrupted_one(self) -> None:
        opencode_host.handle_context(self.event())
        now = time.time()
        self.assertEqual(
            opencode_host.cleanup_deliveries(self.root, now=now, max_age_seconds=3600),
            {"removed_deliveries": 0, "removed_orphan_tokens": 0},
        )
        self.assertTrue(self.token_path().exists())
        removed = opencode_host.cleanup_deliveries(self.root, now=now + 7200, max_age_seconds=3600)
        self.assertEqual(removed["removed_deliveries"], 1)
        self.assertFalse(self.token_path().exists())

    def test_disabled_rfc_context_and_response_are_inert(self) -> None:
        with patch.dict(os.environ, {"RCODER_RFC_DISABLE": "1"}):
            self.assertEqual(opencode_host.handle_context(self.event()), {})
            self.assertEqual(
                opencode_host.handle_response({**self.event(), "response": "ignored"}), {}
            )
        canary_directory = self.root / ".rcoder" / "private" / "rfc-canaries"
        self.assertFalse(canary_directory.exists())

    def test_missing_database_is_inert(self) -> None:
        with tempfile.TemporaryDirectory(prefix="rcoder-opencode-empty-") as empty:
            event = {"cwd": empty, "session_id": self.session_id, "request_id": "oc-request-001"}
            self.assertEqual(opencode_host.handle_context(event), {})
            self.assertFalse((Path(empty) / ".rcoder").exists())

    def test_runtime_packet_is_independent_of_rfc_failure(self) -> None:
        packet_text = "RCoder Runtime active task packet. SHA-256: " + "a" * 64
        with patch.object(
            opencode_host.runtime_task_host,
            "build_hook_response",
            return_value={
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": packet_text,
                }
            },
        ):
            with tempfile.TemporaryDirectory(prefix="rcoder-opencode-runtime-") as empty:
                result = opencode_host.handle_context(
                    {"cwd": empty, "session_id": self.session_id, "request_id": "oc-request-001"}
                )
        self.assertEqual(result, {"runtime": {"text": packet_text}})

    def _runtime_binary(self) -> Optional[str]:
        candidates = []
        explicit = os.environ.get("RCODER_RUNTIME_PATH")
        if explicit:
            candidates.append(explicit)
        on_path = shutil.which("rcoder-runtime")
        if on_path:
            candidates.append(on_path)
        candidates.append(str(ROOT / "runtime" / "target" / "debug" / "rcoder-runtime"))
        for candidate in candidates:
            path = Path(candidate)
            if path.is_file():
                return str(path.resolve())
        cargo = shutil.which("cargo")
        if not cargo:
            return None
        try:
            subprocess.run(
                [
                    cargo,
                    "build",
                    "--manifest-path",
                    str(ROOT / "runtime" / "Cargo.toml"),
                    "-p",
                    "rcoder-runtime",
                ],
                capture_output=True,
                text=True,
                timeout=180,
                check=True,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        built = ROOT / "runtime" / "target" / "debug" / "rcoder-runtime"
        return str(built) if built.is_file() else None

    def _cli_json(self, binary: str, *args: str) -> dict:
        environment = {
            "PATH": os.environ.get("PATH", ""),
            "HOME": str(self.root),
            "RCODER_RUNTIME_PATH": binary,
        }
        completed = subprocess.run(
            [binary, *args],
            capture_output=True,
            text=True,
            timeout=30,
            env=environment,
            check=True,
        )
        return json.loads(completed.stdout)

    def test_artifact_backed_verification_reaches_opencode_runtime_context(self) -> None:
        binary = self._runtime_binary()
        if binary is None:
            self.skipTest("rcoder-runtime binary is unavailable")
        reports = self.root / "reports"
        reports.mkdir(exist_ok=True)
        (reports / "unit.json").write_text(
            json.dumps(
                {
                    "schema": "rcoder-test-report/v1",
                    "criterion_id": "AC-001",
                    "summary": {
                        "passed": 2,
                        "failed": 0,
                        "skipped": 0,
                        "errors": 0,
                    },
                    "cases": [
                        {"name": "one", "outcome": "pass"},
                        {"name": "two", "outcome": "pass"},
                    ],
                }
            ),
            encoding="utf-8",
        )

        task = self._cli_json(
            binary,
            "task",
            "create",
            "--project",
            str(self.root),
            "--objective",
            "OpenCode verification summary",
            "--acceptance",
            "Artifact-backed tests pass",
            "--risk",
            "high",
            "--json",
        )
        task_id = task["id"]
        self._cli_json(
            binary,
            "task",
            "transition",
            "--project",
            str(self.root),
            "--id",
            task_id,
            "--to",
            "active",
            "--json",
        )
        evidenced = self._cli_json(
            binary,
            "task",
            "evidence",
            "--project",
            str(self.root),
            "--id",
            task_id,
            "--criterion",
            "AC-001",
            "--outcome",
            "pass",
            "--summary",
            "caller claim",
            "--source",
            "reports/unit.json",
            "--json",
        )
        evidence_id = evidenced["evidence"][-1]["id"]
        verified = self._cli_json(
            binary,
            "task",
            "verify",
            "--project",
            str(self.root),
            "--id",
            task_id,
            "--evidence",
            evidence_id,
            "--artifact",
            "reports/unit.json",
            "--parser",
            "rcoder_test_report_v1",
            "--criterion",
            "AC-001",
            "--provenance",
            "cli:opencode-test",
            "--enforce",
            "--json",
        )
        self.assertEqual(verified["verification_state"], "artifact_verified")
        self.assertEqual(verified["declared_outcome"], "pass")

        with patch.dict(os.environ, {"RCODER_RUNTIME_PATH": binary}):
            payload = opencode_host.handle_context(self.event())
        self.assertIn("runtime", payload)
        self.assertIn("rfc", payload)
        text = payload["runtime"]["text"]
        self.assertIn("RCoder Runtime active task packet", text)
        self.assertIn("artifact_verified", text)
        self.assertIn("rcoder_test_report_v1", text)
        self.assertIn("cli:opencode-test", text)
        packet = json.loads(text[text.index("{"):])
        summary = packet["task"]["verifications"][0]
        self.assertEqual(summary["state"], "artifact_verified")
        self.assertEqual(summary["declared_outcome"], "pass")
        self.assertNotIn("artifact", summary)
        self.assertNotIn("detail", summary)
        self.assertNotIn("raw", summary)

    def test_runtime_failure_does_not_block_rfc_context(self) -> None:
        with patch.object(
            opencode_host.runtime_task_host,
            "build_hook_response",
            side_effect=RuntimeError("runtime unavailable"),
        ):
            result = opencode_host.handle_context(self.event())
        self.assertIn("rfc", result)
        self.assertNotIn("runtime", result)

    def test_symlinked_private_state_is_rejected(self) -> None:
        (self.root / ".rcoder" / "private").symlink_to(self.root / ".rcoder", target_is_directory=True)
        self.assertEqual(opencode_host.handle_context(self.event()), {})
        self.assertFalse((self.root / ".rcoder" / "private" / "rfc-canaries").exists())

    def test_response_rejects_oversized_text(self) -> None:
        opencode_host.handle_context(self.event())
        oversized = "x" * (opencode_host.MAX_RESPONSE_BYTES + 1)
        self.assertEqual(
            opencode_host.handle_response({**self.event(), "response": oversized}), {}
        )

    def test_cli_emits_json_and_fails_open_on_malformed_input(self) -> None:
        completed = __import__("subprocess").run(
            [sys.executable, str(SCRIPT_DIR / "opencode_host.py"), "context"],
            input="not-json",
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(json.loads(completed.stdout), {})


if __name__ == "__main__":
    unittest.main()
