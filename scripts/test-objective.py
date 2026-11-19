#!/usr/bin/env python3
"""Self-tests for the deterministic objective verifier and its scorer integration."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERIFIER = ROOT / "scripts" / "verify-objective.py"
SCORER = ROOT / "scripts" / "score-eval.py"
EXPECTATIONS = ROOT / "evals" / "routing-expectations.json"


def run(script, *arguments):
    return subprocess.run(
        [sys.executable, str(script), *[str(a) for a in arguments]],
        text=True, capture_output=True, check=False, timeout=20,
    )


def main():
    expectations = json.loads(EXPECTATIONS.read_text(encoding="utf-8"))["expectations"]
    positive = next(key for key, value in expectations.items() if value)
    negative = next(key for key, value in expectations.items() if not value)
    scenario_id = json.loads((ROOT / "evals" / "scenarios.json").read_text())[0]["id"]
    good_module = expectations[positive][0]

    with tempfile.TemporaryDirectory(prefix="rcoder-objective-test-") as temporary:
        root = Path(temporary)
        predictions = root / "WITH.jsonl"
        output = root / "OBJECTIVE.jsonl"
        definitions = root / "definitions.json"
        malformed = root / "malformed.jsonl"
        records = [
            {"id": positive, "predicted_trigger": True, "selected_specialists": [good_module]},
            {"id": negative, "predicted_trigger": True, "selected_specialists": ["invented-module"]},
            {"id": scenario_id, "scenario_scores": {}},
        ]
        predictions.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
        malformed.write_text("{bad\n", encoding="utf-8")

        result = run(VERIFIER, "--predictions", predictions, "--expectations", EXPECTATIONS,
                     "--output", output, "--definitions", definitions)
        assert result.returncode == 0, result.stderr
        verified = {r["id"]: r["objective_checks"][r["id"]]
                    for r in (json.loads(line) for line in output.read_text().splitlines() if line.strip())}
        assert all(verified[positive]), verified[positive]
        assert verified[negative] == [True, False, True, False], verified[negative]
        assert verified[scenario_id] == [True, False], verified[scenario_id]
        defined = json.loads(definitions.read_text())
        assert defined[positive] == ["prediction_shape", "specialists_are_known",
                                     "activation_has_specialists", "negative_not_activated"]

        result = run(SCORER, "--predictions", predictions, "--objective", output, "--json")
        assert result.returncode == 0, result.stderr
        report = json.loads(result.stdout)
        assert report["objective_verification"]["items_scored"] == 3
        assert report["objective_verification"]["checks_total"] == 10
        assert report["objective_verification"]["checks_passed"] == 7
        assert report["objective_verification"]["pass_rate"] == 0.7

        assert run(VERIFIER, "--predictions", malformed, "--output", output).returncode == 2

    print("PASS objective verifier: trigger/case checks, definitions, and scorer integration verified")


if __name__ == "__main__":
    main()
