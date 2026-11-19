#!/usr/bin/env python3
"""Score RCoder trigger, specialist-selection, and behavioral evaluation runs.

A predictions file is JSON Lines: one object per line with an "id" matching
evals/triggers.json. Optional fields: "predicted_trigger" (bool),
"selected_specialists" (list of module names), and "scenario_scores" (map of
scenario id to a list of booleans matching that scenario's rubric length).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRIGGERS = ROOT / "evals" / "triggers.json"
SCENARIOS = ROOT / "evals" / "scenarios.json"
EXPECTATIONS = ROOT / "evals" / "routing-expectations.json"


def load_json(path: Path) -> dict | list:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_predictions(path: Path, valid_ids: set[str]) -> dict[str, dict]:
    predictions: dict[str, dict] = {}
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"{path}:{number}: invalid JSON: {error}") from error
            item_id = item.get("id")
            if not isinstance(item_id, str) or item_id not in valid_ids:
                raise ValueError(f"{path}:{number}: unknown or missing id: {item_id!r}")
            if item_id in predictions:
                raise ValueError(f"{path}:{number}: duplicate id: {item_id}")
            predictions[item_id] = item
    if not predictions:
        raise ValueError(f"{path}: no prediction records")
    return predictions


def ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


def score_triggers(triggers: list[dict], predictions: dict[str, dict]) -> dict:
    true_positive = false_positive = true_negative = false_negative = 0
    missing = []
    for trigger in triggers:
        item = predictions.get(trigger["id"])
        if item is None or "predicted_trigger" not in item:
            missing.append(trigger["id"])
            continue
        predicted = bool(item["predicted_trigger"])
        actual = trigger["should_trigger"] is True
        if predicted and actual:
            true_positive += 1
        elif predicted and not actual:
            false_positive += 1
        elif not predicted and actual:
            false_negative += 1
        else:
            true_negative += 1
    precision = ratio(true_positive, true_positive + false_positive)
    recall = ratio(true_positive, true_positive + false_negative)
    f1 = ratio(2 * precision * recall, precision + recall)
    accuracy = ratio(true_positive + true_negative, len(triggers))
    return {
        "tp": true_positive, "fp": false_positive,
        "tn": true_negative, "fn": false_negative,
        "precision": precision, "recall": recall, "f1": f1,
        "accuracy": accuracy, "missing_predictions": missing,
    }


def score_specialists(triggers: list[dict], predictions: dict[str, dict], expectations: dict) -> dict:
    matched = relevant = selected = 0
    exact_matches = 0
    scored = 0
    for trigger in triggers:
        item = predictions.get(trigger["id"])
        expected = set(expectations.get(trigger["id"], []))
        if item is None or "selected_specialists" not in item or not expected:
            continue
        actual = set(item["selected_specialists"])
        matched += len(expected & actual)
        relevant += len(expected)
        selected += len(actual)
        exact_matches += int(expected == actual)
        scored += 1
    return {
        "scored_prompts": scored,
        "precision": ratio(matched, selected),
        "recall": ratio(matched, relevant),
        "f1": ratio(2 * matched, selected + relevant),
        "exact_match_rate": ratio(exact_matches, scored),
    }


def score_scenarios(scenarios: list[dict], predictions: dict[str, dict]) -> dict:
    results = {}
    passed = total = 0
    for scenario in scenarios:
        item = predictions.get(scenario["id"])
        scores = item.get("scenario_scores", {}).get(scenario["id"]) if item else None
        if scores is None:
            results[scenario["id"]] = {"status": "NOT SCORED"}
            continue
        expected_length = len(scenario.get("rubric", []))
        if not isinstance(scores, list) or len(scores) != expected_length:
            raise ValueError(
                f"{scenario['id']}: expected {expected_length} rubric scores, got "
                f"{len(scores) if isinstance(scores, list) else type(scores).__name__}"
            )
        flags = [bool(value) for value in scores]
        scenario_pass = all(flags)
        passed += sum(flags)
        total += len(flags)
        results[scenario["id"]] = {
            "status": "PASS" if scenario_pass else "FAIL",
            "criteria_passed": sum(flags),
            "criteria_total": len(flags),
        }
    return {
        "scenarios_scored": sum(1 for value in results.values() if value["status"] != "NOT SCORED"),
        "scenarios_passed": sum(1 for value in results.values() if value["status"] == "PASS"),
        "criteria_pass_rate": ratio(passed, total),
        "scenarios": results,
    }


def deltas(current: dict, baseline: dict) -> dict:
    keys = ("precision", "recall", "f1", "accuracy")
    return {key: round(current[key] - baseline[key], 6) for key in keys if key in current and key in baseline}


def render(report: dict) -> str:
    triggers = report["triggers"]
    specialists = report["specialists"]
    scenarios = report["scenarios"]
    lines = [
        f"Triggers: TP={triggers['tp']} FP={triggers['fp']} TN={triggers['tn']} FN={triggers['fn']}",
        f"  precision={triggers['precision']} recall={triggers['recall']} f1={triggers['f1']} accuracy={triggers['accuracy']}",
        f"Specialists: scored={specialists['scored_prompts']} precision={specialists['precision']} "
        f"recall={specialists['recall']} f1={specialists['f1']} exact_match={specialists['exact_match_rate']}",
        f"Scenarios: passed={scenarios['scenarios_passed']}/{scenarios['scenarios_scored']} "
        f"criteria_pass_rate={scenarios['criteria_pass_rate']}",
    ]
    if report.get("missing_predictions"):
        lines.append(f"Missing trigger predictions: {len(report['missing_predictions'])}")
    if "ablation_delta" in report:
        lines.append("Ablation delta (with minus without): " + json.dumps(report["ablation_delta"], sort_keys=True))
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", required=True, type=Path, help="JSONL predictions for the RCoder run")
    parser.add_argument("--baseline", type=Path, help="Optional JSONL predictions for the without-RCoder run")
    parser.add_argument("--strict", action="store_true", help="Fail when any trigger prediction is missing")
    parser.add_argument("--json", action="store_true", help="Emit the full report as JSON")
    args = parser.parse_args()

    try:
        triggers = load_json(TRIGGERS)
        scenarios = load_json(SCENARIOS)
        expectations = load_json(EXPECTATIONS)["expectations"]
        trigger_ids = {item["id"] for item in triggers}
        scenario_ids = {item["id"] for item in scenarios}
        predictions = load_predictions(args.predictions, trigger_ids | scenario_ids)
        trigger_scores = score_triggers(triggers, predictions)
        report = {
            "predictions_file": str(args.predictions),
            "triggers": trigger_scores,
            "specialists": score_specialists(triggers, predictions, expectations),
            "scenarios": score_scenarios(scenarios, predictions),
            "missing_predictions": trigger_scores["missing_predictions"],
        }
        if args.baseline:
            baseline = load_predictions(args.baseline, trigger_ids | scenario_ids)
            baseline_report = score_triggers(triggers, baseline)
            report["baseline"] = baseline_report
            report["ablation_delta"] = deltas(report["triggers"], baseline_report)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render(report))
    if args.strict and report["missing_predictions"]:
        print("ERROR: strict mode requires every trigger prediction", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
