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
    known = {path.stem for path in (ROOT / "skills" / "rcoder" / "references").glob("*.md")}
    helpers = {"verification", "rsaver", "rsaver-gate", "token-efficiency", "model-adaptation"}
    unexpected = next(iter(sorted(name for name in known - helpers if name not in set(expectations[positive]))))

    with tempfile.TemporaryDirectory(prefix="rcoder-objective-test-") as temporary:
        root = Path(temporary)
        predictions = root / "WITH.jsonl"
        output = root / "OBJECTIVE.jsonl"
        definitions = root / "definitions.json"
        malformed = root / "malformed.jsonl"
        semantic = root / "semantic.jsonl"
        semantic_output = root / "semantic-objective.jsonl"
        clean = root / "clean.jsonl"
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
        assert verified[negative] == [True, False, True, False, False, True, True], verified[negative]
        assert verified[scenario_id] == [True, False], verified[scenario_id]
        defined = json.loads(definitions.read_text())
        assert defined[positive] == ["prediction_shape", "specialists_are_known",
                                     "activation_has_specialists", "negative_not_activated",
                                     "negative_selection_empty", "non_helper_primary",
                                     "expected_specialist_overlap"]

        semantic_records = [
            {"id": positive, "predicted_trigger": True,
             "selected_specialists": ["verification", "rsaver"]},
            {"id": positive, "predicted_trigger": True,
             "selected_specialists": [unexpected]},
            {"id": negative, "predicted_trigger": False,
             "selected_specialists": [good_module]},
        ]
        semantic.write_text("\n".join(json.dumps(r) for r in semantic_records) + "\n", encoding="utf-8")
        result = run(VERIFIER, "--predictions", semantic, "--expectations", EXPECTATIONS,
                     "--output", semantic_output)
        assert result.returncode == 0, result.stderr
        semantic_flags = [r["objective_checks"][r["id"]]
                          for r in (json.loads(line) for line in semantic_output.read_text().splitlines() if line.strip())]
        assert semantic_flags[0][5] is False, semantic_flags[0]
        assert semantic_flags[1][1] is True and semantic_flags[1][6] is False, semantic_flags[1]
        assert semantic_flags[2][4] is False, semantic_flags[2]
        assert run(VERIFIER, "--predictions", semantic, "--expectations", EXPECTATIONS,
                   "--output", semantic_output, "--strict").returncode == 1
        clean.write_text(json.dumps({"id": positive, "predicted_trigger": True,
                                     "selected_specialists": [good_module]}) + "\n", encoding="utf-8")
        assert run(VERIFIER, "--predictions", clean, "--expectations", EXPECTATIONS,
                   "--output", semantic_output, "--strict").returncode == 0

        result = run(SCORER, "--predictions", predictions, "--objective", output, "--json")
        assert result.returncode == 0, result.stderr
        report = json.loads(result.stdout)
        assert report["objective_verification"]["items_scored"] == 3
        assert report["objective_verification"]["checks_total"] == 16
        assert report["objective_verification"]["checks_passed"] == 12
        assert report["objective_verification"]["pass_rate"] == 0.75

        assert run(VERIFIER, "--predictions", malformed, "--output", output).returncode == 2

    print("PASS objective verifier: trigger/case checks, routing semantics, strict mode, definitions, and scorer integration verified")


if __name__ == "__main__":
    main()
