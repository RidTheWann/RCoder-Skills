#!/usr/bin/env python3
"""Check release completeness, artifact leaks, and generated package hashes."""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
MAX_TEXT_SAMPLE = 1024 * 1024

REQUIRED_PATHS = (
    "README.md", "LICENSE", "AGENTS.md", "CLAUDE.md", "GEMINI.md", "mcp.json", "plugin.json",
    "gemini-extension.json", ".claude-plugin/plugin.json", ".codex-plugin/plugin.json",
    ".opencode/plugins/rcoder.js", "hooks/hooks.json", "skills/rcoder/SKILL.md",
    "skills/rcoder/contracts/rcoder-v2.json", "skills/rcoder/scripts/rcoder_hooks.py",
    "scripts/rcoder.mjs", "scripts/rcoder-hooks.py", "scripts/sync_plugins.py",
    "scripts/verify_parity.py", "scripts/check-dist.py", "launcher/rcoder-mcp.mjs",
    "install.ps1", "install.sh",
)
FORBIDDEN_DIR_SEGMENTS = {
    ".git", ".mcp-live-test", "__pycache__", "node_modules", ".pytest_cache", ".mypy_cache",
    ".venv", "venv", "dist",
}
FORBIDDEN_PATTERNS = (
    re.compile(r"(^|/)evals/runs/[^/]+/raw(/|$)", re.I),
    re.compile(r"\.err$", re.I),
    re.compile(r"(^|/)\.env[^/]*($|/)", re.I),
    re.compile(r"\.(pem|key|p12|pfx|jks|keystore|kdbx)$", re.I),
    re.compile(r"(^|/)(\.npmrc|\.pypirc|\.netrc|\.git-credentials|credentials(\.[^/]*)?|secrets?\.(json|ya?ml|toml))$", re.I),
    re.compile(r"(^|/)\.DS_Store$", re.I),
    re.compile(r"(^|/)\.ssh(/|$)|(^|/)\.aws(/|$)|(^|/)\.gnupg(/|$)|(^|/)\.kube(/|$)", re.I),
)
SECRET_LEAK_RE = re.compile(
    r"(?:gh[pousr]_[A-Za-z0-9_]{30,}|github_pat_[A-Za-z0-9_]{30,}|"
    r"sk-[A-Za-z0-9_-]{24,}|AIza[0-9A-Za-z_-]{35})"
)


def normalize_archive_name(name: str) -> tuple[str, bool]:
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    unsafe = path.is_absolute() or ".." in path.parts or "\x00" in normalized
    normalized = path.as_posix()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized, unsafe


def is_forbidden_archive_member(name: str) -> bool:
    normalized, unsafe = normalize_archive_name(name)
    if unsafe:
        return True
    parts = PurePosixPath(normalized).parts
    if set(parts) & FORBIDDEN_DIR_SEGMENTS:
        return True
    return any(pattern.search(normalized) for pattern in FORBIDDEN_PATTERNS)


def check_required_source_paths(violations: list[str]) -> set[str]:
    files: set[str] = set()
    ignored = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist"}
    for directory, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = sorted(name for name in dirnames if name not in ignored)
        for filename in filenames:
            path = Path(directory) / filename
            files.add(path.relative_to(ROOT).as_posix())
    for required in REQUIRED_PATHS:
        if required not in files:
            violations.append(f"MISSING_REQUIRED: {required}")
    return files


def _archive_required(filename: str) -> set[str]:
    lowered = filename.lower()
    if lowered.endswith(".skill.zip"):
        return {"rcoder/SKILL.md", "rcoder/contracts/rcoder-v2.json", "rcoder/scripts/rcoder_hooks.py"}
    if lowered.endswith(".claude-plugin.zip"):
        return {"hooks/hooks.json", ".claude-plugin/plugin.json", "skills/rcoder/SKILL.md",
                "skills/rcoder/scripts/rcoder_hooks.py"}
    if lowered.endswith(".codex-plugin.zip"):
        return {"plugin.json", ".codex-plugin/plugin.json", "skills/rcoder/SKILL.md"}
    if lowered.endswith(".gemini-extension.zip"):
        return {"gemini-extension.json", "GEMINI.md", "commands/rcoder/doctor.toml",
                "skills/rcoder/SKILL.md"}
    if lowered.endswith(".agent-plugin.zip"):
        return {"plugin.json", "skills/rcoder/SKILL.md"}
    if lowered.endswith("-source.zip"):
        return {f"rcoder/{path}" for path in REQUIRED_PATHS}
    return {"README.md", "LICENSE"}


def inspect_archive(archive_path: Path, violations: list[str]) -> int:
    if not archive_path.is_file():
        violations.append(f"ARCHIVE_MISSING: {archive_path}")
        return 0
    try:
        with zipfile.ZipFile(archive_path, "r") as archive:
            entries: set[str] = set()
            for info in archive.infolist():
                if info.is_dir():
                    continue
                normalized, unsafe = normalize_archive_name(info.filename)
                if unsafe:
                    violations.append(f"UNSAFE_ARCHIVE_PATH: {archive_path.name}:{info.filename}")
                    continue
                entries.add(normalized)
                if is_forbidden_archive_member(normalized):
                    violations.append(f"FORBIDDEN_ARCHIVE_MEMBER: {archive_path.name}:{normalized}")
                    continue
                try:
                    content = archive.read(info)
                except (OSError, RuntimeError, zipfile.BadZipFile) as error:
                    violations.append(f"ARCHIVE_READ_ERROR: {archive_path.name}:{normalized}: {error}")
                    continue
                text = content.decode("utf-8", errors="ignore")
                if SECRET_LEAK_RE.search(text):
                    violations.append(f"POTENTIAL_SECRET_LEAK: {archive_path.name}:{normalized}")
            missing = sorted(_archive_required(archive_path.name) - entries)
            if missing:
                violations.append(f"ARCHIVE_INCOMPLETE: {archive_path.name}: missing {', '.join(missing)}")
            return len(entries)
    except (OSError, zipfile.BadZipFile) as error:
        violations.append(f"INVALID_ARCHIVE: {archive_path.name}: {error}")
        return 0


def verify_checksum_manifest(manifest: Path, violations: list[str]) -> list[Path]:
    if not manifest.is_file():
        return []
    archives: list[Path] = []
    for line in manifest.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 2 or not re.fullmatch(r"[A-Fa-f0-9]{64}", parts[0]):
            violations.append(f"MALFORMED_CHECKSUM: {line}")
            continue
        expected, name = parts
        relative = PurePosixPath(name.replace("\\", "/"))
        if relative.is_absolute() or ".." in relative.parts or len(relative.parts) != 1:
            violations.append(f"UNSAFE_CHECKSUM_PATH: {name}")
            continue
        artifact = DIST / name
        if not artifact.is_file():
            violations.append(f"MISSING_ARTIFACT: {name}")
            continue
        actual = hashlib.sha256(artifact.read_bytes()).hexdigest()
        if actual != expected.lower():
            violations.append(f"HASH_MISMATCH: {name}")
            continue
        archives.append(artifact)
    if not archives:
        violations.append("EMPTY_CHECKSUM_MANIFEST: no verified package archives listed")
    return archives


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, help="inspect one release ZIP, including leaks and completeness")
    parser.add_argument("--strict-workspace", action="store_true",
                        help="also fail when forbidden local artifacts exist in the working tree")
    args = parser.parse_args()
    violations: list[str] = []
    workspace_files = check_required_source_paths(violations)
    archive_count = 0

    if args.strict_workspace:
        for rel in sorted(workspace_files):
            if is_forbidden_archive_member(rel):
                violations.append(f"FORBIDDEN_WORKSPACE_FILE: {rel}")

    if args.archive is not None:
        archive_count += inspect_archive(args.archive.resolve(), violations)
    else:
        checksum_archives = verify_checksum_manifest(DIST / "SHA256SUMS", violations)
        for archive in checksum_archives:
            archive_count += inspect_archive(archive, violations)

    # Check source text for obvious provider token formats. Test/evaluation inputs are inert fixtures.
    for rel in sorted(workspace_files):
        if rel.startswith(("scripts/test-", "scripts/fixtures/", "evals/", ".mcp-live-test/")):
            continue
        path = ROOT / rel
        try:
            if path.stat().st_size <= MAX_TEXT_SAMPLE and SECRET_LEAK_RE.search(
                path.read_bytes().decode("utf-8", errors="ignore")
            ):
                violations.append(f"POTENTIAL_SECRET_LEAK: {rel}")
        except OSError as error:
            violations.append(f"SOURCE_READ_ERROR: {rel}: {error}")

    if violations:
        for item in violations:
            print(f"[check-dist] FAIL: {item}", file=sys.stderr)
        print(f"[check-dist] FAILED with {len(violations)} violation(s).", file=sys.stderr)
        return 1
    scope = str(args.archive.resolve()) if args.archive else (f"{archive_count} release archive(s) and source tree"
                                                               if archive_count else "source tree")
    print(f"[check-dist] PASSED — required files and release hygiene verified in {scope}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
