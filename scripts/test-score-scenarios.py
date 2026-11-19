#!/usr/bin/env python3
"""Offline self-tests for the judge helper (no live judge model required)."""
import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODULE = ROOT / "scripts" / "score-scenarios.py"


def load_module():
    spec = importlib.util.spec_from_file_location("score_scenarios", MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    mod = load_module()
    blinded = mod.blind_summary(
        "read /tmp/fixture-without/.opencode/skills/rcoder/SKILL.md and WITH.jsonl; "
        "without arm baseline; with arm treatment"
    )
    assert "fixture-with" not in blinded, blinded
    assert "WITH.jsonl" not in blinded, blinded
    assert "without arm" not in blinded, blinded
    assert "with arm" not in blinded, blinded
    assert "rcoder/SKILL.md" in blinded, blinded

    assert mod.parse_flags("[true,false,true]", 3) == [True, False, True]
    assert mod.parse_flags("noise [true,false] tail", 2) == [True, False]
    assert mod.parse_flags("[true,false,true]", 2) is None
    assert mod.parse_flags('["true",false]', 2) is None
    assert mod.parse_flags("no flags", 2) is None

    with tempfile.TemporaryDirectory(prefix="rcoder-judge-test-") as temporary:
        run_dir = Path(temporary)
        assert mod.judged_path(run_dir, "with", False) == run_dir / "judged" / "WITH.jsonl"
        assert mod.judged_path(run_dir, "without", False) == run_dir / "judged" / "WITHOUT.jsonl"
        assert mod.judged_path(run_dir, "with", True) == run_dir / "WITH.jsonl"

    print("PASS score-scenarios helpers: blinding, strict flag parsing, and non-destructive output paths")


if __name__ == "__main__":
    main()
