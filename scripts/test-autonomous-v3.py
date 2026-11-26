#!/usr/bin/env python3
"""Integration tests for Phase 3 autonomous execution, memory, swarm, and parity."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "rcoder" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT / "scripts"))

from rcoder_memory import EpisodicLessonStore  # noqa: E402
from rcoder_swarm import SwarmCoordinator  # noqa: E402
from rsaver_sandbox import transactional_apply_and_verify  # noqa: E402
from verify_parity import audit_cross_platform_parity  # noqa: E402


class TestAutonomousPhase3(unittest.TestCase):
    def test_transactional_sandbox_rolls_back_on_broken_syntax(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            target = workspace / "calc.py"
            original = "def add(a, b):\n    return a + b\n"
            target.write_text(original, encoding="utf-8")
            result = transactional_apply_and_verify(
                workspace,
                [{"path": "calc.py", "old_text": "return a + b", "new_text": "return a + (broken"}],
            )
            self.assertFalse(result["ok"])
            self.assertTrue(result["rolled_back"])
            self.assertEqual("syntax_check", result["stage"])
            self.assertEqual(target.read_text(encoding="utf-8"), original)

    def test_transactional_sandbox_commits_when_verification_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            target = workspace / "calc.py"
            target.write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
            result = transactional_apply_and_verify(
                workspace,
                [{"path": "calc.py", "old_text": "return a + b", "new_text": "return a - b"}],
                verify_cmd=[sys.executable, "-c", "import calc; assert calc.add(3, 1) == 2"],
            )
            self.assertTrue(result["ok"])
            self.assertFalse(result["rolled_back"])
            self.assertIn("return a - b", target.read_text(encoding="utf-8"))

    def test_episodic_lesson_redacts_secrets_and_recalls(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            store = EpisodicLessonStore(workspace)
            record = store.record_lesson(
                symptom="WinError 32 SQLite file locked during Windows test cleanup",
                root_cause="Unclosed sqlite3.connect() using token sk-proj-secret1234567890abcd",
                verified_fix="Wrap sqlite3.connect() in contextlib.closing()",
                related_files=[r"skills\rcoder\scripts\rscan_index.py"],
                tags=["windows", "sqlite"],
            )
            self.assertTrue(record["recorded"])
            self.assertNotIn("sk-proj-", record["lesson"]["root_cause"])
            self.assertEqual(
                ["skills/rcoder/scripts/rscan_index.py"], record["lesson"]["files"]
            )
            hits = store.recall("sqlite locked WinError 32 windows")
            self.assertEqual(1, len(hits))
            self.assertIn("contextlib.closing", hits[0]["verified_fix"])

    def test_swarm_file_lease_and_signed_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            swarm = SwarmCoordinator(workspace)
            first = swarm.claim_files("rcoder-debugger", ["skills/rcoder/scripts/rsaver.py"])
            self.assertTrue(first["granted"])
            second = swarm.claim_files("rcoder-reviewer", [r"skills\rcoder\scripts\rsaver.py"])
            self.assertFalse(second["granted"])
            self.assertIn("skills/rcoder/scripts/rsaver.py", first["claimed"])

            capsule = swarm.pack_handoff(
                from_agent="rcoder-debugger",
                to_agent="rcoder-verifier",
                objective="Fix CRLF digest drift",
                target_files=[r"skills\rcoder\scripts\rsaver.py"],
                verified_receipts=["python3 scripts/test-rsaver.py -> OK"],
            )
            self.assertTrue(SwarmCoordinator.verify_handoff(capsule))
            capsule["objective"] = "Tampered objective"
            self.assertFalse(SwarmCoordinator.verify_handoff(capsule))

    def test_parity_linter_detects_crlf_reserved_names_and_collisions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            (workspace / "helper.py").write_bytes(b"print('hi')\r\n")
            (workspace / "CON.txt").write_text("reserved", encoding="utf-8")
            (workspace / "Auth.py").write_text("a=1\n", encoding="utf-8")
            (workspace / "auth.py").write_text("a=2\n", encoding="utf-8")
            (workspace / "mcp.json").write_text(
                r'{"command": "C:\\Python\\python.exe"}', encoding="utf-8"
            )
            issues = audit_cross_platform_parity(workspace)
            self.assertTrue(any("[CRLF_LEAK]" in issue for issue in issues))
            self.assertTrue(any("[WIN_RESERVED_NAME]" in issue for issue in issues))
            self.assertTrue(any("[CASE_COLLISION]" in issue for issue in issues))
            self.assertTrue(any("[HARDCODED_OS_PATH]" in issue for issue in issues))

    def test_mcp_registry_exposes_autonomous_tools(self) -> None:
        import rcoder_mcp
        for name in ("rcoder_apply_verify", "rcoder_recall", "rcoder_learn", "rcoder_handoff"):
            self.assertIn(name, rcoder_mcp.TOOL_INDEX)


if __name__ == "__main__":
    unittest.main(verbosity=2)
