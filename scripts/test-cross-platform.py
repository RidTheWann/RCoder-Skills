#!/usr/bin/env python3
"""Cross-platform parity tests for Windows, Linux, and macOS portability."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "rcoder" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import rcoder_mcp  # noqa: E402
import rsaver  # noqa: E402
from platform_runtime import (  # noqa: E402
    normalize_portable_mcp_config,
    resolve_python_command,
    to_native_path,
    to_posix_rel,
)
from rscan_index import IncrementalRepoIndex, compute_test_blast_radius  # noqa: E402


class TestCrossPlatformSync(unittest.TestCase):
    def test_gitattributes_locks_line_endings(self) -> None:
        content = (ROOT / ".gitattributes").read_text(encoding="utf-8")
        self.assertIn("* text=auto eol=lf", content)
        self.assertIn("*.py text eol=lf", content)
        self.assertIn("*.ps1 text eol=crlf", content)
        self.assertIn("*.zip binary", content)

    def test_posix_and_native_path_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            self.assertEqual(
                to_posix_rel(r"skills\rcoder\scripts\rscan.py"),
                "skills/rcoder/scripts/rscan.py",
            )
            native = to_native_path("skills/rcoder/scripts/rscan.py", workspace)
            self.assertEqual(native, workspace / "skills" / "rcoder" / "scripts" / "rscan.py")
            with self.assertRaises(ValueError):
                to_native_path("../outside.txt", workspace)

    def test_portable_mcp_config_strips_hardcoded_os_paths(self) -> None:
        windows_config = {
            "mcpServers": {
                "rcoder": {
                    "command": r"C:\Python312\python.exe",
                    "args": [r"D:\Projects\RCoder-Skills\skills\rcoder\scripts\rcoder_mcp.py"],
                }
            }
        }
        normalized = normalize_portable_mcp_config(windows_config)
        entry = normalized["mcpServers"]["rcoder"]
        self.assertEqual("node", entry["command"])
        self.assertEqual(["launcher/rcoder-mcp.mjs"], entry["args"])

    def test_python_resolver_excludes_windows_store_stub(self) -> None:
        command = resolve_python_command()
        self.assertGreaterEqual(len(command), 1)
        self.assertNotIn("windowsapps", command[0].lower())

    def test_incremental_index_and_blast_radius(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            (workspace / "core.py").write_text(
                "def token_budget() -> int:\n    return 2048\n", encoding="utf-8"
            )
            (workspace / "api.py").write_text("import core\n", encoding="utf-8")
            (workspace / "test_api.py").write_text("import api\n", encoding="utf-8")

            index = IncrementalRepoIndex(workspace)
            first = index.sync_files(["core.py", "api.py", "test_api.py"])
            self.assertEqual(3, first["reindexed"])
            second = index.sync_files(["core.py", "api.py", "test_api.py"])
            self.assertEqual(3, second["cached"])
            self.assertEqual("core.py", index.find_symbol("token_budget")[0]["path"])

            blast = compute_test_blast_radius(
                ["core.py"],
                {"api.py": ["core.py"], "test_api.py": ["api.py"]},
                ["core.py", "api.py", "test_api.py"],
            )
            self.assertIn("test_api.py", blast["recommended_tests"])
            self.assertIn("api.py", blast["impacted_modules"])

    def test_launcher_bridge_probes_python_and_sets_utf8(self) -> None:
        launcher = (ROOT / "launcher" / "rcoder-mcp.mjs").read_text(encoding="utf-8")
        for token in ("spawnSync", "windowsapps", "PYTHONUTF8", "PYTHONIOENCODING",
                      "RCODER_WORKSPACE_ROOT", "RCODER_PYTHON"):
            self.assertIn(token, launcher)

    def test_rsaver_digest_is_crlf_invariant(self) -> None:
        self.assertEqual(rsaver.sha256_text("alpha\r\nbeta\n"), rsaver.sha256_text("alpha\nbeta\n"))
        self.assertEqual(rsaver.normalize_lf("alpha\r\nbeta\n"), "alpha\nbeta\n")

    def test_cli_sync_pipeline_is_wired(self) -> None:
        source = (ROOT / "scripts" / "rcoder.mjs").read_text(encoding="utf-8")
        for token in ("sync [--json]", "function performSync(", "function normalizeJsonPaths(",
                      "sync:validation", "doctor [--json] [--fix]"):
            self.assertIn(token, source)

    def test_new_mcp_tools_are_registered(self) -> None:
        self.assertIn("rcoder_read_symbol", rcoder_mcp.TOOL_INDEX)
        self.assertIn("rcoder_impact_test", rcoder_mcp.TOOL_INDEX)
        for name in ("rcoder_read_symbol", "rcoder_impact_test"):
            schema = rcoder_mcp.TOOL_INDEX[name][3]
            self.assertFalse(schema["additionalProperties"])
            self.assertTrue(schema["type"] == "object")


if __name__ == "__main__":
    unittest.main(verbosity=2)
