#!/usr/bin/env python3
"""Static cross-platform parity verifier for Linux, Windows, and macOS safety gates."""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".rcoder", "dist"}
LF_REQUIRED_EXTS = {".py", ".sh", ".mjs", ".js", ".json", ".md", ".toml", ".yml", ".yaml"}
WIN_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}
ABS_PATH_RE = re.compile(
    r"(?:(?<![A-Za-z0-9_])[A-Za-z]:[\\/]|(?<![A-Za-z0-9_])/(?:Users|home)/)"
)
CONFIG_FILES_TO_AUDIT = [
    ".mcp.json",
    "mcp.json",
    "targets.json",
    "plugin.json",
    "gemini-extension.json",
    "skills/rcoder/contracts/rcoder-v2.json",
]


def audit_cross_platform_parity(repo_root: Path = ROOT) -> list[str]:
    issues: list[str] = []
    lower_seen: dict[str, str] = {}
    root = Path(repo_root).resolve()

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(name for name in dirnames if name not in SKIP_DIRS)
        for filename in sorted(filenames):
            full = Path(dirpath) / filename
            rel = full.relative_to(root).as_posix()
            lowered = rel.lower()
            if lowered in lower_seen and lower_seen[lowered] != rel:
                issues.append(
                    f"[CASE_COLLISION] '{rel}' collides with '{lower_seen[lowered]}' on Windows/macOS."
                )
            lower_seen[lowered] = rel
            if Path(filename).stem.upper() in WIN_RESERVED:
                issues.append(
                    f"[WIN_RESERVED_NAME] '{rel}' uses Windows reserved device name "
                    f"'{Path(filename).stem.upper()}'."
                )
            if full.suffix.lower() in LF_REQUIRED_EXTS:
                try:
                    if b"\r\n" in full.read_bytes():
                        issues.append(f"[CRLF_LEAK] '{rel}' contains CRLF; normalize to LF.")
                except OSError as error:
                    issues.append(f"[READ_ERROR] '{rel}': {error}")

    for config_rel in CONFIG_FILES_TO_AUDIT:
        config_path = root / config_rel
        if config_path.is_file():
            text = config_path.read_text(encoding="utf-8", errors="replace")
            if ABS_PATH_RE.search(text):
                issues.append(
                    f"[HARDCODED_OS_PATH] '{config_rel}' contains a machine-specific absolute path."
                )
    return issues


def main() -> int:
    issues = audit_cross_platform_parity(ROOT)
    if issues:
        for issue in issues:
            print(issue, file=sys.stderr)
        print(f"FAILED: {len(issues)} cross-platform parity issue(s) detected.", file=sys.stderr)
        return 1
    print("OK: Cross-platform parity verified (0 case collisions, 0 CRLF leaks, 0 hardcoded OS paths).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
