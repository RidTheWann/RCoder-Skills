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


def write_predictions(path, triggers, scenarios, expectations, flip=None, omit=(), scenario_ok=True):
    records = []
    for trigger in triggers:
        if trigger["id"] in omit:
            continue
        predicted = trigger["should_trigger"] is True
        if flip and trigger["id"] in flip:
            predicted = not predicted
        records.append({
            "id": trigger["id"],
            "predicted_trigger": predicted,
            "selected_specialists": list(expectations.get(trigger["id"], [])),
        })
    for scenario in scenarios:
        length = len(scenario.get("rubric", []))
        records.append({
            "id": scenario["id"],
            "scenario_scores": {scenario["id"]: [scenario_ok] * length},
        })
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
    assert len(triggers) == 42 and len(scenarios) >= 14
    assert set(expectations) == {item["id"] for item in triggers}

    with tempfile.TemporaryDirectory(prefix="rcoder-score-test-") as temporary:
        root = Path(temporary)
        perfect = root / "perfect.jsonl"
        mixed = root / "mixed.jsonl"
        wrong = root / "wrong.jsonl"
        malformed = root / "malformed.jsonl"
        bad_rubric = root / "bad-rubric.jsonl"
        unknown = root / "unknown.jsonl"
        partial = root / "partial.jsonl"

        write_predictions(perfect, triggers, scenarios, expectations)
        write_predictions(mixed, triggers, scenarios, expectations, flip={"trig-02", "trig-13"})
        write_predictions(wrong, triggers, scenarios, expectations,
                          flip={item["id"] for item in triggers}, scenario_ok=False)
        malformed.write_text("{not json}\n", encoding="utf-8")
        bad_rubric.write_text(json.dumps({"id": scenarios[0]["id"], "scenario_scores": {
            scenarios[0]["id"]: [True]}}) + "\n", encoding="utf-8")
        unknown.write_text(json.dumps({"id": "does-not-exist", "predicted_trigger": True}) + "\n", encoding="utf-8")
        write_predictions(partial, triggers, scenarios, expectations, omit={"trig-01"})

        result = run("--predictions", perfect, "--json", "--strict")
        assert result.returncode == 0, result.stderr
        report = json.loads(result.stdout)
        assert report["triggers"]["precision"] == 1.0
        assert report["triggers"]["recall"] == 1.0
        assert report["triggers"]["accuracy"] == 1.0
        assert report["specialists"]["f1"] == 1.0
        assert report["specialists"]["exact_match_rate"] == 1.0
        assert report["scenarios"]["scenarios_passed"] == len(scenarios)
        assert report["scenarios"]["criteria_pass_rate"] == 1.0

        result = run("--predictions", mixed, "--json")
        assert result.returncode == 0, result.stderr
        report = json.loads(result.stdout)
        assert report["triggers"]["tp"] == 23
        assert report["triggers"]["fp"] == 1
        assert report["triggers"]["fn"] == 1
        assert report["triggers"]["tn"] == 17
        assert report["triggers"]["precision"] == round(23 / 24, 6)
        assert report["triggers"]["recall"] == round(23 / 24, 6)
        assert report["triggers"]["accuracy"] == round(40 / 42, 6)

        result = run("--predictions", perfect, "--baseline", wrong, "--json")
        assert result.returncode == 0, result.stderr
        report = json.loads(result.stdout)
        assert report["baseline"]["precision"] == 0.0
        assert report["ablation_delta"]["precision"] == 1.0
        assert report["ablation_delta"]["accuracy"] == 1.0

        assert run("--predictions", malformed).returncode == 2
        assert run("--predictions", bad_rubric).returncode == 2
        assert run("--predictions", unknown).returncode == 2
        assert run("--predictions", partial, "--strict").returncode == 2

    print("PASS score-eval: perfect/mixed/ablation scoring and four rejection paths verified")


if __name__ == "__main__":
    main()
