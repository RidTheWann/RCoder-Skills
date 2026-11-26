#!/usr/bin/env python3
"""Compile commands/*.md into Gemini CLI slash commands and verify host manifests."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMANDS_DIR = ROOT / "commands"
GEMINI_CMD_DIR = COMMANDS_DIR / "rcoder"
SKILL_COMMANDS_DIR = ROOT / "skills" / "rcoder" / "commands"
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
        with toml_path.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        generated.append(toml_path.name)
    return generated



def sync_skill_command_prompts() -> list[str]:
    """Bundle MCP prompt sources inside the skill tree for skill-only installations."""
    SKILL_COMMANDS_DIR.mkdir(parents=True, exist_ok=True)
    synced: list[str] = []
    source_names = set()
    for md_file in sorted(COMMANDS_DIR.glob("*.md")):
        source_names.add(md_file.name)
        target = SKILL_COMMANDS_DIR / md_file.name
        content = md_file.read_text(encoding="utf-8")
        with target.open("w", encoding="utf-8", newline="\\n") as handle:
            handle.write(content)
        synced.append(md_file.name)
    for target in SKILL_COMMANDS_DIR.glob("*.md"):
        if target.name not in source_names:
            target.unlink()
    return synced


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
    skill_prompts = sync_skill_command_prompts()
    manifests = verify_manifests()
    missing = [name for name, ok in manifests.items() if not ok]
    print(json.dumps({"gemini_toml_synced": tomls, "skill_prompts_synced": skill_prompts,
                      "missing_manifests": missing}, indent=2))
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
