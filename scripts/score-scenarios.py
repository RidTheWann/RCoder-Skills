#!/usr/bin/env python3
"""Score scenario rubric items from retained agent transcripts using a judge model.

The judge may be the tested model (disclosed same-model bias) or, when
--judge-model is supplied, a separate authorized model. The grader receives a
bounded, arm-blinded transcript summary and an objective rubric, and must return
a JSON boolean list per scenario. Raw judge responses are retained in full for
audit. This is an LLM-as-judge measurement, not ground truth; deterministic
objective evidence is produced separately by verify-objective.py.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import random
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCENARIOS = ROOT / "evals" / "scenarios.json"
HELPER = ROOT / "scripts" / "run-benchmark.py"
EVIDENCE_LIMIT = 9000

ARM_PATTERNS = (
    (re.compile(r"fixture-without"), "fixture-arm"),
    (re.compile(r"fixture-with"), "fixture-arm"),
    (re.compile(r"(?i)\bwithout arm\b"), "arm"),
    (re.compile(r"(?i)\bwith arm\b"), "arm"),
    (re.compile(r"(?i)(WITH|WITHOUT)\.jsonl"), "arm.jsonl"),
)


def load_helper():
    spec = importlib.util.spec_from_file_location("rb", HELPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def blind_summary(summary: str) -> str:
    """Remove arm-identifying labels from evidence shown to the judge."""
    result = summary
    for pattern, replacement in ARM_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


def transcript_summary(path: Path) -> str:
    pieces = []
    total = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind = event.get("type")
        part = event.get("part", {}) or {}
        if kind == "text":
            text = (part.get("text", "") or "").strip()
            if text:
                pieces.append("AGENT: " + text)
                total += len(text)
        elif kind == "tool_use":
            state = part.get("state", {}) or {}
            tool = part.get("tool", "?")
            inp = json.dumps(state.get("input", {}), ensure_ascii=False)
            err = state.get("error", "")
            line_text = f"TOOL {tool}: {inp[:500]}" + (f" ERROR {err}" if err else "")
            pieces.append(line_text)
            total += len(line_text)
        if total >= EVIDENCE_LIMIT:
            break
    return "\n".join(pieces)[:EVIDENCE_LIMIT]


def judge(opencode: list[str], model: str, summary: str, rubric: list[str], timeout: int) -> str:
    items = "\n".join(f"{i + 1}. {item}" for i, item in enumerate(rubric))
    prompt = (
        "You are grading an agent transcript against an objective rubric. "
        "Use ONLY the evidence below. For each numbered item return true only if the "
        "transcript directly shows it; otherwise return false. Do not infer success "
        "from intent. Reply with ONLY a JSON array of booleans, one per item, e.g. [true,false,true,false].\n\n"
        "RUBRIC\n" + items + "\n\nTRANSCRIPT SUMMARY\n" + summary
    )
    proc = subprocess.run(
        list(opencode) + ["run", prompt, "--model", model, "--format", "json", "--title", "rubric-judge"],
        capture_output=True, text=True, timeout=timeout, check=False,
    )
    texts = []
    for line in proc.stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "text":
            texts.append(event.get("part", {}).get("text", ""))
    return "".join(texts).strip()


def parse_flags(text: str, length: int) -> list[bool] | None:
    for match in re.finditer(r"\[[^\]]*\]", text):
        try:
            value = json.loads(match.group(0))
        except json.JSONDecodeError:
            continue
        if isinstance(value, list) and len(value) == length and all(isinstance(x, bool) for x in value):
            return value
    return None


def judged_path(run_dir: Path, arm: str, overwrite: bool) -> Path:
    original = run_dir / (arm.upper() + ".jsonl")
    if overwrite:
        return original
    return run_dir / "judged" / (arm.upper() + ".jsonl")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--opencode", nargs="+", required=True)
    parser.add_argument("--model", required=True, help="Model under test")
    parser.add_argument("--judge-model", help="Optional separate, authorized judge model")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--seed", type=int, default=0, help="Seed for blinded evaluation order")
    parser.add_argument("--blind-order", action="store_true", help="Shuffle judge call order with --seed")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite retained prediction files (legacy behaviour)")
    args = parser.parse_args()

    judge_model = args.judge_model or args.model
    rb = load_helper()
    scenarios = rb.load_json(SCENARIOS)
    judge_log = {
        "_methodology": {
            "tested_model": args.model,
            "judge_model": judge_model,
            "same_model_judge": judge_model == args.model,
            "arm_labels_hidden": True,
            "blind_order": args.blind_order,
            "seed": args.seed,
            "disclosure": "LLM-as-judge measurement; not ground truth. Same-model bias applies when same_model_judge is true.",
        }
    }
    work = []
    by_arm = {}
    for arm in ("with", "without"):
        pred_path = args.run_dir / (arm.upper() + ".jsonl")
        if not pred_path.is_file():
            raise SystemExit(f"Missing predictions: {pred_path}")
        predictions = [json.loads(line) for line in pred_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        by_id = {item["id"]: item for item in predictions}
        by_arm[arm] = (predictions, by_id)
        for scenario in scenarios:
            sid = scenario["id"]
            valid, _ = rb.case_valid(args.run_dir / "raw", arm, sid)
            if sid in by_id and valid:
                work.append((arm, sid))
    if args.blind_order:
        random.Random(args.seed).shuffle(work)

    for arm, sid in work:
        scenario = next(item for item in scenarios if item["id"] == sid)
        summary = blind_summary(transcript_summary(args.run_dir / "raw" / arm / (sid + ".jsonl")))
        response = judge(args.opencode, judge_model, summary, scenario["rubric"], args.timeout)
        flags = parse_flags(response, len(scenario["rubric"]))
        judge_log[f"{arm}/{sid}"] = {
            "response": response,
            "parsed": flags,
            "judge_model": judge_model,
        }
        if flags is not None:
            by_arm[arm][1][sid]["scenario_scores"] = {sid: flags}

    for arm in ("with", "without"):
        predictions, _ = by_arm[arm]
        output = judged_path(args.run_dir, arm, args.overwrite)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", encoding="utf-8") as handle:
            for record in predictions:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(f"judged {arm}: wrote {output}")
    (args.run_dir / "judge-log.json").write_text(
        json.dumps(judge_log, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
