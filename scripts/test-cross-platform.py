#!/usr/bin/env python3
"""Cross-platform parity tests for Windows, Linux, and macOS portability."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "rcoder" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import rcoder_mcp  # noqa: E402
import rsaver  # noqa: E402
from platform_runtime import (  # noqa: E402
    isolated_host_environment,
    link_or_copy,
    normalize_portable_mcp_config,
    portable_temp_root,
    resolve_host_command,
    resolve_node_command,
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

    def test_node_and_host_resolvers_are_safe_vectors(self) -> None:
        node = resolve_node_command()
        self.assertTrue(node)
        self.assertTrue(all(isinstance(part, str) for part in node))
        with patch("platform_runtime.shutil.which", return_value="C:\\Tools\\opencode.cmd"):
            self.assertEqual(
                resolve_host_command("opencode"),
                ["cmd.exe", "/c", "C:\\Tools\\opencode.cmd"],
            )
        with patch("platform_runtime.shutil.which", return_value="/usr/local/bin/opencode"):
            self.assertEqual(resolve_host_command("opencode"), ["/usr/local/bin/opencode"])
        with patch("platform_runtime.shutil.which", return_value=None):
            self.assertEqual(resolve_host_command("opencode"), [])

    def test_isolated_environment_removes_credentials_per_os(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            with patch.dict(os.environ, {
                "OPENAI_API_KEY": "must-not-inherit",
                "ANTHROPIC_API_KEY": "must-not-inherit",
                "OPENCODE_SESSION_ID": "ses-ambient",
                "AI_AGENT": "opencode",
                "XDG_CONFIG_HOME": "/ambient/config",
            }), patch("platform_runtime.os.name", "posix"):
                posix = isolated_host_environment(
                    workspace, mock_key="local-fixture", python_command=["/usr/bin/python3"])
            self.assertNotIn("OPENAI_API_KEY", posix)
            self.assertNotIn("ANTHROPIC_API_KEY", posix)
            self.assertNotIn("OPENCODE_SESSION_ID", posix)
            self.assertNotIn("AI_AGENT", posix)
            self.assertEqual(posix["XDG_CONFIG_HOME"], str(workspace / "xdg" / "config"))
            self.assertEqual(posix["PWD"], str(workspace))

            with patch("platform_runtime.os.name", "nt"):
                windows = isolated_host_environment(
                    workspace, mock_key="local-fixture", python_command=["python.exe"])
            self.assertEqual(windows["APPDATA"], str(workspace / "appdata"))
            self.assertEqual(windows["USERPROFILE"], str(workspace))
            self.assertNotIn("XDG_CONFIG_HOME", windows)

    def test_link_or_copy_falls_back_when_symlinks_are_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "source"
            source.mkdir()
            (source / "SKILL.md").write_text("fixture", encoding="utf-8")
            destination = base / "destination"
            with patch.object(Path, "symlink_to", side_effect=OSError("no symlink")):
                link_or_copy(source, destination)
            self.assertEqual((destination / "SKILL.md").read_text(encoding="utf-8"), "fixture")

    def test_portable_temp_root_uses_system_temp(self) -> None:
        with tempfile.TemporaryDirectory() as system_temp:
            with patch("platform_runtime.tempfile.gettempdir", return_value=system_temp):
                result = portable_temp_root("rcoder-e2e")
            self.assertEqual(result, Path(system_temp) / "rcoder-e2e")
            self.assertTrue(result.is_dir())


if __name__ == "__main__":
    unittest.main(verbosity=2)
