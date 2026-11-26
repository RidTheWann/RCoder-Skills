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
import rcoder_mcp_modern as modern  # noqa: E402
import rsaver_guard  # noqa: E402
import rsaver_sandbox  # noqa: E402
import sync_plugins  # noqa: E402
from rcoder_memory import EpisodicLessonStore, RCoderMemoryStore, _sanitize  # noqa: E402
from rcoder_swarm import RCoderSwarm, SwarmCoordinator, SwarmTask  # noqa: E402
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


class TestV3Architecture(unittest.TestCase):
    def test_fts5_memory_records_recalls_and_redacts(self) -> None:
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

    def test_dag_swarm_verifier_gate_and_blackboard(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            swarm = RCoderSwarm(Path(temporary))
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

    def test_invalid_swarm_graphs_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            swarm = RCoderSwarm(Path(temporary))
            with self.assertRaises(ValueError):
                swarm._build_waves([SwarmTask("x", "rcoder-explorer", "x", depends_on=["missing"])])
            with self.assertRaises(ValueError):
                swarm._build_waves([
                    SwarmTask("x", "rcoder-explorer", "x", depends_on=["y"]),
                    SwarmTask("y", "rcoder-planner", "y", depends_on=["x"]),
                ])

    def test_plugin_compiler_frontmatter_and_toml_parity(self) -> None:
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
        for path in sync_plugins.GEMINI_CMD_DIR.glob("*.toml"):
            self.assertNotIn("\r", path.read_bytes().decode("utf-8"))

    def test_modern_live_resources_and_command_prompts(self) -> None:
        rcoder_mcp.State.root = ROOT
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
            "prompts/get", {"name": "rcoder_cmd_scan", "arguments": {"args": "auth module"}}
        )
        self.assertIn("auth module", built["messages"][0]["content"]["text"])

    def test_destructive_gate_is_capability_opt_in(self) -> None:
        rcoder_mcp.State.root = ROOT
        args = {"edits": [{"path": "src/auth/login.py", "old_text": "a", "new_text": "b"}]}
        with mock.patch.object(rcoder_mcp, "handle", return_value={"content": [], "isError": False}) as handle:
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



class TestCodexConnectorRegressions(unittest.TestCase):
    def test_sudo_no_argument_flags_and_exclusion_only_pathspecs_are_denied(self) -> None:
        for command in (
            "sudo -P rm -rf /",
            "sudo --preserve-env rm -rf /",
            "git add -A ':!secret'",
            "git add ':!secret'",
        ):
            decision = rcoder_hooks.decide_tool(
                {"tool_name": "Bash", "tool_input": {"command": command}}
            )
            self.assertEqual("deny", decision[0], command)
        opencode = rcoder_hooks.decide_tool(
            {"tool": "read", "output": {"args": {"filePath": ".env"}}}
        )
        self.assertIsNotNone(opencode)
        self.assertEqual("deny", opencode[0])

    def test_unquoted_secret_assignments_are_redacted(self) -> None:
        self.assertEqual(
            "API_KEY=[REDACTED_SECRET]",
            _sanitize("API_KEY=supersecret123"),
        )
        self.assertEqual(
            "password=[REDACTED_SECRET]",
            _sanitize("password=anothersecret456"),
        )

    def test_impact_test_does_not_fabricate_missing_js_test_script(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            (workspace / "package.json").write_text(
                '{"scripts":{},"devDependencies":{}}', encoding="utf-8"
            )
            self.assertIsNone(
                rcoder_mcp._detected_test_command(workspace, ["src/a.test.ts"])
            )
            (workspace / "package.json").write_text(
                '{"scripts":{},"devDependencies":{"vitest":"^3"}}', encoding="utf-8"
            )
            self.assertEqual(
                "npx --no-install vitest run",
                rcoder_mcp._detected_test_command(workspace, []),
            )

    def test_nested_rust_symbols_are_indexed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            source = workspace / "nested.rs"
            source.write_text(
                "mod inner {\n    pub struct NestedType;\n"
                "    impl NestedType {\n        pub fn inner_method(&self) {}\n    }\n}\n",
                encoding="utf-8",
            )
            index = IncrementalRepoIndex(workspace)
            index.sync_files(["nested.rs"])
            self.assertEqual("nested.rs", index.find_symbol("NestedType")[0]["path"])
            self.assertEqual("nested.rs", index.find_symbol("inner_method")[0]["path"])

    def test_rcoder_learn_writes_to_fts5_memory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            previous = rcoder_mcp.State.root
            try:
                rcoder_mcp.State.root = workspace
                result = rcoder_mcp.tool_learn({
                    "root": str(workspace),
                    "symptom": "FTS5 lesson integration regression",
                    "root_cause": "normal MCP learning used only the JSONL ledger",
                    "verified_fix": "write the verified lesson to the shared FTS5 store",
                    "related_files": ["src/memory.py"],
                    "tags": ["memory", "mcp"],
                })
                self.assertTrue(result["ok"])
                hits = RCoderMemoryStore(workspace).recall_for_context(
                    "FTS5 lesson integration"
                )
                self.assertTrue(hits)
                self.assertEqual("FTS5 lesson integration regression", hits[0]["title"])
            finally:
                rcoder_mcp.State.root = previous

    def test_concurrent_claims_are_serialized_by_persistent_lock(self) -> None:
        import threading
        from concurrent.futures import ThreadPoolExecutor

        with tempfile.TemporaryDirectory() as temporary:
            swarm = SwarmCoordinator(Path(temporary))
            barrier = threading.Barrier(2)

            def claim(agent: str):
                barrier.wait(timeout=5)
                return swarm.claim_files(agent, ["shared/concurrent.py"])

            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(claim, ["agent-a", "agent-b"]))
            self.assertEqual(1, sum(1 for result in results if result["granted"]))
            self.assertTrue(swarm.leases_path.with_suffix(".lock").exists())

    def test_worktree_diff_includes_untracked_file_contents(self) -> None:
        from rcoder_swarm import WorktreeManager

        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            (repo / "tracked.txt").write_text("baseline\n", encoding="utf-8")
            subprocess.run(["git", "add", "tracked.txt"], cwd=repo, check=True)
            subprocess.run(
                ["git", "-c", "user.email=test@example.invalid", "-c", "user.name=Test",
                 "commit", "-qm", "initial"],
                cwd=repo, check=True,
            )
            (repo / "new_worker.py").write_text(
                "print('new worker survives')\n", encoding="utf-8"
            )
            manager = WorktreeManager(repo, repo.parent / "scratch")
            diff = manager.collect_diff(repo)
            self.assertIn("new_worker.py", diff)
            self.assertIn("+print('new worker survives')", diff)
            status = subprocess.run(
                ["git", "status", "--porcelain"], cwd=repo,
                capture_output=True, text=True, check=True,
            ).stdout
            self.assertIn("?? new_worker.py", status)

    def test_supplied_verifier_is_ordered_after_all_work(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            swarm = RCoderSwarm(Path(temporary))
            tasks = [
                SwarmTask("work-a", "rcoder-debugger", "change A"),
                SwarmTask("work-b", "rcoder-debugger", "change B"),
                SwarmTask("verify", "rcoder-verifier", "verify both"),
            ]
            result = swarm.execute(tasks, lambda task, root, context: {"ok": True})
            self.assertEqual(2, result["waves"])
            self.assertEqual(["work-a", "work-b"], tasks[2].depends_on)

    def test_user_scope_mcp_repair_keeps_active_project_root(self) -> None:
        source = (ROOT / "scripts" / "rcoder.mjs").read_text(encoding="utf-8")
        self.assertIn("path.join(PACKAGE_ROOT, 'launcher', 'rcoder-mcp.mjs')", source)
        self.assertIn("delete entry.cwd", source)
        self.assertNotIn("'--root', PACKAGE_ROOT", source)


def rcoder_swarm_source() -> str:
    return (SCRIPTS / "rcoder_swarm.py").read_text(encoding="utf-8")


if __name__ == "__main__":
    unittest.main(verbosity=2)
