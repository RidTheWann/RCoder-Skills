#!/usr/bin/env python3
"""Installer helper for RCoder's built-in RFC store and Runtime companion.

Both subsystems are fail-open: a missing Rust toolchain, an unavailable source
tree, or a failed setup never aborts installation of the portable skill.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import platform
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = SKILL_DIR.parent.parent
RFC_SCRIPT = SKILL_DIR / "scripts" / "context_fabric.py"
BUNDLED_BIN_DIR = Path("runtime") / "bin"
RUNTIME_BINARY_NAME = "rcoder-runtime.exe" if os.name == "nt" else "rcoder-runtime"
ENV_ALLOWLIST = (
    "PATH", "HOME", "USERPROFILE", "SYSTEMROOT", "WINDIR", "TEMP", "TMP",
    "TMPDIR", "LANG", "LC_ALL", "PYTHONUTF8", "PYTHONIOENCODING",
    "RCODER_RUNTIME_PATH", "RCODER_RUNTIME_DISABLE",
)


def safe_env() -> dict[str, str]:
    return {key: os.environ[key] for key in ENV_ALLOWLIST if key in os.environ}


def runtime_candidates() -> list[Path]:
    names = ("rcoder-runtime.exe", "rcoder-runtime") if os.name == "nt" else ("rcoder-runtime",)
    candidates: list[Path] = []
    for name in names:
        located = shutil.which(name)
        if located:
            candidates.append(Path(located))
        home = os.environ.get("HOME") or os.environ.get("USERPROFILE")
        if home:
            candidates.append(Path(home) / ".cargo" / "bin" / name)
    seen: set[str] = set()
    return [item for item in candidates if not (str(item) in seen or seen.add(str(item)))]


def setup_rfc(root: Path, dry_run: bool) -> bool:
    database = root / ".rcoder" / "context-fabric.sqlite3"
    if database.is_file():
        print(f"[RFC] already initialized at {database}")
        return True
    if dry_run:
        print(f"[RFC] would initialize the store at {database}")
        return True
    if not RFC_SCRIPT.is_file():
        print("[RFC] skipped: bundled context_fabric.py is missing", file=sys.stderr)
        return False
    try:
        result = subprocess.run(
            [sys.executable, str(RFC_SCRIPT), "--root", str(root), "stats"],
            env=safe_env(), capture_output=True, text=True, timeout=60, check=False,
        )
    except (OSError, subprocess.SubprocessError) as error:
        print(f"[RFC] skipped: {error}", file=sys.stderr)
        return False
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "unknown error").strip().splitlines()[-1]
        print(f"[RFC] skipped: {detail}", file=sys.stderr)
        return False
    print(f"[RFC] initialized at {database}")
    return True


def platform_key() -> str | None:
    system = platform.system().lower()
    machine = platform.machine().lower()
    if system == "linux" and machine in {"x86_64", "amd64"}:
        return "linux-x64"
    if system == "linux" and machine in {"aarch64", "arm64"}:
        return "linux-arm64"
    if system == "darwin" and machine in {"x86_64", "amd64"}:
        return "macos-x64"
    if system == "darwin" and machine == "arm64":
        return "macos-arm64"
    if system == "windows" and machine in {"amd64", "x86_64"}:
        return "windows-x64"
    return None


def bundled_binary(source: Path | None, key: str) -> Path | None:
    if not source:
        return None
    suffix = ".exe" if os.name == "nt" else ""
    candidate = source / BUNDLED_BIN_DIR / f"rcoder-runtime-{key}{suffix}"
    return candidate if candidate.is_file() else None


def verify_digest(binary: Path, source: Path) -> bool:
    sums = source / BUNDLED_BIN_DIR / "SHA256SUMS"
    expected = None
    if sums.is_file():
        for line in sums.read_text(encoding="utf-8").splitlines():
            parts = line.split()
            if len(parts) == 2 and parts[1] in {binary.name, f"*{binary.name}"}:
                expected = parts[0].lower()
                break
    actual = hashlib.sha256(binary.read_bytes()).hexdigest()
    if expected and expected != actual:
        print(f"[Runtime] refused: checksum mismatch for {binary.name}", file=sys.stderr)
        return False
    if not expected:
        print(f"[Runtime] warning: no SHA256SUMS entry for {binary.name}", file=sys.stderr)
    return True


def asset_name(key: str) -> str:
    return f"rcoder-runtime-{key}.exe" if os.name == "nt" else f"rcoder-runtime-{key}"


def default_release_base(source: Path | None) -> str | None:
    if not source:
        return None
    manifest = source / "package.json"
    try:
        import json
        version = json.loads(manifest.read_text(encoding="utf-8"))["version"]
    except (OSError, ValueError, KeyError):
        return None
    return f"https://github.com/RidTheWann/RCoder-Skills/releases/download/v{version}/"


def normalize_base(base: str | None, source: Path | None) -> str:
    if base:
        return base if "://" in base else Path(base).expanduser().resolve().as_uri() + "/"
    return default_release_base(source) or ""


def download_asset(base_url: str, key: str, home: Path, dry_run: bool) -> bool:
    name = asset_name(key)
    if not base_url:
        return False
    if dry_run:
        print(f"[Runtime] would download {name} from the project release")
        return True
    try:
        with urllib.request.urlopen(base_url.rstrip("/") + "/SHA256SUMS", timeout=30) as response:
            sums = response.read(65536).decode("utf-8", "replace")
        with urllib.request.urlopen(base_url.rstrip("/") + "/" + name, timeout=180) as response:
            length = response.headers.get("Content-Length")
            if length and int(length) > 64 * 1024 * 1024:
                raise ValueError("release asset exceeds the 64 MiB limit")
            payload = response.read(64 * 1024 * 1024 + 1)
    except (OSError, ValueError, urllib.error.URLError) as error:
        print(f"[Runtime] download skipped: {error}", file=sys.stderr)
        return False
    if len(payload) > 64 * 1024 * 1024:
        print("[Runtime] download refused: asset is too large", file=sys.stderr)
        return False
    expected = next((line.split()[0].lower() for line in sums.splitlines()
                     if len(line.split()) == 2 and line.split()[1].lstrip("*") == name), None)
    actual = hashlib.sha256(payload).hexdigest()
    if not expected or expected != actual:
        print(f"[Runtime] download refused: checksum mismatch for {name}", file=sys.stderr)
        return False
    destination_dir = home / ".rcoder" / "bin"
    destination = destination_dir / RUNTIME_BINARY_NAME
    try:
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)
        destination.chmod(0o755)
    except OSError as error:
        print(f"[Runtime] download refused: could not write binary: {error}", file=sys.stderr)
        return False
    print(f"[Runtime] installed release asset {name} at {destination}")
    return True


def setup_runtime(root: Path, source: Path | None, dry_run: bool, home: Path | None = None,
                  release_base: str | None = None) -> bool:
    if os.environ.get("RCODER_RUNTIME_DISABLE", "").strip().lower() in {"1", "true", "yes", "on"}:
        print("[Runtime] skipped: explicitly disabled")
        return False
    existing = next((item for item in runtime_candidates() if item.is_file()), None)
    if existing:
        print(f"[Runtime] ready: {existing}")
        return True
    key = platform_key()
    asset = bundled_binary(source, key) if key else None
    home = home or Path(os.environ.get("HOME") or os.environ.get("USERPROFILE") or root)
    if dry_run:
        if asset:
            print(f"[Runtime] would install the bundled binary {asset.name}")
        elif key:
            print(f"[Runtime] would try the project release asset for {key}")
        else:
            print("[Runtime] no asset for this platform; Runtime stays fail-open")
        return True
    if not asset:
        if key and release_base:
            return download_asset(release_base, key, home, False)
        print(f"[Runtime] skipped: no asset for {platform.platform()} ({key or 'unsupported'})",
              file=sys.stderr)
        return False
    if not verify_digest(asset, source):
        return False
    destination_dir = home / ".rcoder" / "bin"
    destination = destination_dir / RUNTIME_BINARY_NAME
    try:
        destination_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(asset, destination)
        destination.chmod(0o755)
    except OSError as error:
        print(f"[Runtime] skipped: could not install binary: {error}", file=sys.stderr)
        return False
    print(f"[Runtime] installed bundled binary at {destination}")
    if not shutil.which("rcoder-runtime"):
        print("[Runtime] add ~/.rcoder/bin to PATH or set RCODER_RUNTIME_PATH", file=sys.stderr)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    setup = sub.add_parser("setup", help="initialize RFC and detect/build Runtime")
    setup.add_argument("--root", required=True, help="project or user home root")
    setup.add_argument("--source", help="repository/package root containing runtime/")
    setup.add_argument("--home", help="home directory for the bundled Runtime binary")
    setup.add_argument("--release-base", help="base URL/local directory for release assets")
    setup.add_argument("--no-rfc", action="store_true", help="skip RFC store initialization")
    setup.add_argument("--no-runtime", action="store_true", help="skip Runtime setup")
    setup.add_argument("--dry-run", action="store_true", help="print actions without writing")
    args = parser.parse_args()

    root = Path(args.root).expanduser()
    if not root.is_dir():
        parser.error(f"root directory does not exist: {root}")
    source = Path(args.source).expanduser() if args.source else DEFAULT_SOURCE
    if args.command == "setup":
        if not args.no_rfc:
            setup_rfc(root, args.dry_run)
        if not args.no_runtime:
            home = Path(args.home).expanduser() if args.home else None
            base = normalize_base(args.release_base, source if source.is_dir() else None)
            setup_runtime(root, source if source.is_dir() else None, args.dry_run, home, base)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
