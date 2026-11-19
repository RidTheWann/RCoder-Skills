#!/usr/bin/env python3
"""Verify dist/SHA256SUMS against the built package artifacts."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"


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
        artifact = DIST / name
        if not artifact.is_file():
            errors.append(f"missing artifact: {name}")
            continue
        actual = hashlib.sha256(artifact.read_bytes()).hexdigest()
        checked += 1
        if actual != expected.lower():
            errors.append(f"hash mismatch: {name}")
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    if checked == 0:
        print("ERROR: manifest listed no artifacts", file=sys.stderr)
        return 1
    print(f"PASS: {checked} package artifact hashes verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
