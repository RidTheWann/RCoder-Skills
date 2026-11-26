#!/usr/bin/env python3
"""Unified SSOT, contract, and cross-platform integrity gate for RCoder-Skills."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.9-3.10 may use the optional tomli backport.
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:
        tomllib = None  # type: ignore[assignment]

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".mcp-live-test", "node_modules", "__pycache__", ".venv", "venv", ".rcoder", "dist"}
LF_REQUIRED_EXTS = {".py", ".sh", ".mjs", ".js", ".json", ".md", ".toml", ".yml", ".yaml"}
WIN_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}
ABS_PATH_RE = re.compile(r"(?:(?<![A-Za-z0-9_])[A-Za-z]:[\\/]|(?<![A-Za-z0-9_])/(?:Users|home)/)")
SKILL_PATH_RE = re.compile(r"(?:references|assets/templates|contracts)/([A-Za-z0-9_.-]+\.json|[A-Za-z0-9_.-]+\.md)")
AGENT_PATH_RE = re.compile(r"(?:^|[(/`])agents/(rcoder-[a-z0-9-]+\.md)")
CONFIG_FILES_TO_AUDIT = (
    ".mcp.json", "mcp.json", "targets.json", "plugin.json", "gemini-extension.json",
    "skills/rcoder/contracts/rcoder-v2.json",
)
SKILL_MD = ROOT / "skills" / "rcoder" / "SKILL.md"
CONTRACT_JSON = ROOT / "skills" / "rcoder" / "contracts" / "rcoder-v2.json"
TOML_CMD_DIR = ROOT / "commands" / "rcoder"


def _report_lf(path: Path, relative: str, issues: list[str]) -> None:
    try:
        if b"\r\n" in path.read_bytes():
            issues.append(f"[CRLF_LEAK] '{relative}' contains CRLF; normalize to LF.")
    except OSError as error:
        issues.append(f"[READ_ERROR] '{relative}': {error}")


def audit_cross_platform_parity(repo_root: Path = ROOT) -> list[str]:
    issues: list[str] = []
    lower_seen: dict[str, str] = {}
    root = Path(repo_root).resolve()

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(name for name in dirnames if name not in SKIP_DIRS)
        for filename in sorted(filenames):
            full = Path(dirpath) / filename
            rel = full.relative_to(root).as_posix()
            lowered = rel.casefold()
            if lowered in lower_seen and lower_seen[lowered] != rel:
                issues.append(f"[CASE_COLLISION] '{rel}' collides with '{lower_seen[lowered]}' on Windows/macOS.")
            lower_seen[lowered] = rel
            if Path(filename).stem.upper() in WIN_RESERVED:
                reserved = Path(filename).stem.upper()
                issues.append(f"[WIN_RESERVED_NAME] '{rel}' uses Windows reserved device name '{reserved}'.")
            if full.suffix.lower() in LF_REQUIRED_EXTS:
                _report_lf(full, rel, issues)

    for config_rel in CONFIG_FILES_TO_AUDIT:
        config_path = root / config_rel
        if config_path.is_file():
            text = config_path.read_bytes().decode("utf-8", errors="replace")
            if ABS_PATH_RE.search(text):
                issues.append(f"[HARDCODED_OS_PATH] '{config_rel}' contains a machine-specific absolute path.")
    return issues


def verify_generated_commands(issues: list[str]) -> None:
    sync_script = ROOT / "scripts" / "sync_plugins.py"
    result = subprocess.run(
        [sys.executable, str(sync_script), "--check"], cwd=ROOT,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode != 0:
        output = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part.strip())
        issues.append("[SSOT_DRIFT] scripts/sync_plugins.py --check failed:\n" + (output or "(no output)"))


def verify_toml_commands(issues: list[str]) -> None:
    if tomllib is None:
        issues.append("[TOML_UNAVAILABLE] TOML parsing requires Python 3.11+ or the 'tomli' backport.")
        return
    for toml_file in sorted(TOML_CMD_DIR.glob("*.toml")):
        relative = toml_file.relative_to(ROOT).as_posix()
        raw = toml_file.read_bytes()
        if b"\r\n" in raw:
            issues.append(f"[CRLF_LEAK] '{relative}' contains CRLF; normalize to LF.")
        try:
            parsed = tomllib.loads(raw.decode("utf-8"))
            if not isinstance(parsed.get("description"), str) or not parsed["description"].strip():
                issues.append(f"[TOML_REQUIRED] '{relative}' has no description.")
            if not isinstance(parsed.get("prompt"), str) or not parsed["prompt"].strip():
                issues.append(f"[TOML_REQUIRED] '{relative}' has no prompt.")
        except Exception as error:
            issues.append(f"[TOML_INVALID] '{relative}': {error}")


def verify_contract(issues: list[str]) -> None:
    if not CONTRACT_JSON.is_file():
        issues.append("[CONTRACT_MISSING] skills/rcoder/contracts/rcoder-v2.json is missing.")
        return
    raw = CONTRACT_JSON.read_bytes()
    if b"\r\n" in raw:
        issues.append("[CRLF_LEAK] 'skills/rcoder/contracts/rcoder-v2.json' contains CRLF; normalize to LF.")
    try:
        data = json.loads(raw.decode("utf-8"))
        if not isinstance(data, dict) or data.get("contract_id") != "rcoder.v2":
            issues.append("[CONTRACT_INVALID] rcoder-v2.json must be an object with contract_id 'rcoder.v2'.")
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        issues.append(f"[CONTRACT_INVALID] skills/rcoder/contracts/rcoder-v2.json: {error}")


def verify_skill_references(issues: list[str]) -> None:
    if not SKILL_MD.is_file():
        issues.append("[SKILL_MISSING] skills/rcoder/SKILL.md is missing.")
        return
    text = SKILL_MD.read_bytes().decode("utf-8", errors="replace")
    for relative in sorted(set(SKILL_PATH_RE.findall(text))):
        # The regex captures the basename; retain the declared parent directory.
        for directory in ("references", "assets/templates", "contracts"):
            token = f"{directory}/{relative}"
            if token in text:
                candidate = ROOT / "skills" / "rcoder" / directory / relative
                if not candidate.is_file():
                    issues.append(f"[SKILL_REFERENCE_MISSING] SKILL.md references missing file: skills/rcoder/{directory}/{relative}")
    for agent_file in sorted(set(AGENT_PATH_RE.findall(text))):
        if not (ROOT / "agents" / agent_file).is_file():
            issues.append(f"[SKILL_AGENT_MISSING] SKILL.md references missing agent: agents/{agent_file}")


def main() -> int:
    issues = audit_cross_platform_parity(ROOT)
    legacy = ROOT / "scripts" / "verify-parity.py"
    if legacy.exists():
        issues.append("[DUPLICATE_GATE] remove scripts/verify-parity.py; use scripts/verify_parity.py only.")
    verify_generated_commands(issues)
    verify_toml_commands(issues)
    verify_contract(issues)
    verify_skill_references(issues)

    if issues:
        for issue in issues:
            print(issue, file=sys.stderr)
        print(f"[verify_parity] FAILED: {len(issues)} parity or contract issue(s).", file=sys.stderr)
        return 1
    print("[verify_parity] PASSED — SSOT mirrors, manifest versions, TOML, contract, links, and cross-platform parity verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
