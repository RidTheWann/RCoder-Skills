#!/usr/bin/env python3
"""Tests for the v3 swarm, memory ledger, plugin compiler, and MCP live surfaces."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "rcoder" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT / "scripts"))

import rcoder_mcp as core  # noqa: E402
import rcoder_mcp_modern as modern  # noqa: E402
import sync_plugins  # noqa: E402
from rcoder_memory import RCoderMemoryStore  # noqa: E402
from rcoder_swarm import RCoderSwarm, SwarmCoordinator, SwarmTask  # noqa: E402


class TestEpisodicLedger(unittest.TestCase):
    def test_record_recall_and_recent_redact_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = RCoderMemoryStore(Path(temporary))
            episode = store.record(
                "fix",
                "sqlite locked on Windows",
                "wrap connect in closing, token sk-proj-secret1234567890abcd",
                [r"skills\rcoder\scripts\rscan_index.py"],
                ["sqlite3.connect"],
            )
            hits = store.recall_for_context("sqlite locked windows", ["rscan_index.py"])
            self.assertEqual(1, len(hits))
            self.assertNotIn("sk-proj-", hits[0]["summary"])
            self.assertEqual(["skills/rcoder/scripts/rscan_index.py"], hits[0]["files"])
            self.assertEqual(episode, store.recent(1)[0]["id"])
            with self.assertRaises(ValueError):
                store.record("unknown", "x", "y")


class TestDAGSwarm(unittest.TestCase):
    def test_waves_verifier_gate_and_blackboard(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            swarm = RCoderSwarm(workspace)
            tasks = [
                SwarmTask("a", "rcoder-explorer", "explore"),
                SwarmTask("b", "rcoder-reviewer", "review", depends_on=["a"]),
                SwarmTask("c", "rcoder-planner", "plan", depends_on=["a"]),
            ]

            def runner(task, exec_root, context):
                return {"ok": True, "saw_a": "task:a" in context["blackboard"]}

            result = swarm.execute(tasks, runner)
            self.assertEqual(3, result["waves"])
            self.assertEqual(["a", "b", "c", "gate-verify"],
                             [item["task_id"] for item in result["tasks"]])
            self.assertTrue(all(item["status"] == "completed" for item in result["tasks"]))
            self.assertIn("task:a", result["blackboard"])

    def test_invalid_graphs_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            swarm = RCoderSwarm(Path(temporary))
            with self.assertRaises(ValueError):
                swarm._build_waves([SwarmTask("x", "rcoder-explorer", "x", depends_on=["missing"])])
            with self.assertRaises(ValueError):
                swarm._build_waves([
                    SwarmTask("x", "rcoder-explorer", "x", depends_on=["y"]),
                    SwarmTask("y", "rcoder-planner", "y", depends_on=["x"]),
                ])

    def test_legacy_coordinator_remains_available(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            self.assertTrue(SwarmCoordinator(Path(temporary)).claim_files("a", ["x.py"])["granted"])


class TestPluginCompiler(unittest.TestCase):
    def test_frontmatter_parser_and_generated_tomls(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            md = Path(temporary) / "demo.md"
            md.write_text('---\ndescription: "Demo workflow"\n---\nBody $ARGUMENTS\n', encoding="utf-8")
            description, body = sync_plugins.parse_command_md(md)
            self.assertEqual("Demo workflow", description)
            self.assertEqual("Body $ARGUMENTS", body)
        self.assertEqual('a\\"b', sync_plugins.toml_escape('a"b'))
        commands = sorted(path.stem for path in (ROOT / "commands").glob("*.md"))
        tomls = sorted(path.stem for path in sync_plugins.GEMINI_CMD_DIR.glob("*.toml"))
        self.assertEqual(commands, tomls)


class TestModernMCPSurfaces(unittest.TestCase):
    def test_live_resources_and_command_prompts(self) -> None:
        core.State.root = ROOT
        resources = modern.modern_result("resources/list", {})["resources"]
        uris = {item["uri"] for item in resources}
        self.assertTrue({
            "rcoder://repo/map", "rcoder://memory/recall", "rcoder://capsule/latest"
        } <= uris)
        commands = modern.command_prompts()
        self.assertEqual(13, len(commands))
        prompts = modern.modern_result("prompts/list", {})["prompts"]
        self.assertTrue(any(item["name"].startswith(modern.PROMPT_PREFIX) for item in prompts))
        built = modern.modern_result(
            "prompts/get",
            {"name": "rcoder_cmd_scan", "arguments": {"args": "auth module"}},
        )
        self.assertIn("auth module", built["messages"][0]["content"]["text"])

    def test_destructive_gate_is_capability_opt_in(self) -> None:
        core.State.root = ROOT
        args = {"edits": [{"path": "src/auth/login.py", "old_text": "a", "new_text": "b"}]}
        with mock.patch.object(core, "handle", return_value={"content": [], "isError": False}) as handle:
            plain = modern.modern_result("tools/call", {"name": "rcoder_apply_verify", "arguments": args,
                "_meta": {modern.META_VERSION: modern.MODERN_PROTOCOL}})
            handle.assert_called_once()
        self.assertFalse(plain.get("isError"))
        meta = {modern.META_VERSION: modern.MODERN_PROTOCOL, "capabilities": {"elicitation": {}}}
        blocked = modern.modern_result("tools/call", {"name": "rcoder_apply_verify", "arguments": args,
            "_meta": meta})
        self.assertTrue(blocked["isError"])
        self.assertEqual("CONFIRMATION_REQUIRED", blocked["structuredContent"]["error"]["code"])
        self.assertEqual(modern.ELICITATION_METHOD,
                         blocked["structuredContent"]["elicitation"]["method"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
