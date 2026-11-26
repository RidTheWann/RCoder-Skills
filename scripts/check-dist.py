#!/usr/bin/env python3
"""Verify package hashes and reject local test artifacts in release archives."""
from __future__ import annotations

import hashlib
import sys
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"


def is_forbidden_archive_member(name: str) -> bool:
    path = PurePosixPath(name)
    parts = path.parts
    if path.is_absolute() or ".." in parts or ".mcp-live-test" in parts:
        return True
    for index in range(max(0, len(parts) - 3)):
        if parts[index:index + 2] == ("evals", "runs") and parts[index + 3] == "raw":
            return True
    return bool(parts and parts[-1].lower().endswith(".err"))


def main() -> int:
    manifest = DIST / "SHA256SUMS"
    if not manifest.is_file():
        print(f"ERROR: missing {manifest.relative_to(ROOT)}", file=sys.stderr)
        return 1
    checked = 0
    errors = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 2:
            errors.append(f"malformed manifest line: {line}")
            continue
        expected, name = parts
        relative = PurePosixPath(name)
        if relative.is_absolute() or ".." in relative.parts or len(relative.parts) != 1:
            errors.append(f"unsafe artifact path in manifest: {name}")
            continue
        artifact = DIST / name
        if not artifact.is_file():
            errors.append(f"missing artifact: {name}")
            continue
        actual = hashlib.sha256(artifact.read_bytes()).hexdigest()
        checked += 1
        if actual != expected.lower():
            errors.append(f"hash mismatch: {name}")
            continue
        if zipfile.is_zipfile(artifact):
            try:
                with zipfile.ZipFile(artifact) as archive:
                    offenders = [member for member in archive.namelist()
                                 if not member.endswith("/") and is_forbidden_archive_member(member)]
                if offenders:
                    errors.append(f"forbidden archive member(s) in {name}: {', '.join(offenders[:8])}")
            except (OSError, zipfile.BadZipFile) as error:
                errors.append(f"invalid ZIP artifact {name}: {error}")
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    if checked == 0:
        print("ERROR: manifest listed no artifacts", file=sys.stderr)
        return 1
    print(f"PASS: {checked} package hashes and archive hygiene verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
