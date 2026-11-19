#!/usr/bin/env python3
"""Deterministic tests for RSaver's reduction, evidence preservation, and recovery."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RSAVER = ROOT / "scripts" / "rsaver.py"


def run(*arguments, stdin_text=None):
    return subprocess.run(
        [sys.executable, str(RSAVER), *[str(arg) for arg in arguments]],
        text=True, capture_output=True, check=False, timeout=20, input=stdin_text,
    )


def run_json(*arguments, stdin_text=None):
    result = run(*arguments, stdin_text=stdin_text)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def build_fixture(path: Path) -> dict:
    lines = ["# Tool output fixture"]
    lines.extend(f"INFO noise iteration {index} with repeated filler tokens" for index in range(80))
    critical = {
        82: "ERROR: parser failed at offset 42",
        83: "sha256=abcdef0123456789abcdef0123456789abcdef01",
        84: "See https://example.com/docs for reference",
        85: "Status: NOT VERIFIED",
    }
    lines.extend(critical[index] for index in sorted(critical))
    lines.append("done")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return critical


def main():
    with tempfile.TemporaryDirectory(prefix="rcoder-rsaver-test-") as temporary:
        root = Path(temporary)
        fixture = root / "log.txt"
        critical = build_fixture(fixture)
        manifest_path = root / "manifest.json"

        canonical = ROOT / "skills" / "rcoder" / "scripts" / "rsaver.py"
        assert canonical.is_file()
        direct = subprocess.run([sys.executable, str(canonical), "--version"],
                                text=True, capture_output=True, check=True, timeout=20)
        assert "RSaver 1.4.0" in direct.stdout
        version = run("--version")
        assert version.returncode == 0 and "RSaver 1.4.0" in version.stdout

        measured = run_json("measure", str(fixture), "--json")
        assert measured["total_estimate"] > 0
        assert measured["files"][0]["lines"] == 86
        assert measured["files"][0]["estimate"] == measured["total_estimate"]

        compacted = run_json("compact", str(fixture), "--max-lines", "20", "--json")
        reduced = compacted["compacted"]
        original_lines = fixture.read_text(encoding="utf-8").splitlines()
        assert compacted["estimate"]["saved_percent"] >= 40.0
        assert compacted["estimate"]["compact_estimate"] < compacted["estimate"]["original_estimate"]
        assert sorted(compacted["critical_lines"]) == sorted(critical)
        assert compacted["omitted_ranges"]
        assert not compacted["budget_exceeded_by_critical"]
        for text in critical.values():
            assert text in reduced, text
        assert all(line in original_lines for line in reduced.splitlines())

        written = run("compact", str(fixture), "--max-lines", "20", "--manifest", str(manifest_path), "--verify")
        assert written.returncode == 0, written.stderr
        verified = run("verify", "--manifest", str(manifest_path))
        assert verified.returncode == 0 and "RSAVER VERIFY PASS" in verified.stdout

        range_start, range_end = compacted["omitted_ranges"][0]
        recovered = run_json("recover", "--file", str(fixture), "--range", f"{range_start}:{range_end}", "--json")
        assert recovered["text"].splitlines() == original_lines[range_start - 1:range_end]

        selected = run_json("select", str(fixture), "--match", "ERROR|sha256", "--context", "1",
                            "--max-lines", "10", "--json")
        assert selected["critical_lines"] == [82, 83]
        assert len(selected["selected_text"].splitlines()) <= 10
        assert critical[84] in selected["selected_text"]

        small = run_json("dedupe", "-", "--json", stdin_text="A\nA\nERROR: boom\nA\n")
        assert small["stats"]["saved_estimate"] >= 0
        assert "ERROR: boom" in small["deduped_text"]

        repeated = root / "repeated.txt"
        repeated.write_text("\n".join(["INFO worker heartbeat ok"] * 40 + ["ERROR: boom"]) + "\n", encoding="utf-8")
        deduped = run_json("dedupe", str(repeated), "--json")
        assert deduped["stats"]["saved_estimate"] > 0
        assert "original lines 1-40" in deduped["deduped_text"]
        assert "ERROR: boom" in deduped["deduped_text"]

        tampered = root / "tampered.txt"
        tampered.write_text(fixture.read_text(encoding="utf-8") + "ERROR: new evidence\n", encoding="utf-8")
        failed = run("verify", "--manifest", str(manifest_path), "--file", str(tampered))
        assert failed.returncode == 1 and "RSAVER VERIFY FAIL" in failed.stderr

        assert run("compact", str(fixture), "--critical", "[", "--json").returncode == 2
        assert run("recover", "--file", str(fixture), "--range", "999:1000").returncode == 2
        assert run("measure", str(root / "missing.txt")).returncode == 2

    print("PASS rsaver: bounded reduction, verbatim evidence, recoverability, verification, and dedupe economics")


if __name__ == "__main__":
    main()
