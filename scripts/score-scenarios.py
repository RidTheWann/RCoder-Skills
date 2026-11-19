#!/usr/bin/env python3
"""Score scenario rubric items from retained agent transcripts using a pinned judge model.

The judge is the same pinned model used for the ablation. It receives only a
bounded transcript summary and the objective rubric, and must return a JSON
boolean list per scenario. Raw judge responses are retained for audit. This is
an LLM-as-judge measurement with a disclosed same-model bias, not ground truth.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCENARIOS = ROOT / "evals" / "scenarios.json"
HELPER = ROOT / "scripts" / "run-benchmark.py"
EVIDENCE_LIMIT = 9000


def load_helper():
    spec = importlib.util.spec_from_file_location("rb", HELPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--opencode", nargs="+", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()

    rb = load_helper()
    scenarios = rb.load_json(SCENARIOS)
    judged = {}
    judge_log = {}
    for arm in ("with", "without"):
        pred_path = args.run_dir / (arm.upper() + ".jsonl")
        predictions = []
        for line in pred_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                predictions.append(json.loads(line))
        by_id = {item["id"]: item for item in predictions}
        for scenario in scenarios:
            sid = scenario["id"]
            valid, _ = rb.case_valid(args.run_dir / "raw", arm, sid)
            if sid not in by_id or not valid:
                continue
            summary = transcript_summary(args.run_dir / "raw" / arm / (sid + ".jsonl"))
            response = judge(args.opencode, args.model, summary, scenario["rubric"], args.timeout)
            flags = parse_flags(response, len(scenario["rubric"]))
            judge_log[f"{arm}/{sid}"] = {"response": response[:2000], "parsed": flags}
            if flags is None:
                continue
            by_id[sid]["scenario_scores"] = {sid: flags}
        judged[arm] = [by_id[item["id"]] for item in predictions]
        with pred_path.open("w", encoding="utf-8") as handle:
            for record in judged[arm]:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(f"judged {arm}: {sum(1 for s in scenarios if 'scenario_scores' in by_id.get(s['id'], {}))}/{len(scenarios)}")
    (args.run_dir / "judge-log.json").write_text(json.dumps(judge_log, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
