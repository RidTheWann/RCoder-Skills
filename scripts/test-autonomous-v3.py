#!/usr/bin/env python3
"""Integration tests for Phase 3 autonomous execution, memory, swarm, and parity."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "rcoder" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT / "scripts"))

import rcoder_hooks  # noqa: E402
import rcoder_mcp  # noqa: E402
import rsaver_guard  # noqa: E402
import rsaver_sandbox  # noqa: E402
from rcoder_memory import EpisodicLessonStore, _sanitize  # noqa: E402
from rcoder_swarm import SwarmCoordinator  # noqa: E402
from rscan_index import IncrementalRepoIndex  # noqa: E402
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
            upper = workspace / "Auth.py"
            lower = workspace / "auth.py"
            upper.write_text("a=1\n", encoding="utf-8")
            lower.write_text("a=2\n", encoding="utf-8")
            case_sensitive_filesystem = upper.read_text(encoding="utf-8") == "a=1\n" and \
                lower.read_text(encoding="utf-8") == "a=2\n"
            (workspace / "mcp.json").write_text(
                r'{"command": "C:\\Python\\python.exe"}', encoding="utf-8"
            )
            issues = audit_cross_platform_parity(workspace)
            self.assertTrue(any("[CRLF_LEAK]" in issue for issue in issues))
            self.assertTrue(any("[WIN_RESERVED_NAME]" in issue for issue in issues))
            if case_sensitive_filesystem:
                self.assertTrue(any("[CASE_COLLISION]" in issue for issue in issues))
            self.assertTrue(any("[HARDCODED_OS_PATH]" in issue for issue in issues))

    def test_mcp_registry_exposes_autonomous_tools(self) -> None:
        import rcoder_mcp
        for name in ("rcoder_apply_verify", "rcoder_recall", "rcoder_learn", "rcoder_handoff"):
            self.assertIn(name, rcoder_mcp.TOOL_INDEX)


class TestCodexReviewFixes(unittest.TestCase):
    def test_hook_guard_handles_wrapper_options_and_broad_add(self) -> None:
        checks = [
            ("sudo -u root rm -rf /", "recursive delete"),
            ("sudo -u root cat .env", "credential file"),
            ("git add -A", "broad pathspec"),
            ("git add .", "broad pathspec"),
        ]
        for command, expected in checks:
            decision = rcoder_hooks.decide_tool(
                {"tool_name": "Bash", "tool_input": {"command": command}}
            )
            self.assertEqual("deny", decision[0], command)
            self.assertIn(expected, decision[1], command)
        self.assertIsNone(
            rcoder_hooks.decide_tool(
                {"tool_name": "Bash", "tool_input": {"command": "git add -A src"}}
            )
        )

    def test_doctor_repair_uses_valid_join_and_package_root(self) -> None:
        source = (ROOT / "scripts" / "rcoder.mjs").read_text(encoding="utf-8")
        self.assertNotIn("' '.join(", source)
        self.assertIn("path.join(PACKAGE_ROOT, 'launcher', 'rcoder-mcp.mjs')", source)

    def test_impact_command_matches_detected_stack(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            (workspace / "go.mod").write_text("module example\n", encoding="utf-8")
            self.assertEqual("go test ./...", rcoder_mcp._detected_test_command(workspace, []))
            (workspace / "go.mod").unlink()
            (workspace / "package.json").write_text(
                '{"scripts":{"test":"vitest"}}', encoding="utf-8"
            )
            self.assertEqual("npm test", rcoder_mcp._detected_test_command(workspace, []))

    def test_memory_sanitizer_redacts_cloud_keys_and_assignments(self) -> None:
        access_key = "AKIA" + "1234567890ABCDEF"
        self.assertEqual(
            'api_key = "[REDACTED_SECRET]"',
            _sanitize(f'api_key = "{access_key}"'),
        )
        self.assertEqual(
            'password: "[REDACTED_SECRET]"',
            _sanitize('password: "supersecret123"'),
        )

    def test_swarm_lease_lock_is_cleaned_and_checksum_is_not_authentication(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            swarm = SwarmCoordinator(workspace)
            self.assertTrue(swarm.claim_files("rcoder-a", ["shared.py"])["granted"])
            self.assertFalse(swarm.claim_files("rcoder-b", ["shared.py"])["granted"])
            self.assertFalse(swarm.leases_path.with_suffix(".lock").exists())
            capsule = swarm.pack_handoff("rcoder-a", "rcoder-b", "goal", ["shared.py"], ["PASS"])
            self.assertTrue(SwarmCoordinator.verify_handoff(capsule))
            self.assertIn("checksum", rcoder_swarm_source())

    def test_brace_skeleton_preserves_declarations_and_module_lines(self) -> None:
        source = (
            "import os\nCONFIG = 1\nexport function sum(a) {\n  return a;\n}\nconst tail = 2;\n"
        )
        skeleton = rsaver_guard.compress_skeleton(source, "sum.js", ".js")
        self.assertIn("L1: import os", skeleton)
        self.assertIn("L2: CONFIG = 1", skeleton)
        self.assertIn("L3-L5: export function sum(a) { ... }", skeleton)
        self.assertIn("L6: const tail = 2;", skeleton)

    def test_git_drift_preserves_leading_dot_in_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            subprocess.run(["git", "init", "-q"], cwd=workspace, check=True)
            target = workspace / ".github" / "workflows" / "build.yml"
            target.parent.mkdir(parents=True)
            target.write_text("name: build\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=workspace, check=True)
            subprocess.run(
                ["git", "-c", "user.email=test@example.invalid", "-c", "user.name=Test",
                 "commit", "-qm", "initial"],
                cwd=workspace, check=True,
            )
            target.write_text("name: changed\n", encoding="utf-8")
            drift = rsaver_guard.crosscheck_git_drift(
                workspace, [".github/workflows/build.yml"], []
            )
            self.assertIn(".github/workflows/build.yml", drift["modified_files"])
            self.assertEqual([], drift["untouched_targets"])

    def test_sandbox_rejects_outside_absolute_and_rolls_back_on_interrupt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            target = workspace / "calc.py"
            original = "def add(a, b):\n    return a + b\n"
            target.write_text(original, encoding="utf-8")
            outside_path = str(workspace.parent / "rcoder-outside-evil.txt")
            rejected = transactional_apply_and_verify(
                workspace, [{"path": outside_path, "old_text": "", "new_text": "x"}]
            )
            self.assertFalse(rejected["ok"])
            with mock.patch.object(rsaver_sandbox.subprocess, "run", side_effect=KeyboardInterrupt):
                with self.assertRaises(KeyboardInterrupt):
                    transactional_apply_and_verify(
                        workspace,
                        [{"path": "calc.py", "old_text": "return a + b", "new_text": "return 0"}],
                        verify_cmd=["python3", "-m", "pytest"],
                    )
            self.assertEqual(original, target.read_text(encoding="utf-8"))

    def test_index_extracts_polyglot_symbols(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            (workspace / "main.go").write_text(
                "package main\nfunc Serve() {}\n", encoding="utf-8"
            )
            (workspace / "lib.js").write_text(
                "export function fetchData() {}\n", encoding="utf-8"
            )
            index = IncrementalRepoIndex(workspace)
            index.sync_files(["main.go", "lib.js"])
            self.assertEqual("main.go", index.find_symbol("Serve")[0]["path"])
            self.assertEqual("lib.js", index.find_symbol("fetchData")[0]["path"])


def rcoder_swarm_source() -> str:
    return (SCRIPTS / "rcoder_swarm.py").read_text(encoding="utf-8")


if __name__ == "__main__":
    unittest.main(verbosity=2)
