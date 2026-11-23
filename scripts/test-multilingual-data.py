#!/usr/bin/env python3
"""Validate the separate multilingual routing research dataset; no model is invoked."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "evals" / "datasets" / "multilingual.triggers.json"
REFERENCES = ROOT / "skills" / "rcoder" / "references"


def main() -> int:
    cases = json.loads(DATA.read_text(encoding="utf-8"))
    modules = {path.stem for path in REFERENCES.glob("*.md")}
    ids = [case.get("id") for case in cases]
    assert len(cases) >= 12, f"expected at least 12 multilingual cases, found {len(cases)}"
    assert len(set(ids)) == len(ids), "duplicate multilingual case IDs"
    assert {case.get("language") for case in cases} >= {"ID", "EN", "MIXED_ID_EN"}
    assert sum(not case.get("expected_specialists") for case in cases) >= 3, "negative controls were lost"
    for case in cases:
        identifier = case.get("id")
        prompt = case.get("prompt", "")
        assert isinstance(prompt, str) and prompt.strip(), f"{identifier}: empty prompt"
        assert isinstance(case.get("identifier_integrity"), list), f"{identifier}: identifier_integrity must be a list"
        for token in case["identifier_integrity"]:
            assert token and token in prompt, f"{identifier}: identifier was translated or removed: {token!r}"
        for specialist in case.get("expected_specialists", []):
            assert specialist in modules, f"{identifier}: unknown specialist {specialist}"
    print(f"PASS multilingual dataset: {len(cases)} verbatim cases, 3 language modes, identifier checks, negative controls")
    print("NOTE: static fixture validation only; model routing accuracy is NOT VERIFIED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
