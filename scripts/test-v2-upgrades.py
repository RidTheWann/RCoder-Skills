#!/usr/bin/env python3
"""Regression tests for the RCoder v2 upgrade tracks."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS = ROOT / "skills" / "rcoder" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

import rcoder_hooks  # noqa: E402
import rcoder_mcp  # noqa: E402
import route_predict  # noqa: E402
import rsaver_guard  # noqa: E402
import rscan_graph  # noqa: E402


def git(root: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.email=test@example.invalid", "-c", "user.name=Test", *args],
        cwd=str(root), check=True, capture_output=True,
    )


class RScanGraphUpgradeTests(unittest.TestCase):
    def test_cycles_hotspots_and_budget_modes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package = root / "pkg"
            package.mkdir()
            (package / "__init__.py").write_text("", encoding="utf-8")
            (package / "a.py").write_text(
                "import pkg.b\n\ndef transform(value):\n    if value:\n        return value\n    return 0\n",
                encoding="utf-8",
            )
            (package / "b.py").write_text("import pkg.a\n", encoding="utf-8")

            compact = rscan_graph.analyze_repository_graph(root, token_budget=500)
            deep = rscan_graph.analyze_repository_graph(root, token_budget=12000)

            self.assertEqual("compact", compact["budget_mode"])
            self.assertEqual("deep", deep["budget_mode"])
            self.assertEqual(2, deep["summary"]["dependency_edges"])
            self.assertEqual(1, deep["summary"]["circular_dependency_groups"])
            self.assertEqual(["pkg/a.py", "pkg/b.py"], deep["cycles"][0])
            self.assertLessEqual(len(compact["hotspots"]), len(deep["hotspots"]))
            self.assertTrue(any(item["file"] == "pkg/a.py" for item in deep["hotspots"]))
            self.assertTrue(
                any(item["code"] == "CIRCULAR_DEPENDENCY" for item in deep["risks"])
            )

    def test_documentation_mentions_secrets_without_risk_false_positive(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            docs = root / "docs"
            docs.mkdir()
            (docs / "setup.md").write_text(
                "Copy .env.example and set API_KEY in your local shell.", encoding="utf-8"
            )
            result = rscan_graph.analyze_repository_graph(root, token_budget=400)
            self.assertFalse(
                any(item["code"] == "SENSITIVE_CONFIG_PATH" for item in result["risks"])
            )


class RSaverGuardUpgradeTests(unittest.TestCase):
    def test_reversible_redaction_is_single_and_idempotent(self) -> None:
        original = 'api_key = "unit-test-placeholder-value"\nport = 8080\n'
        redactor = rsaver_guard.ReversibleRedactor()
        redacted, count = redactor.redact(original)
        self.assertEqual(1, count)
        self.assertNotIn("unit-test-placeholder-value", redacted)
        self.assertIn("[REDACTED:BEARER_ASSIGNMENT:", redacted)
        self.assertEqual(original, redactor.restore(redacted))

        again, second_count = redactor.redact(redacted)
        self.assertEqual(redacted, again)
        self.assertEqual(1, second_count)

    def test_python_skeleton_keeps_anchor_signature_and_docstring(self) -> None:
        source = (
            'def add(a: int, b: int) -> int:\n'
            '    """Add two integers."""\n'
            "    return a + b\n"
        )
        skeleton = rsaver_guard.compress_python_skeleton(source, "sample.py")
        self.assertIn("# FILE: sample.py (total_lines=3)", skeleton)
        self.assertIn("L1-L3: def add(a: int, b: int) -> int:", skeleton)
        self.assertIn("Add two integers", skeleton)
        self.assertNotIn("return a + b", skeleton)

    def test_brace_skeleton_masks_strings_and_comments(self) -> None:
        source = (
            "export function sum(values) {\n"
            "  // hidden comment\n"
            '  const note = "}";\n'
            "  let total = 0;\n"
            "  for (const value of values) {\n"
            "    total += value;\n"
            "  }\n"
            "  return total;\n"
            "}\n"
        )
        skeleton = rsaver_guard.compress_skeleton(source, "sum.js", suffix=".js")
        self.assertIn("// FILE: sum.js (total_lines=9)", skeleton)
        self.assertIn("L1-L9: export function sum(values) { ... }", skeleton)
        self.assertNotIn("hidden comment", skeleton)
        self.assertNotIn("const note", skeleton)

    def test_git_drift_reports_untouched_targets_and_unverified_claims(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            git(root, "init", "-q")
            (root / "target.py").write_text("value = 1\n", encoding="utf-8")
            (root / "other.py").write_text("value = 2\n", encoding="utf-8")
            git(root, "add", ".")
            git(root, "commit", "-qm", "initial")
            (root / "target.py").write_text("value = 3\n", encoding="utf-8")

            aligned = rsaver_guard.crosscheck_git_drift(root, ["target.py"], ["target.py"])
            self.assertEqual("ALIGNED", aligned["status"])
            self.assertEqual([], aligned["untouched_targets"])
            self.assertEqual([], aligned["unverified_claims"])

            drift = rsaver_guard.crosscheck_git_drift(
                root, ["target.py", "other.py"], ["target.py", "other.py"]
            )
            self.assertEqual("DRIFT_DETECTED", drift["status"])
            self.assertEqual(["other.py"], drift["untouched_targets"])
            self.assertEqual(["other.py"], drift["unverified_claims"])


class RouteAddendumTests(unittest.TestCase):
    def test_polyglot_request_has_language_primary_and_bounded_addendums(self) -> None:
        valid = set(route_predict.reference_names())
        result = route_predict.propose(
            "Implement a Go authentication service with JWT signing and PostgreSQL migrations; "
            "verify secrets handling and query latency.",
            valid,
        )
        self.assertEqual("go-engineering", result["primary"])
        self.assertEqual("composite", result["route_mode"])
        self.assertLessEqual(len(result["addendums"]), route_predict.MAX_ADDENDUMS)
        self.assertTrue(result["addendums"])
        for addendum in result["addendums"]:
            self.assertEqual(route_predict.ADDENDUM_SECTION, addendum["load_section"])
            self.assertGreaterEqual(addendum["score"], route_predict.SECONDARY_THRESHOLD)
            self.assertIn(addendum["module"], result["proposed"])

    def test_bundler_handles_empty_and_single_rankings(self) -> None:
        empty = route_predict.bundle_multistage_route([])
        self.assertEqual("fallback", empty["mode"])
        self.assertEqual([], empty["addendums"])

        single = route_predict.bundle_multistage_route([("coding", 1.0)])
        self.assertEqual("single", single["mode"])
        self.assertEqual([], single["addendums"])


class MCPBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.old_root = rcoder_mcp.State.root
        self.old_protocol = rcoder_mcp.State.protocol
        self.old_enabled = rcoder_mcp.State.enabled
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        rcoder_mcp.State.root = self.root
        rcoder_mcp.State.protocol = rcoder_mcp.PROTOCOLS[0]
        rcoder_mcp.State.enabled = None

    def tearDown(self) -> None:
        rcoder_mcp.State.root = self.old_root
        rcoder_mcp.State.protocol = self.old_protocol
        rcoder_mcp.State.enabled = self.old_enabled
        self.temporary.cleanup()

    def test_workspace_path_rejects_prefix_escape_and_symlink(self) -> None:
        allowed = self.root / "allowed.txt"
        allowed.write_text("safe", encoding="utf-8")
        self.assertEqual(
            allowed, rcoder_mcp.resolve_workspace_path(self.root, "allowed.txt")
        )
        with self.assertRaises(rcoder_mcp.WorkspaceSecurityError):
            rcoder_mcp.resolve_workspace_path(self.root, "../outside.txt")

        sibling = self.root.parent / f"{self.root.name}-evil"
        sibling.mkdir(exist_ok=True)
        (sibling / "secret.txt").write_text("not-read", encoding="utf-8")
        with self.assertRaises(rcoder_mcp.WorkspaceSecurityError):
            rcoder_mcp.resolve_workspace_path(
                self.root, f"../{sibling.name}/secret.txt"
            )

        outside = self.root.parent / "outside-target.txt"
        outside.write_text("not-read", encoding="utf-8")
        link = self.root / "linked.txt"
        try:
            link.symlink_to(outside)
        except OSError:
            self.skipTest("symlinks are unavailable on this host")
        with self.assertRaises(rcoder_mcp.WorkspaceSecurityError):
            rcoder_mcp.resolve_workspace_path(self.root, "linked.txt")

    def test_error_envelope_and_call_tool_preserve_recovery_guidance(self) -> None:
        envelope = rcoder_mcp.mcp_error_envelope(
            "TEST_CODE", "message", "recovery", {"task": "example"}
        )
        self.assertFalse(envelope["ok"])
        self.assertEqual("recovery", envelope["error"]["recovery_hint"])
        self.assertEqual({"task": "example"}, envelope["error"]["valid_example"])

        result = rcoder_mcp.call_tool("rcoder_scan", {"root": "../outside"})
        self.assertTrue(result["isError"])
        text = result["content"][0]["text"]
        self.assertIn("outside the server root", text)
        self.assertIn("Recovery:", text)
        self.assertEqual(
            "TOOL_ERROR", result["structuredContent"]["error"]["code"]
        )

    def test_preflight_returns_bounded_objective_graph_and_routing(self) -> None:
        (self.root / "main.py").write_text(
            "def main():\n    return 0\n", encoding="utf-8"
        )
        result = rcoder_mcp.call_tool(
            "rcoder_preflight",
            {
                "task": "Implement a Go authentication service with JWT signing and "
                        "PostgreSQL migrations; verify secrets handling and query latency.",
                "root": str(self.root),
                "token_budget": 800,
                "target_files": ["main.py"],
            },
        )
        self.assertFalse(result.get("isError", False))
        payload = json.loads(result["content"][0]["text"])
        self.assertEqual("rcoder_preflight", payload["tool"])
        self.assertEqual(["main.py"], payload["objective"]["target_files"])
        self.assertEqual("compact", payload["scan"]["budget_mode"])
        self.assertEqual("go-engineering", payload["routing"]["primary"])
        self.assertLessEqual(len(payload["routing"]["addendums"]), 2)
        self.assertEqual(3, len(payload["next_actions"]))


class DoctorAndStopGateTests(unittest.TestCase):
    def test_doctor_source_exposes_fix_pipeline(self) -> None:
        source = (ROOT / "scripts" / "rcoder.mjs").read_text(encoding="utf-8")
        for token in (
            "doctor [--json] [--fix]",
            "function applyDoctorFixes()",
            "function doctorWrapperCheck(",
            "function doctorMcpCheck(",
            "mcp:paths:",
            "hooks:registration",
            "SHA256SUMS",
        ):
            self.assertIn(token, source)

    def test_last_verification_exit_code_from_tool_events(self) -> None:
        entries = [
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {"type": "tool_use", "id": "check-1", "name": "Bash",
                         "input": {"command": "python3 -m pytest -q"}}
                    ]
                },
            },
            {
                "type": "user",
                "message": {
                    "content": [
                        {"type": "tool_result", "tool_use_id": "check-1", "is_error": True,
                         "content": [{"type": "text", "text": "1 failed"}]}
                    ]
                },
            },
        ]
        self.assertEqual(1, rcoder_hooks._last_verification_exit_code(entries))
        result = entries[1]["message"]["content"][0]
        result["is_error"] = False
        result["content"][0]["text"] = "1 passed"
        self.assertEqual(0, rcoder_hooks._last_verification_exit_code(entries))

    def test_strict_stop_gate_blocks_drift_and_respects_env_override(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            git(root, "init", "-q")
            policy = root / ".rcoder"
            policy.mkdir()
            (policy / "policy.json").write_text(
                '{"strict_stop": true, "target_files": ["target.py"]}', encoding="utf-8"
            )
            (root / "target.py").write_text("value = 1\n", encoding="utf-8")
            git(root, "add", ".")
            git(root, "commit", "-qm", "initial")

            blocked = rcoder_hooks.evaluate_stop_gate(
                root,
                {
                    "target_files": ["target.py"],
                    "claimed_files": ["target.py"],
                    "last_verification_exit_code": 1,
                },
            )
            self.assertIsNotNone(blocked)
            self.assertIn("strict stop gate", blocked)
            self.assertIn("target.py", blocked)
            self.assertIn("exited 1", blocked)

            (root / "target.py").write_text("value = 2\n", encoding="utf-8")
            self.assertIsNone(
                rcoder_hooks.evaluate_stop_gate(
                    root,
                    {
                        "target_files": ["target.py"],
                        "claimed_files": ["target.py"],
                        "last_verification_exit_code": 0,
                    },
                )
            )

            with mock.patch.dict(os.environ, {"RCODER_STRICT_STOP": "0"}):
                self.assertIsNone(
                    rcoder_hooks.evaluate_stop_gate(
                        root,
                        {
                            "target_files": ["other.py"],
                            "claimed_files": [],
                            "last_verification_exit_code": 1,
                        },
                    )
                )


class VerificationFooterTests(unittest.TestCase):
    def test_every_reference_has_executable_footer(self) -> None:
        references = sorted((SKILL_SCRIPTS.parent / "references").glob("*.md"))
        self.assertEqual(71, len(references))
        heading = "## Executable Verification & Failure Diagnostics"
        for path in references:
            text = path.read_text(encoding="utf-8")
            self.assertEqual(1, text.count(heading), path.name)
            footer = text.split(heading, 1)[1]
            self.assertIn("- **Verify**:", footer)
            self.assertIn("- **Anti-Patterns**:", footer)
            self.assertIn("- **Failure Diagnostics**:", footer)
            self.assertIn("->", footer)
            self.assertNotIn("TODO", footer)
            self.assertNotIn("TBD", footer)
            self.assertNotIn("FIXME", footer)


if __name__ == "__main__":
    unittest.main(verbosity=2)
