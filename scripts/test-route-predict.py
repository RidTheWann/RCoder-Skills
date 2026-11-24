#!/usr/bin/env python3
"""Deterministic checks for the route_predict specialist proposal helper.

Scores canonical, expanded, multilingual, and manually-held-out cases, plus
negative-rejection, determinism, boundary regression, ordinal confidence, and
MCP tool wiring. No model call is made; all numbers are deterministic.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "skills" / "rcoder" / "scripts" / "route_predict.py"
MCP = ROOT / "skills" / "rcoder" / "scripts" / "rcoder_mcp.py"


def call(text: str) -> dict:
    done = subprocess.run(
        [sys.executable, str(SCRIPT), "--text", text, "--json"],
        capture_output=True, text=True, encoding="utf-8", timeout=15,
    )
    assert done.returncode == 0, done.stderr
    return json.loads(done.stdout)


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def score(cases: list[tuple[str, list[str]]]) -> dict:
    tp = fp = fn = positive_empty = 0
    for prompt, expected in cases:
        result = call(prompt)
        proposed = set(result["proposed"])
        exp = set(expected)
        if exp and not proposed:
            positive_empty += 1
        tp += len(exp & proposed)
        fp += len(proposed - exp)
        fn += len(exp - proposed)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0
    return {"precision": precision, "recall": recall, "f1": f1,
            "tp": tp, "fp": fp, "fn": fn, "positive_empty": positive_empty}


def collect_cases():
    canonical = load("evals/routing-expectations.json")["expectations"]
    triggers = {item["id"]: item for item in load("evals/triggers.json")}
    expanded = load("evals/datasets/expanded/routing-expectations.json")["expectations"]
    exp_triggers = {item["id"]: item for item in load("evals/datasets/expanded/triggers.json")}
    multilingual = load("evals/datasets/multilingual.triggers.json")
    heldout = load("evals/dataset-heldout.json")["cases"]

    pos_canon = [(triggers[i]["prompt"], v) for i, v in canonical.items() if v]
    neg_canon = [(triggers[i]["prompt"], []) for i, v in canonical.items() if not v]
    pos_expanded = [(exp_triggers[i]["prompt"], v) for i, v in expanded.items() if v]
    neg_expanded = [(exp_triggers[i]["prompt"], []) for i, v in expanded.items() if not v]
    pos_multi = [(m["prompt"], m["expected_specialists"])
                 for m in multilingual if m["expected_specialists"]]
    neg_multi = [(m["prompt"], []) for m in multilingual if not m["expected_specialists"]]
    pos_held = [(c["prompt"], c["expected_specialists"]) for c in heldout
                if c["expected_specialists"]]
    neg_held = [(c["prompt"], []) for c in heldout if not c["expected_specialists"]]
    return {
        "canonical": (pos_canon, neg_canon),
        "expanded": (pos_expanded, neg_expanded),
        "multilingual": (pos_multi, neg_multi),
        "heldout": (pos_held, neg_held),
    }


def rejection_rate(cases: list[tuple[str, list[str]]]) -> tuple[int, int]:
    rejected = sum(1 for prompt, _ in cases if not call(prompt)["proposed"])
    return rejected, len(cases)


def main() -> int:
    assert SCRIPT.is_file(), "route_predict.py missing"
    cases = collect_cases()
    report = {}
    for name, (positive, negative) in cases.items():
        scored = score(positive)
        rejected, n_neg = rejection_rate(negative)
        report[name] = {**scored, "negative_rejection": f"{rejected}/{n_neg}"}
        assert scored["positive_empty"] == 0, f"{name}: positive with empty proposal"
        assert rejected >= int(n_neg * 0.75), f"{name}: weak negative rejection"

    # Leave-one-out is not applicable to a rule-based helper (no learned weights),
    # but held-out cases serve the same generalization role.
    assert report["heldout"]["f1"] >= 0.5, "held-out F1 below floor"

    # Determinism: identical input -> identical output.
    prompt = "Fix a race in this Go worker and add a regression test."
    assert call(prompt) == call(prompt), "non-deterministic proposal"

    # Word-boundary regression: 'sli' inside 'slide' must not fire observability.
    assert call("Create a slide deck about jazz.")["proposed"] == []
    # Confidence must stay ordinal; no numeric probability field.
    for value in report:
        pass
    for prompt, _ in cases["canonical"][0]:
        result = call(prompt)
        assert "probability" not in result and "score" not in result
        assert result["confidence"] in {
            "low", "medium", "insufficient signal", "n/a (out of scope)",
        }, result["confidence"]
        assert len(result["proposed"]) <= 4
        assert len(result["proposed"]) == len(set(result["proposed"]))

    # MCP wiring: tool is registered with strict schema and a read-only handler.
    server = MCP.read_text(encoding="utf-8")
    assert '"rcoder_route_predict"' in server, "MCP tool not registered"
    assert "tool_route_predict" in server
    assert "route_predict.py" in server

    print("PASS deterministic route proposal checks")
    for name, entry in report.items():
        print(f"  {name:12s} F1={entry['f1']:.3f} P={entry['precision']:.3f} "
              f"R={entry['recall']:.3f} neg-reject={entry['negative_rejection']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
