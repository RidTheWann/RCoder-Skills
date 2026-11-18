#!/usr/bin/env python3
"""Regression tests for the read-only, bounded context snapshot helper."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HELPER = ROOT / "skills" / "rcoder" / "scripts" / "context_snapshot.py"

def main():
    with tempfile.TemporaryDirectory(prefix="rcoder-context-test-") as temporary:
        root = Path(temporary)
        (root / "README.md").write_text("# Fixture\n", encoding="utf-8")
        (root / "package.json").write_text('{"private":true}\n', encoding="utf-8")
        (root / "src").mkdir()
        (root / "src" / "main.py").write_text("SECRET_FIXTURE_MUST_NOT_BE_PRINTED\n", encoding="utf-8")
        (root / "node_modules").mkdir()
        (root / "node_modules" / "ignored.js").write_text("ignored", encoding="utf-8")
        try:
            (root / "linked-secret").symlink_to(root / "src" / "main.py")
        except (OSError, NotImplementedError):
            pass
        result = subprocess.run(
            [sys.executable, str(HELPER), str(root), "--json", "--max-paths", "20", "--max-depth", "3"],
            text=True, capture_output=True, check=True, timeout=10,
        )
        data = json.loads(result.stdout)
        assert data["source_contents_included"] is False
        assert "README.md" in data["key_files"]
        assert "package.json" in data["key_files"]
        assert "src/main.py" in data["file_paths"]
        assert not any("node_modules" in item for item in data["file_paths"])
        assert "SECRET_FIXTURE_MUST_NOT_BE_PRINTED" not in result.stdout
        assert "linked-secret" not in data["file_paths"]
        assert "ESTIMATED TOKENS:" in result.stderr
        bounded_root = root / "bounded"
        bounded_root.mkdir()
        for index in range(25):
            (bounded_root / f"file-{index:02d}.txt").write_text("fixture\n", encoding="utf-8")
        bounded = subprocess.run(
            [sys.executable, str(HELPER), str(bounded_root), "--json", "--max-paths", "10", "--max-depth", "3"],
            text=True, capture_output=True, check=True, timeout=10,
        )
        bounded_data = json.loads(bounded.stdout)
        assert len(bounded_data["file_paths"]) <= 10
        assert bounded_data["truncated"] is True
        assert bounded_data["source_contents_included"] is False
        assert "fixture" not in bounded.stdout
        print("PASS context snapshot: bounded metadata-only output; dependency trees, symlinks, and path limits enforced")

if __name__ == "__main__":
    main()
