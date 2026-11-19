#!/usr/bin/env python3
"""Self-tests for the deterministic evaluation scorer."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCORER = ROOT / "scripts" / "score-eval.py"
TRIGGERS = ROOT / "evals" / "triggers.json"
SCENARIOS = ROOT / "evals" / "scenarios.json"
EXPECTATIONS = ROOT / "evals" / "routing-expectations.json"


def write_predictions(path, triggers, scenarios, expectations, flip=None, omit=(), scenario_ok=True,
                      specialist_shift=None, invalid=(), objective=None):
    records = []
    for trigger in triggers:
        if trigger["id"] in omit:
            continue
        predicted = trigger["should_trigger"] is True
        if flip and trigger["id"] in flip:
            predicted = not predicted
        specialists = list(expectations.get(trigger["id"], []))
        if specialist_shift and trigger["id"] in specialist_shift:
            add, drop = specialist_shift[trigger["id"]]
            specialists = [name for name in specialists if name not in drop] + list(add)
        record = {
            "id": trigger["id"],
            "predicted_trigger": predicted,
            "selected_specialists": specialists,
        }
        if trigger["id"] in invalid:
            record["valid"] = False
        records.append(record)
    for scenario in scenarios:
        length = len(scenario.get("rubric", []))
        record = {
            "id": scenario["id"],
            "scenario_scores": {scenario["id"]: [scenario_ok] * length},
        }
        if objective and scenario["id"] in objective:
            record["objective_checks"] = {scenario["id"]: objective[scenario["id"]]}
        records.append(record)
    path.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")


def run(*arguments):
    return subprocess.run(
        [sys.executable, str(SCORER), *[str(arg) for arg in arguments]],
        text=True, capture_output=True, check=False, timeout=20,
    )


def main():
    triggers = json.loads(TRIGGERS.read_text(encoding="utf-8"))
    scenarios = json.loads(SCENARIOS.read_text(encoding="utf-8"))
    expectations = json.loads(EXPECTATIONS.read_text(encoding="utf-8"))["expectations"]
    positives = [item for item in triggers if item["should_trigger"] is True]
    negatives = [item for item in triggers if item["should_trigger"] is not True]
    assert len(triggers) >= 42 and len(scenarios) >= 14
    assert set(expectations) == {item["id"] for item in triggers}
    assert positives and negatives
    expanded = ROOT / "evals" / "datasets" / "expanded"
    exp_triggers = json.loads((expanded / "triggers.json").read_text(encoding="utf-8"))
    exp_scenarios = json.loads((expanded / "scenarios.json").read_text(encoding="utf-8"))
    exp_expectations = json.loads((expanded / "routing-expectations.json").read_text(encoding="utf-8"))["expectations"]

    with tempfile.TemporaryDirectory(prefix="rcoder-score-test-") as temporary:
        root = Path(temporary)
        perfect = root / "perfect.jsonl"
        mixed = root / "mixed.jsonl"
        wrong = root / "wrong.jsonl"
        malformed = root / "malformed.jsonl"
        bad_rubric = root / "bad-rubric.jsonl"
        unknown = root / "unknown.jsonl"
        partial = root / "partial.jsonl"
        invalid_file = root / "invalid.jsonl"
        shifted = root / "shifted.jsonl"
        objective_file = root / "objective.jsonl"
        bad_objective = root / "bad-objective.jsonl"
        duplicate = root / "duplicate.jsonl"
        empty = root / "empty.jsonl"

        write_predictions(perfect, triggers, scenarios, expectations)
        write_predictions(mixed, triggers, scenarios, expectations, flip={"trig-02", "trig-13"})
        write_predictions(wrong, triggers, scenarios, expectations,
                          flip={item["id"] for item in triggers}, scenario_ok=False)
        write_predictions(partial, triggers, scenarios, expectations, omit={"trig-01"})
        write_predictions(invalid_file, triggers, scenarios, expectations, invalid={"trig-02"})
        first_shift = positives[0]["id"]
        write_predictions(shifted, triggers, scenarios, expectations,
                          specialist_shift={first_shift: (["invented-module"], [])})

        objective_scenario = next((s for s in scenarios if len(s.get("rubric", [])) >= 4), None)
        assert objective_scenario is not None
        obj_length = len(objective_scenario["rubric"])
        obj_flags = [True] * (obj_length - 1) + [False]
        write_predictions(objective_file, triggers, scenarios, expectations,
                          objective={objective_scenario["id"]: obj_flags})
        bad_flags = [True] * (obj_length - 1) + ["false"]
        write_predictions(bad_objective, triggers, scenarios, expectations,
                          objective={objective_scenario["id"]: bad_flags})

        malformed.write_text("{not json}\n", encoding="utf-8")
        bad_rubric.write_text(json.dumps({"id": scenarios[0]["id"], "scenario_scores": {
            scenarios[0]["id"]: [True]}}) + "\n", encoding="utf-8")
        unknown.write_text(json.dumps({"id": "does-not-exist", "predicted_trigger": True}) + "\n", encoding="utf-8")
        duplicate.write_text(
            json.dumps({"id": triggers[0]["id"], "predicted_trigger": True}) + "\n" +
            json.dumps({"id": triggers[0]["id"], "predicted_trigger": False}) + "\n",
            encoding="utf-8",
        )
        empty.write_text("\n", encoding="utf-8")

        result = run("--predictions", perfect, "--json", "--strict")
        assert result.returncode == 0, result.stderr
        report = json.loads(result.stdout)
        assert report["triggers"]["precision"] == 1.0
        assert report["triggers"]["recall"] == 1.0
        assert report["triggers"]["f1"] == 1.0
        assert report["triggers"]["accuracy"] == 1.0
        assert report["triggers"]["false_positive_rate"] == 0.0
        assert report["triggers"]["false_negative_rate"] == 0.0
        assert report["specialists"]["f1"] == 1.0
        assert report["specialists"]["exact_match_rate"] == 1.0
        assert report["specialists"]["negative_fp_activation_rate"] == 0.0
        assert report["specialists"]["positive_empty_activation_rate"] == 0.0
        assert "per_specialist" in report["specialists"]
        assert report["negative_rejection"]["rejection_rate"] == 1.0
        assert report["negative_rejection"]["false_activations"] == []
        assert report["objective_checks"]["scored"] == 0
        assert "cross_domain" in report and "ambiguous_scenarios" in report
        assert report["scenarios"]["scenarios_passed"] == len(scenarios)
        assert report["scenarios"]["criteria_pass_rate"] == 1.0

        result = run("--predictions", mixed, "--json")
        assert result.returncode == 0, result.stderr
        report = json.loads(result.stdout)
        expected_tp = len(positives) - 1
        expected_tn = len(negatives) - 1
        assert report["triggers"]["tp"] == expected_tp
        assert report["triggers"]["fp"] == 1
        assert report["triggers"]["fn"] == 1
        assert report["triggers"]["tn"] == expected_tn
        assert report["triggers"]["precision"] == round(expected_tp / (expected_tp + 1), 6)
        assert report["triggers"]["accuracy"] == round((expected_tp + expected_tn) / len(triggers), 6)
        assert report["triggers"]["false_positive_rate"] == round(1 / len(negatives), 6)
        assert report["triggers"]["false_negative_rate"] == round(1 / len(positives), 6)
        assert report["negative_rejection"]["false_activations"] == ["trig-13"]

        result = run("--predictions", invalid_file, "--json")
        assert result.returncode == 0, result.stderr
        report = json.loads(result.stdout)
        assert report["excluded_invalid"] == ["trig-02"]
        assert report["triggers"]["tp"] == len(positives) - 1
        result = run("--predictions", invalid_file, "--include-invalid", "--json")
        assert json.loads(result.stdout)["triggers"]["tp"] == len(positives)

        result = run("--predictions", shifted, "--json")
        assert result.returncode == 0, result.stderr
        report = json.loads(result.stdout)
        assert report["specialists"]["per_specialist"]["invented-module"]["fp"] == 1
        assert report["specialists"]["f1"] < 1.0

        result = run("--predictions", objective_file, "--json")
        assert result.returncode == 0, result.stderr
        report = json.loads(result.stdout)
        assert report["objective_checks"]["criteria_pass_rate"] == round((obj_length - 1) / obj_length, 6)
        assert report["objective_checks"]["passed"] == 0

        expanded_predictions = root / "expanded.jsonl"
        write_predictions(expanded_predictions, exp_triggers, exp_scenarios, exp_expectations)
        result = run("--predictions", expanded_predictions, "--dataset", expanded, "--json", "--strict")
        assert result.returncode == 0, result.stderr
        report = json.loads(result.stdout)
        assert report["triggers"]["f1"] == 1.0
        assert report["specialists"]["exact_match_rate"] == 1.0
        assert report["scenarios"]["scenarios_passed"] == len(exp_scenarios)
        assert report["specialists"]["negative_fp_activation_rate"] == 0.0

        result = run("--predictions", perfect, "--baseline", wrong, "--json")
        assert result.returncode == 0, result.stderr
        report = json.loads(result.stdout)
        assert report["baseline"]["precision"] == 0.0
        assert report["ablation_delta"]["precision"] == 1.0
        assert report["ablation_delta"]["accuracy"] == 1.0

        assert run("--predictions", malformed).returncode == 2
        assert run("--predictions", bad_rubric).returncode == 2
        assert run("--predictions", bad_objective).returncode == 2
        assert run("--predictions", unknown).returncode == 2
        assert run("--predictions", partial, "--strict").returncode == 2
        assert run("--predictions", duplicate).returncode == 2
        assert run("--predictions", empty).returncode == 2

    print("PASS score-eval: confusion, FP/FN rates, negative rejection, objective checks, "
          "invalid exclusion, and ten rejection paths verified")


if __name__ == "__main__":
    main()
