#!/usr/bin/env python3
"""Deterministic objective verifier for benchmark prediction artifacts.

Produces an independent evidence layer from retained artifacts only. It never
invokes the tested model, never reads prose as proof, and never guesses. Each
check is a boolean over observable files/fields, with a machine-readable name.
Output is JSONL consumable by `score-eval.py --objective`.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EXPECTATIONS = ROOT / "evals" / "routing-expectations.json"
DEFAULT_REFERENCES = ROOT / "skills" / "rcoder" / "references"

HELPER_MODULES = frozenset({
    "verification", "rsaver", "rsaver-gate", "token-efficiency", "model-adaptation",
})

TRIGGER_CHECKS = (
    "prediction_shape",
    "specialists_are_known",
    "activation_has_specialists",
    "negative_not_activated",
    "negative_selection_empty",
    "non_helper_primary",
    "expected_specialist_overlap",
)
CASE_CHECKS = (
    "prediction_shape",
    "raw_transcript_present",
)


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def known_modules(references: Path) -> set[str]:
    return {path.stem for path in references.glob("*.md")}


def read_predictions(path: Path) -> list[dict]:
    records = []
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(f"{path}:{number}: invalid JSON: {error}") from error
    if not records:
        raise ValueError(f"{path}: no prediction records")
    return records


def verify_trigger(record: dict, expectations: dict, modules: set[str]) -> list[bool]:
    item_id = record.get("id", "")
    predicted = record.get("predicted_trigger")
    selected = record.get("selected_specialists")
    expected = set(expectations.get(item_id, []))
    is_positive_trigger = bool(expected)
    selected_names = set(selected) if isinstance(selected, list) else set()
    return [
        isinstance(predicted, bool) and isinstance(selected, list),
        isinstance(selected, list) and all(name in modules for name in selected),
        (not (predicted is True and is_positive_trigger)) or bool(selected),
        predicted is not True or is_positive_trigger,
        is_positive_trigger or not selected_names,
        not selected_names or any(name not in HELPER_MODULES for name in selected_names),
        not is_positive_trigger or not selected_names or bool(selected_names & expected),
    ]


def verify_case(record: dict, raw_dir: Path | None) -> list[bool]:
    item_id = record.get("id", "")
    present = False
    if raw_dir is not None:
        transcript = raw_dir / f"{item_id}.jsonl"
        present = transcript.is_file() and transcript.stat().st_size > 0
    return [
        isinstance(record.get("id"), str) and isinstance(record.get("scenario_scores"), dict),
        present,
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--expectations", type=Path, default=DEFAULT_EXPECTATIONS)
    parser.add_argument("--references", type=Path, default=DEFAULT_REFERENCES)
    parser.add_argument("--run-dir", type=Path, help="Optional benchmark run dir; enables transcript-presence checks")
    parser.add_argument("--arm", choices=("with", "without"), default="with")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--definitions", type=Path, help="Optional JSON file mapping case IDs to check names")
    parser.add_argument("--strict", action="store_true", help="Exit 1 when any emitted check fails")
    args = parser.parse_args()

    try:
        predictions = read_predictions(args.predictions)
        expectations = load_json(args.expectations)["expectations"]
        modules = known_modules(args.references)
        raw_dir = args.run_dir / "raw" / args.arm if args.run_dir else None
        records = []
        definitions = {}
        for item in predictions:
            item_id = item.get("id")
            if not isinstance(item_id, str):
                raise ValueError("prediction record missing string id")
            if item_id in expectations:
                flags = verify_trigger(item, expectations, modules)
                definitions[item_id] = list(TRIGGER_CHECKS)
            else:
                flags = verify_case(item, raw_dir)
                definitions[item_id] = list(CASE_CHECKS)
            records.append({"id": item_id, "objective_checks": {item_id: flags}})
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n",
            encoding="utf-8",
        )
        if args.definitions:
            args.definitions.parent.mkdir(parents=True, exist_ok=True)
            args.definitions.write_text(json.dumps(definitions, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    failed = sum(1 for record in records for flag in record["objective_checks"][record["id"]] if not flag)
    print(f"objective verification: {len(records)} cases, {failed} failed check(s) -> {args.output}")
    return 1 if failed and args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
