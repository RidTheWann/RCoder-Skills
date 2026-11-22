#!/usr/bin/env python3
"""Tests for the installer-facing MCP setup helper (skills/rcoder/scripts/rcoder_mcp_setup.py).

Proves: snippets per host, safe JSON merge (other keys kept, backup made, idempotent, never
overwrites a different entry, never rewrites non-strict JSON, refuses symlinks), the Codex TOML
route, and the live self-test. Does not prove that a native host launches the server.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "rcoder"
HELPER = SKILL / "scripts" / "rcoder_mcp_setup.py"


def run(*args, expect=0):
    done = subprocess.run([sys.executable, str(HELPER), *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=120, check=False)
    assert done.returncode == expect, (args, done.returncode, done.stdout, done.stderr)
    return done.stdout


def install_copy(base: Path, root_name: str) -> Path:
    import shutil
    destination = base / root_name / "skills" / "rcoder"
    shutil.copytree(SKILL, destination, ignore=shutil.ignore_patterns("__pycache__"))
    return destination / "scripts" / "rcoder_mcp_modern.py"


def snippet_json(text: str) -> dict:
    start = text.index("{")
    end = text.rindex("}") + 1
    return json.loads(text[start:end])


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="rcoder-mcp-setup-") as raw:
        temp = Path(raw)

        # 1. snippets are valid for every JSON host and project scope uses a relative script path
        project = temp / "project"
        project.mkdir()
        server = install_copy(project, ".cursor")
        base_args = ["--base", str(project), "--server", str(server), "--command", "python"]
        for host, key in (("cursor", "mcpServers"), ("gemini-cli", "mcpServers"),
                          ("qoder", "mcpServers"), ("copilot", "servers"), ("opencode", "mcp")):
            data = snippet_json(run("show", "--host", host, *base_args))
            assert "rcoder" in data[key], (host, data)
        cursor = snippet_json(run("show", "--host", "cursor", *base_args))["mcpServers"]["rcoder"]
        assert cursor["command"] == "python"
        assert cursor["args"][0] == ".cursor/skills/rcoder/scripts/rcoder_mcp_modern.py", cursor
        assert cursor["args"][1:] == ["--root", "."]
        user_snippet = snippet_json(run("show", "--host", "cursor", "--scope", "user", *base_args))
        assert Path(user_snippet["mcpServers"]["rcoder"]["args"][0]).is_absolute()
        assert "claude mcp add rcoder" in run("show", "--host", "claude-code", *base_args)
        assert "[mcp_servers.rcoder]" in run("show", "--host", "codex", "--scope", "user", *base_args)

        # 2. merge keeps unrelated keys, makes a backup, and is idempotent
        config = project / ".cursor" / "mcp.json"
        config.write_text(json.dumps({"theme": "x", "mcpServers": {"other": {"command": "foo"}}}),
                          encoding="utf-8")
        out = run("apply", "--host", "cursor", *base_args)
        assert "[applied]" in out and "tools available" in out, out
        merged = json.loads(config.read_text(encoding="utf-8"))
        assert merged["theme"] == "x" and merged["mcpServers"]["other"] == {"command": "foo"}
        assert merged["mcpServers"]["rcoder"]["command"] == "python"
        assert not config.read_bytes().startswith(b"\xef\xbb\xbf"), "BOM written"
        assert len(list(config.parent.glob("mcp.json.rcoder-backup-*"))) == 1
        assert "[already]" in run("apply", "--host", "cursor", *base_args)
        assert len(list(config.parent.glob("mcp.json.rcoder-backup-*"))) == 1, "idempotent run made a backup"

        # 3. a different existing entry is never overwritten
        merged["mcpServers"]["rcoder"] = {"command": "custom"}
        config.write_text(json.dumps(merged), encoding="utf-8")
        out = run("apply", "--host", "cursor", *base_args)
        assert "[conflict]" in out and "Paste this manually" in out, out
        assert json.loads(config.read_text(encoding="utf-8"))["mcpServers"]["rcoder"] == {"command": "custom"}

        # 4. non-strict JSON (comments) is left byte-for-byte untouched
        gemini = project / ".gemini" / "settings.json"
        gemini.parent.mkdir()
        original = '{\n  // comment\n  "mcpServers": {}\n}\n'
        gemini.write_text(original, encoding="utf-8")
        out = run("apply", "--host", "gemini-cli", *base_args)
        assert "[manual]" in out and gemini.read_text(encoding="utf-8") == original, out

        # 5. new file for opencode gets the schema; VS Code route uses "servers"
        assert "[applied]" in run("apply", "--host", "opencode", *base_args)
        opencode = json.loads((project / "opencode.json").read_text(encoding="utf-8"))
        assert opencode["$schema"] == "https://opencode.ai/config.json"
        assert opencode["mcp"]["rcoder"]["type"] == "local" and opencode["mcp"]["rcoder"]["enabled"] is True
        assert "[applied]" in run("apply", "--host", "copilot", *base_args)
        vscode = json.loads((project / ".vscode" / "mcp.json").read_text(encoding="utf-8"))
        assert vscode["servers"]["rcoder"]["type"] == "stdio"
        assert "[applied]" in run("apply", "--host", "claude-code", *base_args)
        assert "rcoder" in json.loads((project / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]

        # 6. hosts without an automatic route print the snippet instead of writing anything
        out = run("apply", "--host", "qoder", *base_args)
        assert "[manual]" in out and '"mcpServers"' in out, out
        out = run("apply", "--host", "codex", *base_args)  # project scope has no Codex file route
        assert "[manual]" in out, out

        # 7. Codex user scope appends a TOML table once
        home = temp / "home"
        home.mkdir()
        user_server = install_copy(home, ".agents")
        user_args = ["--base", str(home), "--server", str(user_server), "--command", "python",
                     "--scope", "user"]
        toml = home / ".codex" / "config.toml"
        toml.parent.mkdir()
        toml.write_text('model = "x"\n', encoding="utf-8")
        assert "[applied]" in run("apply", "--host", "codex", *user_args)
        text = toml.read_text(encoding="utf-8")
        assert text.startswith('model = "x"') and text.count("[mcp_servers.rcoder]") == 1, text
        assert "[already]" in run("apply", "--host", "codex", *user_args)
        assert toml.read_text(encoding="utf-8").count("[mcp_servers.rcoder]") == 1

        # 8. dry run writes nothing; symlinked config directories are refused
        dry = temp / "dry"
        dry.mkdir()
        dry_server = install_copy(dry, ".cursor")
        run("apply", "--host", "cursor", "--dry-run", "--base", str(dry), "--server", str(dry_server))
        assert not (dry / ".cursor" / "mcp.json").exists()
        linked = temp / "linked"
        outside = temp / "outside"
        linked.mkdir()
        outside.mkdir()
        try:
            os.symlink(outside, linked / ".cursor", target_is_directory=True)
        except (OSError, NotImplementedError):
            print("SKIP symlink refusal (symlinks unavailable here)")
        else:
            out = run("apply", "--host", "cursor", "--base", str(linked), "--server", str(dry_server))
            assert "symbolic link" in out and not any(outside.iterdir()), out

        # 9. verify talks to the real server
        assert "OK:" in run("verify", "--server", str(server), "--base", str(project))
        run("verify", "--server", str(temp / "missing.py"), expect=2)
    print("PASS rcoder_mcp_setup: snippets, safe merge, TOML, refusal cases, verify")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
