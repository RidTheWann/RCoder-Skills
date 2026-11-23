#!/usr/bin/env python3
"""Regression tests for RCoder skill new/lint/package authoring workflows."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "skills" / "rcoder" / "scripts" / "skill_authoring.py"


def run(*args, expect=0):
    done = subprocess.run([sys.executable, str(TOOL), *[str(x) for x in args]],
                          cwd=ROOT, text=True, encoding="utf-8", capture_output=True,
                          timeout=30, check=False)
    assert done.returncode == expect, (args, done.returncode, done.stdout, done.stderr)
    return done.stdout + done.stderr


def main():
    with tempfile.TemporaryDirectory(prefix="rcoder-skill-author-") as raw:
        temp = Path(raw)
        skill = temp / "my-domain-skill"
        created = json.loads(run("new", "my-domain-skill", "--dest", skill,
                                 "--description", "Use when implementing and verifying a focused domain workflow.",
                                 "--json"))
        assert created["version"] == "0.1.0" and (skill / "SKILL.md").is_file()
        assert (skill / "assets" / "templates" / "expert-module-template.md").is_file()
        lint = json.loads(run("lint", skill, "--json"))
        assert lint["ok"] is True and lint["files"] == 2

        # Full specialist reference structure is accepted; incomplete specialist modules are rejected.
        references = skill / "references"
        references.mkdir()
        module = references / "domain.md"
        module.write_text("""# Domain specialist

## Activate when
Concrete signal and one negative trigger.

## Mission and expertise
Own a clear deliverable.

## Mental model
One invariant.

## Prerequisites and reconnaissance
Inspect the relevant source.

## Procedure
1. Inspect.
2. Decide.
3. Implement.
4. Test.
5. Review.

## Decision tree
- A -> B

## Tool strategy
Use only observed tools.

## Advanced techniques
Measure before changing.

## Failure modes
- Failure -> diagnosis -> recovery.

## Quality checklist
- [ ] Pass.

## Anti-patterns
- Do not guess.

## Verification
Run a reproducible test.

## Output format
Findings and evidence.
""", encoding="utf-8")
        assert json.loads(run("lint", skill, "--json"))["ok"] is True
        module.write_text("# Domain specialist\n\n## Activate when\nOnly one section.\n", encoding="utf-8")
        bad = json.loads(run("lint", skill, "--json"))
        assert bad["ok"] is False and any("missing" in item for item in bad["errors"])
        module.unlink()

        # Local links must resolve and cannot leave the skill root.
        readme = skill / "references" / "notes.md"
        references.rmdir()
        (skill / "references").mkdir()
        readme.write_text("# Notes\n\n[Missing](../outside.md)\n", encoding="utf-8")
        bad = json.loads(run("lint", skill, "--json"))
        assert bad["ok"] is False and any("escapes skill root" in item for item in bad["errors"])

        # Rebuild with a safe in-root link and check reproducibility and package contents.
        readme.write_text("# Notes\n\n[Skill](../SKILL.md)\n", encoding="utf-8")
        first = json.loads(run("package", skill, "--out", temp / "first.zip", "--json"))
        second = json.loads(run("package", skill, "--out", temp / "second.zip", "--json"))
        assert first["sha256"] == second["sha256"]
        assert first["sha256"] == hashlib.sha256((temp / "first.zip").read_bytes()).hexdigest()
        assert Path(first["checksum_file"]).is_file()
        with zipfile.ZipFile(temp / "first.zip") as archive:
            names = set(archive.namelist())
            assert "my-domain-skill/SKILL.md" in names
            assert "my-domain-skill/assets/templates/expert-module-template.md" in names
            assert "my-domain-skill/references/notes.md" in names
            assert all(item.date_time == (2026, 1, 1, 0, 0, 0) for item in archive.infolist())

        # New must not overwrite an existing directory.
        run("new", "my-domain-skill", "--dest", skill,
            "--description", "A focused domain skill for a test.", expect=2)

        # Credential-shaped files and symlinks are refused.
        (skill / ".env").write_text("TOKEN=never-package-this\n", encoding="utf-8")
        result = run("lint", skill, expect=1)
        assert "potential secret" in result or "potential secret" in result.lower()
    print("PASS skill authoring: scaffold, specialist lint, local-link safety, reproducible package")


if __name__ == "__main__":
    main()
