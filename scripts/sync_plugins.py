#!/usr/bin/env python3
"""Generate host command surfaces from the canonical bundled RCoder skill commands."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_COMMANDS_DIR = ROOT / "skills" / "rcoder" / "commands"
COMMANDS_DIR = ROOT / "commands"
GEMINI_CMD_DIR = COMMANDS_DIR / "rcoder"
GENERATED_MARKER = "# AUTO-GENERATED — DO NOT EDIT DIRECTLY"
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
                desc = match.group(1).strip().strip('"').strip("'")
    return desc, body.strip()


def generated_markdown(source: str) -> str:
    lines = source.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise ValueError("canonical command must start with YAML frontmatter")
    try:
        end = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration as error:
        raise ValueError("canonical command has unterminated frontmatter") from error
    if not any(GENERATED_MARKER in line for line in lines[1:end]):
        lines.insert(end, GENERATED_MARKER + "\n")
        source = "".join(lines)
    return source if source.endswith("\n") else source + "\n"


def toml_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _write_or_check(path: Path, content: str, check: bool) -> None:
    if check:
        if not path.is_file() or path.read_text(encoding="utf-8") != content:
            raise RuntimeError(f"generated command drift: {path.relative_to(ROOT)}; run python scripts/sync_plugins.py")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)


def sync_command_markdown(check: bool = False) -> list[str]:
    """Generate root-level Claude/Codex command Markdown from skill SSOT."""
    if not CANONICAL_COMMANDS_DIR.is_dir():
        raise FileNotFoundError(f"canonical command directory missing: {CANONICAL_COMMANDS_DIR}")
    names: set[str] = set()
    generated: list[str] = []
    for source in sorted(CANONICAL_COMMANDS_DIR.glob("*.md")):
        names.add(source.name)
        _write_or_check(COMMANDS_DIR / source.name,
                        generated_markdown(source.read_text(encoding="utf-8")), check)
        generated.append(source.name)
    stale = [path for path in COMMANDS_DIR.glob("*.md")
             if path.name not in names and GENERATED_MARKER in path.read_text(encoding="utf-8")]
    if stale:
        if check:
            raise RuntimeError("stale generated command(s): " + ", ".join(path.name for path in stale))
        for path in stale:
            path.unlink()
    return generated


def sync_gemini_toml(check: bool = False) -> list[str]:
    """Generate Gemini CLI TOML prompts from canonical skill command Markdown."""
    if not CANONICAL_COMMANDS_DIR.is_dir():
        raise FileNotFoundError(f"canonical command directory missing: {CANONICAL_COMMANDS_DIR}")
    generated: list[str] = []
    for source in sorted(CANONICAL_COMMANDS_DIR.glob("*.md")):
        description, body = parse_command_md(source)
        content = (
            GENERATED_MARKER + "\n"
            + f'description = "{toml_escape(description)}"\n'
            + 'prompt = """\n'
            + f"{body}\n\nUser request / target arguments: {{{{args}}}}\n"
            + '"""\n'
        )
        target = GEMINI_CMD_DIR / f"{source.stem}.toml"
        _write_or_check(target, content, check)
        generated.append(target.name)
    expected = set(generated)
    stale = [path for path in GEMINI_CMD_DIR.glob("*.toml")
             if path.name not in expected and GENERATED_MARKER in path.read_text(encoding="utf-8")]
    if stale:
        if check:
            raise RuntimeError("stale generated Gemini command(s): " + ", ".join(path.name for path in stale))
        for path in stale:
            path.unlink()
    return generated


def sync_skill_command_prompts(check: bool = False) -> list[str]:
    """Deprecated compatibility alias; MCP prompts already use the skill SSOT."""
    return [path.name for path in sorted(CANONICAL_COMMANDS_DIR.glob("*.md"))]


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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify generated files without writing")
    args = parser.parse_args()
    try:
        markdown = sync_command_markdown(check=args.check)
        tomls = sync_gemini_toml(check=args.check)
        missing = [name for name, ok in verify_manifests().items() if not ok]
        print(json.dumps({"canonical_commands": markdown, "generated_gemini_toml": tomls,
                          "missing_manifests": missing, "check_only": args.check}, indent=2))
        return 1 if missing else 0
    except (OSError, ValueError, RuntimeError) as error:
        print(f"RCoder command sync failed: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
