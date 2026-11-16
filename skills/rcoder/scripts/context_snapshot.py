#!/usr/bin/env python3
"""Emit a bounded, read-only repository context map for coding agents.

This helper lists paths and Git state only; it never prints source-file contents,
reads secrets, follows symlinks, or performs network operations.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

SKIP = {
    ".git", ".hg", ".svn", "node_modules", "vendor", "dist", "build",
    "target", ".venv", "venv", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", ".next", ".nuxt", ".turbo",
    "coverage", "DerivedData", ".gradle", ".idea",
}
KEY_FILES = {
    "AGENTS.md", "CLAUDE.md", "GEMINI.md", "README.md", "CONTRIBUTING.md",
    "package.json", "pnpm-lock.yaml", "yarn.lock", "package-lock.json",
    "pyproject.toml", "requirements.txt", "Cargo.toml", "Cargo.lock",
    "go.mod", "go.sum", "pom.xml", "build.gradle", "build.gradle.kts",
    "global.json", "*.sln", "CMakeLists.txt", "Makefile", "justfile",
    "Dockerfile", "compose.yaml", "docker-compose.yml", "Taskfile.yml",
    "tsconfig.json", "vite.config.ts", "next.config.js",
}

def git_summary(root: Path) -> dict[str, str]:
    def run(args: list[str]) -> str:
        try:
            result = subprocess.run(
                ["git", *args], cwd=root, text=True, capture_output=True,
                timeout=3, check=False,
            )
            return result.stdout.strip() if result.returncode == 0 else ""
        except (OSError, subprocess.TimeoutExpired):
            return ""
    branch = run(["branch", "--show-current"])
    status = run(["status", "--short", "--branch", "--untracked-files=no"])
    return {"branch": branch or "unavailable", "status": status[:1600] or "clean / unavailable"}

def collect(root: Path, max_paths: int, max_depth: int) -> tuple[list[str], list[str], bool]:
    paths: list[str] = []
    keys: list[str] = []
    truncated = False
    stack: list[tuple[Path, int]] = [(root, 0)]
    while stack:
        folder, depth = stack.pop()
        try:
            entries = sorted(os.scandir(folder), key=lambda e: e.name.lower())
        except OSError:
            continue
        child_dirs: list[Path] = []
        for entry in entries:
            if entry.is_symlink():
                continue
            rel = Path(entry.path).relative_to(root).as_posix()
            if entry.is_dir(follow_symlinks=False):
                if entry.name not in SKIP and not entry.name.startswith(".cache") and depth < max_depth:
                    child_dirs.append(Path(entry.path))
            elif entry.is_file(follow_symlinks=False):
                paths.append(rel)
                if entry.name in KEY_FILES or any(
                    pattern.startswith("*.") and entry.name.endswith(pattern[1:])
                    for pattern in KEY_FILES
                ):
                    keys.append(rel)
                if len(paths) >= max_paths:
                    truncated = True
                    return sorted(paths), sorted(set(keys)), truncated
        for child in reversed(child_dirs):
            stack.append((child, depth + 1))
    return sorted(paths), sorted(set(keys)), truncated

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="Repository root (default: current directory)")
    parser.add_argument("--max-paths", type=int, default=80, help="Maximum file paths to list (10..300)")
    parser.add_argument("--max-depth", type=int, default=3, help="Maximum directory depth (1..6)")
    parser.add_argument("--json", action="store_true", help="Emit compact JSON")
    args = parser.parse_args()
    if not 10 <= args.max_paths <= 300 or not 1 <= args.max_depth <= 6:
        parser.error("--max-paths must be 10..300 and --max-depth must be 1..6")
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        parser.error(f"root is not a directory: {root}")
    paths, key_files, truncated = collect(root, args.max_paths, args.max_depth)
    data = {
        "root": str(root),
        "git": git_summary(root),
        "key_files": key_files,
        "file_paths": paths,
        "truncated": truncated,
        "source_contents_included": False,
    }
    if args.json:
        rendered = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    else:
        lines = [
            f"ROOT: {data['root']}",
            f"GIT BRANCH: {data['git']['branch']}",
            f"GIT STATUS: {data['git']['status']}",
            f"KEY FILES ({len(key_files)}):",
            *(f"  {p}" for p in key_files),
            f"FILE PATH SAMPLE ({len(paths)}):",
            *(f"  {p}" for p in paths),
            f"TRUNCATED: {'yes' if truncated else 'no'}",
            "SOURCE CONTENTS: not read",
        ]
        rendered = "\n".join(lines)
    print(rendered)
    print(f"ESTIMATED TOKENS: {(len(rendered) + 3) // 4} (rough character heuristic)", file=__import__("sys").stderr)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
