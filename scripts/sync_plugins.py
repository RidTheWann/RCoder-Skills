#!/usr/bin/env python3
"""Compile commands/*.md into Gemini CLI slash commands and verify host manifests."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMANDS_DIR = ROOT / "commands"
GEMINI_CMD_DIR = COMMANDS_DIR / "rcoder"
DESCRIPTION_RE = re.compile(r'^description:\s*["\']?(.+?)["\']?\s*$', re.M)


def parse_command_md(md_path: Path) -> tuple[str, str]:
    text = md_path.read_text(encoding="utf-8")
    desc = f"Run RCoder {md_path.stem} workflow"
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            frontmatter, body = parts[1], parts[2].strip()
            match = DESCRIPTION_RE.search(frontmatter)
            if match:
                desc = match.group(1).strip()
    return desc, body.strip()


def toml_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def sync_gemini_toml() -> list[str]:
    GEMINI_CMD_DIR.mkdir(parents=True, exist_ok=True)
    generated: list[str] = []
    for md_file in sorted(COMMANDS_DIR.glob("*.md")):
        desc, body = parse_command_md(md_file)
        toml_path = GEMINI_CMD_DIR / f"{md_file.stem}.toml"
        content = (
            f'description = "{toml_escape(desc)}"\n'
            f'prompt = """\n'
            f"{body}\n\n"
            f"User request / target arguments: {{{{args}}}}\n"
            f'"""\n'
        )
        toml_path.write_text(content, encoding="utf-8")
        generated.append(toml_path.name)
    return generated


def verify_manifests() -> dict[str, bool]:
    required = [
        ROOT / ".claude-plugin" / "plugin.json",
        ROOT / ".claude-plugin" / "marketplace.json",
        ROOT / ".codex-plugin" / "plugin.json",
        ROOT / ".agents" / "plugins" / "marketplace.json",
        ROOT / "gemini-extension.json",
        ROOT / ".opencode" / "plugins" / "rcoder.js",
        ROOT / "mcp.json",
        ROOT / ".mcp.json",
    ]
    return {str(path.relative_to(ROOT)): path.exists() for path in required}


def main() -> int:
    tomls = sync_gemini_toml()
    manifests = verify_manifests()
    missing = [name for name, ok in manifests.items() if not ok]
    print(json.dumps({"gemini_toml_synced": tomls, "missing_manifests": missing}, indent=2))
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
