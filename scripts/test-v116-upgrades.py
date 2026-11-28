#!/usr/bin/env python3
"""Offline regression tests for RCoder v1.17.1 runtime, parity, resources, and skill prompts."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "skills" / "rcoder" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import platform_runtime  # noqa: E402
import rcoder_mcp as core  # noqa: E402
import rcoder_mcp_modern as modern  # noqa: E402
sys.path.insert(0, str(ROOT / "scripts"))
import sync_plugins  # noqa: E402


class TestV116Upgrades(unittest.TestCase):
    def test_runtime_environment_detector_and_termux_signal(self) -> None:
        info = platform_runtime.detect_runtime_environment(ROOT)
        self.assertIn("runtime", info)
        self.assertIn("stack_markers", info)
        self.assertIn("package.json", info["stack_markers"])
        with mock.patch.dict(os.environ, {
            "TERMUX_VERSION": "0.118.1",
            "PREFIX": "/data/data/com.termux/files/usr",
        }):
            termux_info = platform_runtime.detect_runtime_environment(ROOT)
            self.assertTrue(termux_info["is_termux"])
            self.assertEqual(termux_info["runtime"], "android-termux")

    def test_mcp_parity_audit_and_runtime_profile_tools(self) -> None:
        parity = core.tool_parity_audit({"root": str(ROOT)})
        self.assertTrue(parity["ok"])
        self.assertTrue(parity["healthy"], parity)
        self.assertGreaterEqual(parity["commands"]["md_count"], 16)
        self.assertEqual(parity["commands"]["md_count"], parity["commands"]["toml_count"])
        runtime = core.tool_runtime_profile({"root": str(ROOT)})
        self.assertTrue(runtime["ok"])
        self.assertEqual(runtime["version"], core.product_version())
        self.assertIn("rcoder_state", runtime)

    def test_modern_mcp_live_resources(self) -> None:
        parity = json.loads(modern.read_live_resource("rcoder://parity/matrix")["text"])
        runtime = json.loads(modern.read_live_resource("rcoder://runtime/profile")["text"])
        self.assertTrue(parity["healthy"])
        self.assertEqual(runtime["tool"], "rcoder_runtime_profile")
        names = {item["uri"] for item in modern.live_resources()}
        self.assertIn("rcoder://parity/matrix", names)
        self.assertIn("rcoder://runtime/profile", names)

    def test_skill_only_command_prompts_are_complete(self) -> None:
        prompts = modern.command_prompts()
        self.assertGreaterEqual(len(prompts), 16)
        for name in ("rcoder_cmd_context-pack", "rcoder_cmd_mcp-inspect", "rcoder_cmd_parity-sync"):
            self.assertIn(name, prompts)
        source = ROOT / "commands"
        canonical = ROOT / "skills" / "rcoder" / "commands"
        self.assertEqual(0, subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "sync_plugins.py"), "--check"],
            capture_output=True, text=True, encoding="utf-8", errors="replace").returncode)
        canonical_files = sorted(canonical.glob("*.md"))
        canonical_names = [path.name for path in canonical_files]
        self.assertEqual(canonical_names, sorted(path.name for path in source.glob("*.md")))
        self.assertEqual([p.stem + ".toml" for p in canonical_files],
                         sorted(path.name for path in sync_plugins.GEMINI_CMD_DIR.glob("*.toml")))
        for command in canonical_files:
            generated = source / command.name
            self.assertIn(sync_plugins.MARKDOWN_MARKER, generated.read_text(encoding="utf-8"))
            self.assertEqual(sync_plugins.parse_frontmatter(sync_plugins.read_utf8_lf(generated)),
                             sync_plugins.parse_frontmatter(sync_plugins.read_utf8_lf(command)))

    def test_version_and_default_eval_data_are_packaged(self) -> None:
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(package["version"], "1.17.1")
        self.assertIn("evals/**", package.get("files", []))
        for manifest in (
            ROOT / "plugin.json",
            ROOT / "gemini-extension.json",
            ROOT / ".claude-plugin" / "plugin.json",
            ROOT / ".codex-plugin" / "plugin.json",
        ):
            self.assertEqual(json.loads(manifest.read_text(encoding="utf-8"))["version"], "1.17.1")


if __name__ == "__main__":
    unittest.main()
