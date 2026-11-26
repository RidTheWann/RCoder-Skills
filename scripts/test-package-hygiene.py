#!/usr/bin/env python3
"""Regression tests for source-package exclusions and archive hygiene."""
from __future__ import annotations

import runpy
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
excluded = runpy.run_path(str(ROOT / "scripts" / "package"))["is_excluded"]
forbidden = runpy.run_path(str(ROOT / "scripts" / "check-dist.py"))["is_forbidden_archive_member"]

assert excluded(Path(".mcp-live-test/transcript.txt"))
assert excluded(Path("evals/runs/run-1/raw/provider.jsonl"))
assert excluded(Path("tmp/test.err"))
assert excluded(Path(".env"))
assert excluded(Path("config/.env.production"))
assert excluded(Path("certs/identity.pem"))
assert excluded(Path(".ssh/id_ed25519"))
assert excluded(Path("secrets/service-account.json"))
assert excluded(Path(".env.example"))
assert not excluded(Path("evals/runs/run-1/summary.json"))
assert not excluded(Path("skills/rcoder/references/architecture.md"))
assert forbidden("rcoder/.env.production")
assert forbidden("rcoder/certs/service.key")
assert not forbidden("rcoder/skills/rcoder/SKILL.md")

with tempfile.TemporaryDirectory() as temp:
    archive_path = Path(temp) / "sample.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("rcoder/README.md", "safe")
        archive.writestr("rcoder/.mcp-live-test/session.log", "local")
        archive.writestr("rcoder/.env.local", "local")
        archive.writestr("rcoder/evals/runs/run-1/raw/model.jsonl", "local")
        archive.writestr("rcoder/logs/failure.err", "local")
        archive.writestr("../outside.txt", "unsafe")
    with zipfile.ZipFile(archive_path) as archive:
        offenders = [name for name in archive.namelist() if forbidden(name)]
    assert "rcoder/README.md" not in offenders
    assert len(offenders) == 5, offenders

print("package hygiene: source exclusions and ZIP member policy passed")
