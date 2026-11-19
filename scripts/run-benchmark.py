#!/usr/bin/env python3
"""Run controlled with/without-RCoder ablation cases against an OpenCode CLI.

This harness holds model, CLI, fixtures, prompts, and rubric constant. It writes
one checkpointed raw transcript per (arm, case) and assembles JSONL prediction
files compatible with scripts/score-eval.py. It does not fabricate predictions:
every flag is derived from observable JSON events in the captured transcript.

Example:
  python3 scripts/run-benchmark.py --run-dir /tmp/bench-run \
    --opencode /path/to/opencode-wrapper --limit 4 --parallel 2
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRIGGERS = ROOT / "evals" / "triggers.json"
SCENARIOS = ROOT / "evals" / "scenarios.json"
FIXTURE_FILES = ROOT / "evals" / "scenarios"
CANONICAL_SKILL = ROOT / "skills" / "rcoder"

REF_IDS = sorted(p.stem for p in (CANONICAL_SKILL / "references").glob("*.md"))
REF_PATTERN = re.compile(r"references/(" + "|".join(re.escape(x) for x in REF_IDS) + r")\.md")

FIXTURE_README = (
    "# Sample engineering fixture\n\n"
    "This is a controlled fixture for engineering-planning and analysis tasks.\n"
    "Source files are intentionally not included. Provide analysis, plans, and\n"
    "evidence-based reasoning using only the information in the request. Do not\n"
    "modify files outside this directory.\n"
)


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def sha256_tree(path: Path) -> str:
    digest = hashlib.sha256()
    for file in sorted(path.rglob("*")):
        if file.is_file():
            digest.update(str(file.relative_to(path)).encode())
            digest.update(file.read_bytes())
    return digest.hexdigest()


def prepare_fixtures(run_dir: Path) -> dict:
    fixtures = {}
    for arm, with_rcoder in (("with", True), ("without", False)):
        base = run_dir / ("fixture-" + arm)
        base.mkdir(parents=True, exist_ok=True)
        (base / "README.md").write_text(FIXTURE_README, encoding="utf-8")
        skill_dir = base / ".opencode" / "skills" / "rcoder"
        if with_rcoder:
            if skill_dir.exists():
                shutil.rmtree(skill_dir)
            shutil.copytree(CANONICAL_SKILL, skill_dir)
        elif skill_dir.exists():
            shutil.rmtree(skill_dir)
        fixtures[arm] = base
    return {
        "with_skill_sha256": sha256_tree(run_dir / "fixture-with" / ".opencode" / "skills" / "rcoder"),
        "without_has_rcoder": (run_dir / "fixture-without" / ".opencode" / "skills" / "rcoder").exists(),
        "with_has_rcoder": (run_dir / "fixture-with" / ".opencode" / "skills" / "rcoder" / "SKILL.md").exists(),
    }


def run_case(opencode: list[str], model: str, arm: str, fixture: Path,
             case_id: str, prompt: str, fixture_md: Path | None,
             timeout: int, raw_dir: Path) -> dict:
    dest = raw_dir / arm
    dest.mkdir(parents=True, exist_ok=True)
    out = dest / (case_id + ".jsonl")
    err = dest / (case_id + ".err")
    meta = dest / (case_id + ".meta.json")
    if out.exists() and meta.exists():
        return json.loads(meta.read_text(encoding="utf-8"))
    cmd = list(opencode) + ["run", prompt, "--model", model, "--dir", str(fixture), "--format", "json"]
    if fixture_md is not None:
        cmd += ["--file", str(fixture_md)]
    started = time.time()
    result: dict
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        stdout, stderr, code = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout or ""
        stderr = (error.stderr or "") + "\n[benchmark timeout]"
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", "replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", "replace")
        code = 124
    duration = round(time.time() - started, 3)
    out.write_text(stdout, encoding="utf-8")
    err.write_text(stderr, encoding="utf-8")
    result = {"case_id": case_id, "arm": arm, "exit_code": code, "duration_s": duration,
              "stdout_bytes": len(stdout), "stderr_bytes": len(stderr)}
    meta.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return result


def case_valid(raw_dir: Path, arm: str, case_id: str) -> tuple[bool, str]:
    """A captured case is valid only if it produced agent text without a provider error."""
    out = raw_dir / arm / (case_id + ".jsonl")
    err = raw_dir / arm / (case_id + ".err")
    stderr = err.read_text(encoding="utf-8", errors="replace") if err.exists() else ""
    if "usage limit" in stderr.lower():
        return False, "provider_free_usage_limit_reached"
    if "stream error" in stderr.lower():
        return False, "provider_stream_error"
    if not out.exists():
        return False, "missing_transcript"
    has_text = False
    for line in out.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "text" and (event.get("part", {}).get("text", "") or "").strip():
            has_text = True
            break
    if not has_text:
        return False, "no_agent_text"
    return True, "ok"


def parse_events(raw_dir: Path, arm: str, case_id: str) -> dict:
    path = raw_dir / arm / (case_id + ".jsonl")
    skill_invoked = False
    skill_md_read = False
    specialists: set[str] = set()
    tool_calls = 0
    tool_errors = 0
    tokens = {}
    if not path.exists():
        return {"skill_invoked": False, "skill_md_read": False, "specialists": [],
                "tool_calls": 0, "tool_errors": 0, "tokens": {}}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind = event.get("type")
        part = event.get("part", {}) or {}
        if kind == "tool_use":
            tool_calls += 1
            state = part.get("state", {}) or {}
            tool = part.get("tool")
            if state.get("status") == "error":
                tool_errors += 1
            inp = state.get("input", {}) or {}
            blob = json.dumps(inp, ensure_ascii=False)
            if tool == "skill" and str(inp.get("name", "")).lower() == "rcoder":
                skill_invoked = True
            if tool in {"read", "bash", "grep"}:
                if "rcoder/SKILL.md" in blob or "rcoder\\\\SKILL.md" in blob:
                    skill_md_read = True
                for found in REF_PATTERN.findall(blob):
                    specialists.add(found)
        if kind == "step_finish":
            tok = part.get("tokens", {}) or {}
            if tok:
                tokens = tok
    return {
        "skill_invoked": skill_invoked,
        "skill_md_read": skill_md_read,
        "specialists": sorted(specialists),
        "tool_calls": tool_calls,
        "tool_errors": tool_errors,
        "tokens": tokens,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--opencode", nargs="+", default=["opencode"])
    parser.add_argument("--model", default="opencode/hy4-flash-free")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--parallel", type=int, default=2)
    parser.add_argument("--limit", type=int, default=0, help="0 = all cases")
    parser.add_argument("--triggers-only", action="store_true")
    parser.add_argument("--scenarios-only", action="store_true")
    args = parser.parse_args()

    run_dir = args.run_dir
    run_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = run_dir / "raw"
    raw_dir.mkdir(exist_ok=True)
    fixture_info = prepare_fixtures(run_dir)
    (run_dir / "isolation.json").write_text(json.dumps(fixture_info, indent=2, sort_keys=True), encoding="utf-8")

    cases = []
    if not args.scenarios_only:
        for trig in load_json(TRIGGERS):
            cases.append(("trigger", trig["id"], trig["prompt"], None))
    if not args.triggers_only:
        for scen in load_json(SCENARIOS):
            md = FIXTURE_FILES / (scen["id"] + ".md")
            cases.append(("scenario", scen["id"], scen["prompt"], md if md.exists() else None))
    if args.limit:
        cases = cases[: args.limit]
    (run_dir / "cases.json").write_text(
        json.dumps([{"kind": k, "id": i, "prompt": p} for k, i, p, _ in cases], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    jobs = [(arm, case) for case in cases for arm in ("with", "without")]
    results = []
    with ThreadPoolExecutor(max_workers=args.parallel) as pool:
        futures = {
            pool.submit(run_case, args.opencode, args.model, arm,
                        run_dir / ("fixture-" + arm), cid, prompt, md,
                        args.timeout, raw_dir): (arm, cid)
            for arm, (_, cid, prompt, md) in jobs
        }
        for future in as_completed(futures):
            arm, cid = futures[future]
            try:
                res = future.result()
                results.append(res)
                print(f"[{arm}] {cid}: exit={res['exit_code']} {res['duration_s']}s", flush=True)
            except Exception as error:
                print(f"[{arm}] {cid}: FAILED {error}", file=sys.stderr, flush=True)

    predictions = {"with": [], "without": []}
    evidence = {"with": {}, "without": {}}
    invalid: dict[str, list[str]] = {"with": [], "without": []}
    for arm in ("with", "without"):
        for kind, cid, _, _ in cases:
            valid, reason = case_valid(raw_dir, arm, cid)
            if not valid:
                invalid[arm].append(cid)
            ev = parse_events(raw_dir, arm, cid)
            ev["valid"] = valid
            ev["invalid_reason"] = reason
            evidence[arm][cid] = ev
            if not valid:
                continue
            predicted = ev["skill_invoked"] or ev["skill_md_read"] or bool(ev["specialists"])
            record = {"id": cid, "predicted_trigger": predicted,
                      "selected_specialists": ev["specialists"] if kind == "trigger" else [],
                      "evidence": ev}
            predictions[arm].append(record)
        with (run_dir / (arm.upper() + ".jsonl")).open("w", encoding="utf-8") as handle:
            for record in predictions[arm]:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    (run_dir / "evidence.json").write_text(json.dumps(evidence, indent=2, sort_keys=True), encoding="utf-8")
    (run_dir / "invalid-cases.json").write_text(json.dumps(invalid, indent=2, sort_keys=True), encoding="utf-8")

    done = sum(1 for r in results if r["exit_code"] != 124)
    print(f"DONE cases={len(cases)} arms=2 completed={len(results)} timeouts={len(results)-done}")
    for arm in ("with", "without"):
        print(f"VALID {arm}={len(predictions[arm])} INVALID {arm}={len(invalid[arm])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
