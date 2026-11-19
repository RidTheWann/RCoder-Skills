#!/usr/bin/env python3
"""Score RCoder trigger, specialist-selection, and behavioral evaluation runs.

A predictions file is JSON Lines: one object per line with an "id" matching
evals/triggers.json. Optional fields: "predicted_trigger" (bool),
"selected_specialists" (list of module names), "scenario_scores" (map of
scenario id to a list of booleans), "objective_checks" (same shape, produced by
a deterministic verifier that does NOT use the tested model as judge), and
"valid" (bool; a false value excludes the record unless --include-invalid is set).

All metrics emitted here are deterministic functions of the retained artifacts.
No metric in this scorer invokes the tested model as a judge.
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


def excluded_invalid_ids(predictions: dict[str, dict], invalid_cases: dict | None) -> list[str]:
    ids = [key for key, item in predictions.items() if item.get("valid") is False]
    if invalid_cases:
        for value in invalid_cases.values():
            if isinstance(value, list):
                ids.extend(str(item_id) for item_id in value if str(item_id) in predictions)
    return sorted(set(ids))


def without_invalid(predictions: dict[str, dict], excluded: list[str]) -> dict[str, dict]:
    excluded_set = set(excluded)
    return {key: value for key, value in predictions.items() if key not in excluded_set}


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
        predicted = item["predicted_trigger"] is True
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
    f1 = ratio(2 * true_positive, 2 * true_positive + false_positive + false_negative)
    accuracy = ratio(true_positive + true_negative, len(triggers))
    return {
        "tp": true_positive, "fp": false_positive,
        "tn": true_negative, "fn": false_negative,
        "precision": precision, "recall": recall, "f1": f1,
        "accuracy": accuracy,
        "false_positive_rate": ratio(false_positive, false_positive + true_negative),
        "false_negative_rate": ratio(false_negative, false_negative + true_positive),
        "missing_predictions": missing,
    }


def score_specialists(triggers: list[dict], predictions: dict[str, dict], expectations: dict) -> dict:
    matched = relevant = selected = 0
    exact_matches = 0
    scored = 0
    per_specialist: dict[str, dict] = {}
    negative_triggers = 0
    negative_false_activations = 0
    positive_triggers = 0
    positive_empty = 0
    for trigger in triggers:
        trigger_id = trigger["id"]
        item = predictions.get(trigger_id)
        expected = set(expectations.get(trigger_id, []))
        actual = set(item.get("selected_specialists", [])) if item else set()
        is_positive = trigger["should_trigger"] is True
        if not is_positive:
            negative_triggers += 1
            if actual:
                negative_false_activations += 1
        if expected:
            if is_positive:
                positive_triggers += 1
                if not actual:
                    positive_empty += 1
            if item is None or "selected_specialists" not in item:
                continue
            matched += len(expected & actual)
            relevant += len(expected)
            selected += len(actual)
            exact_matches += int(expected == actual)
            scored += 1
            for name in expected & actual:
                entry = per_specialist.setdefault(name, {"tp": 0, "fp": 0, "fn": 0})
                entry["tp"] += 1
            for name in actual - expected:
                entry = per_specialist.setdefault(name, {"tp": 0, "fp": 0, "fn": 0})
                entry["fp"] += 1
            for name in expected - actual:
                entry = per_specialist.setdefault(name, {"tp": 0, "fp": 0, "fn": 0})
                entry["fn"] += 1
    return {
        "scored_prompts": scored,
        "precision": ratio(matched, selected),
        "recall": ratio(matched, relevant),
        "f1": ratio(2 * matched, selected + relevant),
        "exact_match_rate": ratio(exact_matches, scored),
        "per_specialist": dict(sorted(per_specialist.items())),
        "negative_fp_activation_rate": ratio(negative_false_activations, negative_triggers),
        "negative_fp_activations": negative_false_activations,
        "negative_prompt_count": negative_triggers,
        "positive_empty_activation_rate": ratio(positive_empty, positive_triggers),
        "positive_empty_activations": positive_empty,
        "positive_prompt_count": positive_triggers,
    }


def score_flag_map(items: list[dict], predictions: dict[str, dict], field: str) -> dict:
    results = {}
    passed = total = 0
    for item in items:
        entry = predictions.get(item["id"])
        scores = entry.get(field, {}).get(item["id"]) if entry else None
        if scores is None:
            results[item["id"]] = {"status": "NOT SCORED"}
            continue
        expected_length = len(item.get("rubric", []))
        if not isinstance(scores, list) or len(scores) != expected_length:
            raise ValueError(
                f"{item['id']}: expected {expected_length} {field} flags, got "
                f"{len(scores) if isinstance(scores, list) else type(scores).__name__}"
            )
        if not all(isinstance(value, bool) for value in scores):
            raise ValueError(f"{item['id']}: {field} flags must be booleans")
        item_pass = all(scores)
        passed += sum(scores)
        total += len(scores)
        results[item["id"]] = {
            "status": "PASS" if item_pass else "FAIL",
            "criteria_passed": sum(scores),
            "criteria_total": len(scores),
        }
    return {
        "scored": sum(1 for value in results.values() if value["status"] != "NOT SCORED"),
        "passed": sum(1 for value in results.values() if value["status"] == "PASS"),
        "criteria_pass_rate": ratio(passed, total),
        "items": results,
    }


def score_scenarios(scenarios: list[dict], predictions: dict[str, dict], field: str = "scenario_scores") -> dict:
    result = score_flag_map(scenarios, predictions, field)
    return {
        "scenarios_scored": result["scored"],
        "scenarios_passed": result["passed"],
        "criteria_pass_rate": result["criteria_pass_rate"],
        "scenarios": result["items"],
    }


def score_negative_rejection(triggers: list[dict], predictions: dict[str, dict]) -> dict:
    negatives = [trigger for trigger in triggers if trigger["should_trigger"] is not True]
    false_activations = []
    rejected = 0
    for trigger in negatives:
        item = predictions.get(trigger["id"])
        if item is not None and item.get("predicted_trigger") is True:
            false_activations.append(trigger["id"])
        else:
            rejected += 1
    return {
        "negative_prompts": len(negatives),
        "rejected": rejected,
        "false_activations": false_activations,
        "rejection_rate": ratio(rejected, len(negatives)),
    }


def score_objective_file(path: Path) -> dict:
    """Score a deterministic verifier report (JSONL) without any model judge."""
    items = {}
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"{path}:{number}: invalid JSON: {error}") from error
            item_id = record.get("id")
            flags = record.get("objective_checks", {}).get(item_id) if isinstance(item_id, str) else None
            if not isinstance(item_id, str) or not isinstance(flags, list) or not all(isinstance(f, bool) for f in flags):
                raise ValueError(f"{path}:{number}: expected a boolean objective_checks list keyed by id")
            if item_id in items:
                raise ValueError(f"{path}:{number}: duplicate id: {item_id}")
            items[item_id] = flags
    if not items:
        raise ValueError(f"{path}: no objective check records")
    checks_passed = sum(sum(flags) for flags in items.values())
    checks_total = sum(len(flags) for flags in items.values())
    return {
        "items_scored": len(items),
        "items_passed": sum(1 for flags in items.values() if all(flags)),
        "checks_passed": checks_passed,
        "checks_total": checks_total,
        "pass_rate": ratio(checks_passed, checks_total),
        "items": {key: {"passed": sum(flags), "total": len(flags)} for key, flags in sorted(items.items())},
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
        f"  fp_rate={triggers['false_positive_rate']} fn_rate={triggers['false_negative_rate']}",
        f"Specialists: scored={specialists['scored_prompts']} precision={specialists['precision']} "
        f"recall={specialists['recall']} f1={specialists['f1']} exact_match={specialists['exact_match_rate']}",
        f"  negative_fp_rate={specialists['negative_fp_activation_rate']} "
        f"positive_empty_rate={specialists['positive_empty_activation_rate']}",
        f"Scenarios: passed={scenarios['scenarios_passed']}/{scenarios['scenarios_scored']} "
        f"criteria_pass_rate={scenarios['criteria_pass_rate']}",
        f"Objective checks: scored={report['objective_checks']['scored']} "
        f"passed={report['objective_checks']['passed']} "
        f"criteria_pass_rate={report['objective_checks']['criteria_pass_rate']}",
        f"Negative rejection: {report['negative_rejection']['rejection_rate']} "
        f"({report['negative_rejection']['rejected']}/{report['negative_rejection']['negative_prompts']})",
    ]
    if report.get("excluded_invalid"):
        lines.append(f"Excluded invalid cases: {len(report['excluded_invalid'])}")
    if report.get("missing_predictions"):
        lines.append(f"Missing trigger predictions: {len(report['missing_predictions'])}")
    if "ablation_delta" in report:
        lines.append("Ablation delta (with minus without): " + json.dumps(report["ablation_delta"], sort_keys=True))
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, help="Optional directory with triggers.json, scenarios.json, routing-expectations.json")
    parser.add_argument("--predictions", required=True, type=Path, help="JSONL predictions for the RCoder run")
    parser.add_argument("--baseline", type=Path, help="Optional JSONL predictions for the without-RCoder run")
    parser.add_argument("--invalid-cases", type=Path, help="Optional JSON map of invalid case IDs (e.g. invalid-cases.json)")
    parser.add_argument("--objective", type=Path, help="Optional deterministic verifier report (JSONL) to score as an independent evidence layer")
    parser.add_argument("--include-invalid", action="store_true", help="Score records explicitly marked invalid")
    parser.add_argument("--strict", action="store_true", help="Fail when any trigger prediction is missing")
    parser.add_argument("--json", action="store_true", help="Emit the full report as JSON")
    args = parser.parse_args()

    try:
        dataset = args.dataset or ROOT / "evals"
        triggers = load_json(dataset / "triggers.json")
        scenarios = load_json(dataset / "scenarios.json")
        expectations = load_json(dataset / "routing-expectations.json")["expectations"]
        trigger_ids = {item["id"] for item in triggers}
        scenario_ids = {item["id"] for item in scenarios}
        invalid_cases = load_json(args.invalid_cases) if args.invalid_cases else None
        raw_predictions = load_predictions(args.predictions, trigger_ids | scenario_ids)
        excluded = [] if args.include_invalid else excluded_invalid_ids(raw_predictions, invalid_cases)
        predictions = without_invalid(raw_predictions, excluded)
        trigger_scores = score_triggers(triggers, predictions)
        cross_domain_triggers = [
            trigger for trigger in triggers if "/" in str(trigger.get("category", ""))
        ]
        ambiguous_scenarios = [
            scenario for scenario in scenarios if "ambiguous" in scenario["id"]
        ]
        report = {
            "predictions_file": str(args.predictions),
            "excluded_invalid": excluded,
            "triggers": trigger_scores,
            "specialists": score_specialists(triggers, predictions, expectations),
            "scenarios": score_scenarios(scenarios, predictions),
            "negative_rejection": score_negative_rejection(triggers, predictions),
            "objective_checks": score_flag_map(scenarios, predictions, "objective_checks"),
            "objective_verification": score_objective_file(args.objective) if args.objective else None,
            "cross_domain": score_specialists(cross_domain_triggers, predictions, expectations),
            "ambiguous_scenarios": score_flag_map(ambiguous_scenarios, predictions, "scenario_scores"),
            "missing_predictions": trigger_scores["missing_predictions"],
        }
        if args.baseline:
            raw_baseline = load_predictions(args.baseline, trigger_ids | scenario_ids)
            baseline_excluded = [] if args.include_invalid else excluded_invalid_ids(raw_baseline, invalid_cases)
            baseline = without_invalid(raw_baseline, baseline_excluded)
            baseline_report = score_triggers(triggers, baseline)
            report["baseline"] = baseline_report
            report["baseline_excluded_invalid"] = baseline_excluded
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
