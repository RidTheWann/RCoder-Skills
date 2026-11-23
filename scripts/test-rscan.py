#!/usr/bin/env python3
"""Deterministic tests for RScan scanning, options, hook payloads, and installer."""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANONICAL = ROOT / "skills" / "rcoder" / "scripts" / "rscan.py"
WRAPPER = ROOT / "scripts" / "rscan.py"


def run(*arguments, entrypoint=CANONICAL):
    return subprocess.run(
        [sys.executable, str(entrypoint), *[str(arg) for arg in arguments]],
        text=True, encoding="utf-8", errors="replace", capture_output=True,
        check=False, timeout=30,
    )


def run_json(*arguments):
    result = run(*arguments)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def build_project(root: Path, complete: bool) -> None:
    (root / "src").mkdir()
    (root / "src" / "main.js").write_text("export const answer = 42;\n", encoding="utf-8")
    (root / "package.json").write_text('{"name":"fixture","scripts":{"test":"node --test"}}\n', encoding="utf-8")
    if complete:
        (root / "README.md").write_text("# Fixture\n", encoding="utf-8")
        (root / "AGENTS.md").write_text("# Agent notes\n", encoding="utf-8")
        (root / "tests").mkdir()
        (root / "tests" / "main.test.js").write_text("test('ok', () => {});\n", encoding="utf-8")
        (root / ".github").mkdir()
        (root / ".github" / "workflows").mkdir()
        (root / ".github" / "workflows" / "ci.yml").write_text("name: ci\n", encoding="utf-8")


def main():
    assert CANONICAL.is_file() and WRAPPER.is_file()
    version = run("--version")
    assert version.returncode == 0 and "RScan 1.11.0" in version.stdout
    wrapper = run("--version", entrypoint=WRAPPER)
    assert wrapper.returncode == 0 and "RScan 1.11.0" in wrapper.stdout

    with tempfile.TemporaryDirectory(prefix="rcoder-rscan-test-") as temporary:
        root = Path(temporary)
        minimal = root / "minimal"
        minimal.mkdir()
        build_project(minimal, complete=False)
        scan = run_json("scan", "--root", str(minimal), "--format", "json")
        assert scan["tool"] == "RScan" and scan["version"] == "1.11.0"
        assert "Node.js / JavaScript / TypeScript" in scan["stacks"]
        assert scan["quality"]["ci"] is False and scan["quality"]["tests"] is False
        risk_ids = {item["id"] for item in scan["risk_signals"]}
        assert {"no_ci", "no_test_entry_point", "no_readme", "no_agent_instructions"} <= risk_ids
        option_ids = {item["id"] for item in scan["development_options"]}
        assert "QUALITY_GATES" in option_ids and "ONBOARD" in option_ids
        assert scan["development_options"][0]["priority"] >= scan["development_options"][-1]["priority"]
        for option in scan["development_options"]:
            assert option["first_commands"] and option["specialists"]

        complete = root / "complete"
        complete.mkdir()
        build_project(complete, complete=True)
        full = run_json("scan", "--root", str(complete), "--format", "json")
        assert full["quality"]["ci"] is True and full["quality"]["tests"] is True
        full_risks = {item["id"] for item in full["risk_signals"]}
        assert "no_ci" not in full_risks and "no_readme" not in full_risks

        # A large alphabetically early source tree must not hide CI and repository metadata.
        spread = root / "spread"
        spread.mkdir()
        (spread / "README.md").write_text("# Spread\\n", encoding="utf-8")
        (spread / "package.json").write_text('{"name":"spread"}\\n', encoding="utf-8")
        (spread / "package-lock.json").write_text("{}\\n", encoding="utf-8")
        deep = spread / ".a-source"
        deep.mkdir()
        for index in range(120):
            (deep / f"module-{index:03}.js").write_text("export const value = 1;\\n", encoding="utf-8")
        workflows = spread / ".github" / "workflows"
        workflows.mkdir(parents=True)
        (workflows / "ci.yml").write_text("name: ci\\n", encoding="utf-8")
        tests_dir = spread / "tests"
        tests_dir.mkdir()
        (tests_dir / "main.test.js").write_text("test('ok', () => {});\\n", encoding="utf-8")
        stratified = run_json("scan", "--root", str(spread), "--max-paths", "10", "--format", "json")
        assert stratified["scan"]["sampling_method"] == "deterministic-stratified-v1"
        assert stratified["scan"]["truncated"] is True
        assert stratified["quality"]["ci"] is True and stratified["quality"]["ci_confidence"] == "observed"
        assert stratified["quality"]["tests"] is True and stratified["quality"]["tests_confidence"] == "observed"
        assert ".github/workflows/ci.yml" in stratified["sampled_paths"]

        # Missing README/lockfile is not a verified absence when the bounded inventory is truncated.
        sparse = root / "sparse-truncated"
        sparse.mkdir()
        (sparse / "package.json").write_text('{"name":"sparse"}\n', encoding="utf-8")
        source_tree = sparse / ".a-source"
        source_tree.mkdir()
        for index in range(2100):
            (source_tree / f"module-{index:04}.js").write_text("export const value = 1;\n", encoding="utf-8")
        uncertain = run_json("scan", "--root", str(sparse), "--max-paths", "10", "--format", "json")
        uncertain_risks = {item["id"] for item in uncertain["risk_signals"]}
        assert uncertain["scan"]["truncated"] is True
        assert uncertain["quality"]["readme_confidence"] == "unknown-truncated"
        assert uncertain["quality"]["lockfile_confidence"] == "unknown-truncated"
        assert "no_readme" not in uncertain_risks
        assert "dependency_without_lock" not in uncertain_risks
\n        text = run("scan", "--root", str(minimal))
        assert text.returncode == 0 and "Development options:" in text.stdout
        markdown = run("scan", "--root", str(minimal), "--format", "markdown")
        assert markdown.returncode == 0 and "## Development options" in markdown.stdout

        claude = run_json("scan", "--root", str(minimal), "--hook", "claude")
        assert claude["hookSpecificOutput"]["hookEventName"] == "SessionStart"
        assert "Development options" in claude["hookSpecificOutput"]["additionalContext"]
        gemini = run_json("scan", "--root", str(minimal), "--hook", "gemini")
        assert "systemMessage" in gemini and "additionalContext" in gemini["hookSpecificOutput"]
        opencode = run("scan", "--root", str(minimal), "--hook", "opencode")
        assert opencode.returncode == 0 and "Development options" in opencode.stdout

        for host in ("claude-code", "gemini-cli"):
            preview = run_json("hooks", "preview", "--host", host)
            event = preview["hooks"]["SessionStart"]
            assert event[0]["matcher"] == "startup"
            assert "rscan.py" in event[0]["hooks"][0]["command"]

        settings_path = complete / ".claude" / "settings.json"
        settings_path.parent.mkdir()
        settings_path.write_text(json.dumps({"hooks": {"PreToolUse": [{"hooks": []}]}}), encoding="utf-8")
        installed = run("hooks", "install", "--host", "claude-code", "--scope", "project", "--root", str(complete))
        assert installed.returncode == 0, installed.stderr
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        assert "PreToolUse" in settings["hooks"] and "SessionStart" in settings["hooks"]
        backups = list(settings_path.parent.glob("settings.json.rscan-backup-*"))
        assert len(backups) == 1
        second = run("hooks", "install", "--host", "claude-code", "--scope", "project", "--root", str(complete))
        assert second.returncode == 0 and "already installed" in second.stdout
        assert len(list(settings_path.parent.glob("settings.json.rscan-backup-*"))) == 1

        adapter_root = root / "adapter-project"
        adapter_root.mkdir()
        adapter = run("hooks", "adapter", "--host", "opencode", "--api", "v1",
                      "--scope", "project", "--root", str(adapter_root))
        assert adapter.returncode == 0, adapter.stderr
        plugin_path = adapter_root / ".opencode" / "plugins" / "rscan.js"
        assert plugin_path.is_file()
        plugin_text = plugin_path.read_text(encoding="utf-8")
        assert "experimental.chat.system.transform" in plugin_text
        assert '"--hook"' in plugin_text and '"opencode"' in plugin_text
        assert "output.system.push(text)" in plugin_text
        assert "node:child_process" in plugin_text and "timeout: 10000" in plugin_text
        assert "startsWith(\"RScan:\")" in plugin_text
        assert "let injected" not in plugin_text
        python_literal = re.search(r'const python = ("(?:[^"\\]|\\.)*");', plugin_text)
        assert python_literal and json.loads(python_literal.group(1)) == sys.executable
        assert run("hooks", "adapter", "--host", "opencode", "--api", "v1",
                   "--scope", "project", "--root", str(adapter_root)).returncode == 0
        preview = run("hooks", "adapter", "--host", "opencode", "--api", "v2",
                      "--scope", "project", "--root", str(adapter_root), "--dry-run")
        assert preview.returncode == 0 and "Plugin.define" in preview.stdout
        v2 = run("hooks", "adapter", "--host", "opencode", "--api", "v2",
                 "--scope", "project", "--root", str(adapter_root))
        v2_text = plugin_path.read_text(encoding="utf-8")
        assert v2.returncode == 0 and "ctx.session.hook(\"context\"" in v2_text
        assert "startsWith(\"RScan:\")" in v2_text
        assert "let injected" not in v2_text and "Bun.spawn" not in v2_text

        invalid = run("scan", "--root", str(root / "missing"))
        assert invalid.returncode == 2
        assert run("scan", "--root", str(minimal), "--max-paths", "1").returncode == 2

    print("PASS rscan: bounded scan, options, hook payloads, and idempotent installer")


if __name__ == "__main__":
    main()
