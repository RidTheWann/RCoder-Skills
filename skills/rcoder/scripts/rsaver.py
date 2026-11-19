#!/usr/bin/env python3
"""RSaver: evidence-preserving context reduction with a recoverable manifest.

RSaver prunes or deduplicates context instead of rewriting it. Retained lines are
copied verbatim, and every omitted range is recorded so it can be recovered
exactly. Token figures are deterministic dependency-free estimates for relative
comparison only, not model billing or hard context-limit measurements.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

VERSION = "1.4.0"
PIECES = re.compile(r"[^\W\d_]+|\d+|[^\s\w]", re.UNICODE)
DEFAULT_CRITICAL = (
    r"(?i)(error|fail|exception|traceback|fatal|panic|exit[ _-]?code|"
    r"status[=:]\s*\d+|sha256|\b[0-9a-f]{40,}\b|https?://|"
    r"\bnot verified\b|\binferred\b|\bunknown\b)"
)
HEADING = re.compile(r"^\s{0,3}#{1,6}\s")


def estimate(text: str) -> int:
    total = 0
    for match in PIECES.finditer(text):
        length = len(match.group(0))
        total += 1 if length <= 4 else (length + 3) // 4
    return total


def chars_over_four(text: str) -> int:
    return (len(text) + 3) // 4


def read_lines(path: str) -> list[str]:
    if path == "-":
        return sys.stdin.read().splitlines()
    return Path(path).read_text(encoding="utf-8", errors="replace").splitlines()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def to_ranges(indices: set[int]) -> list[list[int]]:
    result: list[list[int]] = []
    for index in sorted(indices):
        if result and index == result[-1][1] + 1:
            result[-1][1] = index
        else:
            result.append([index, index])
    return result


def range_text(lines: list[str], ranges: list[list[int]]) -> str:
    return "\n".join("\n".join(lines[start - 1:end]) for start, end in ranges)


def line_text(lines: list[str], indices: set[int]) -> str:
    return "\n".join(lines[index - 1] for index in sorted(indices))


def format_indices(indices: list[int]) -> str:
    parts: list[str] = []
    start = previous = indices[0]
    for value in indices[1:]:
        if value == previous + 1:
            previous = value
            continue
        parts.append(str(start) if start == previous else f"{start}-{previous}")
        start = previous = value
    parts.append(str(start) if start == previous else f"{start}-{previous}")
    return ",".join(parts)


def critical_indices(lines: list[str], pattern: str) -> set[int]:
    expression = re.compile(pattern)
    return {index for index, line in enumerate(lines, 1) if expression.search(line)}


def structural_indices(lines: list[str]) -> set[int]:
    return {
        index for index, line in enumerate(lines, 1)
        if HEADING.match(line) or line.strip() in {"```", "---", "===", "..."}
    }


def make_manifest(path: str, lines: list[str], critical: set[int],
                  kept: set[int], pattern: str, method: str,
                  budget_exceeded: bool = False) -> dict:
    kept_ranges = to_ranges(kept)
    omitted = set(range(1, len(lines) + 1)) - kept
    omitted_ranges = to_ranges(omitted)
    kept_text = line_text(lines, kept)
    original_text = "\n".join(lines)
    original_estimate = estimate(original_text)
    compact_estimate = estimate(kept_text)
    saved = original_estimate - compact_estimate
    return {
        "tool": "RSaver",
        "version": VERSION,
        "method": method,
        "file": path,
        "original_sha256": sha256_text(original_text),
        "original_lines": len(lines),
        "critical_pattern": pattern,
        "critical_lines": sorted(critical),
        "kept_ranges": kept_ranges,
        "kept_range_sha256": {
            f"{start}-{end}": sha256_text("\n".join(lines[start - 1:end]))
            for start, end in kept_ranges
        },
        "omitted_ranges": omitted_ranges,
        "recovery_command": "rsaver recover --file <file> --range START:END",
        "budget_exceeded_by_critical": budget_exceeded,
        "estimate": {
            "method": "dependency_free_run_heuristic_v1",
            "original_estimate": original_estimate,
            "compact_estimate": compact_estimate,
            "chars_over_4_original": chars_over_four(original_text),
            "chars_over_4_compact": chars_over_four(kept_text),
            "saved_estimate": saved,
            "saved_percent": round(100 * saved / original_estimate, 2) if original_estimate else 0.0,
        },
    }


def emit(payload: dict, as_json: bool, text: str, label: str, text_key: str = "text") -> int:
    if as_json:
        enriched = dict(payload)
        enriched[text_key] = text
        print(json.dumps(enriched, indent=2, sort_keys=True))
        return 0
    print(text)
    stats = payload.get("estimate", payload.get("stats", {}))
    if stats:
        print(
            f"RSaver {label}: original={stats.get('original_estimate', 0)} "
            f"reduced={stats.get('compact_estimate', stats.get('deduped_estimate', 0))} "
            f"saved={stats.get('saved_estimate', 0)} "
            f"({stats.get('saved_percent', 0.0)}%)",
            file=sys.stderr,
        )
    if payload.get("omitted_ranges"):
        print(f"RSaver manifest: {len(payload['omitted_ranges'])} omitted ranges are recoverable", file=sys.stderr)
    return 0


def command_measure(args: argparse.Namespace) -> int:
    rows = []
    for path in args.paths:
        lines = read_lines(path)
        text = "\n".join(lines)
        rows.append({
            "path": path,
            "lines": len(lines),
            "estimate": estimate(text),
            "chars_over_4": chars_over_four(text),
        })
    total_estimate = sum(row["estimate"] for row in rows)
    if args.json:
        print(json.dumps({"estimate_method": "dependency_free_run_heuristic_v1",
                          "files": rows, "total_estimate": total_estimate}, indent=2, sort_keys=True))
    else:
        for row in rows:
            print(f"{row['path']}: lines={row['lines']} estimate={row['estimate']} chars/4={row['chars_over_4']}")
        print(f"TOTAL estimate={total_estimate} (relative estimate, not a model token count)")
    return 0


def command_select(args: argparse.Namespace) -> int:
    lines = read_lines(args.path)
    expression = re.compile(args.match)
    matched = {index for index, line in enumerate(lines, 1) if expression.search(line)}
    if not matched:
        raise ValueError("no lines matched the pattern")
    selected = set(matched)
    for index in matched:
        for offset in range(1, args.context + 1):
            if index - offset >= 1:
                selected.add(index - offset)
            if index + offset <= len(lines):
                selected.add(index + offset)
    budget_exceeded = len(selected) > args.max_lines
    if budget_exceeded:
        chosen = set(matched)
        for index in sorted(matched):
            for offset in range(1, args.context + 1):
                if len(chosen) >= args.max_lines:
                    break
                for candidate in (index + offset, index - offset):
                    if 1 <= candidate <= len(lines):
                        chosen.add(candidate)
        selected = chosen
    ranges = to_ranges(selected)
    text = range_text(lines, ranges)
    manifest = make_manifest(args.path, lines, matched, selected, args.match, "bounded_symbol_select", budget_exceeded)
    return emit(manifest, args.json, text, "select", "selected_text")


def command_compact(args: argparse.Namespace) -> int:
    lines = read_lines(args.path)
    critical = critical_indices(lines, args.critical)
    structural = structural_indices(lines)
    head = set(range(1, min(args.head, len(lines)) + 1))
    tail = set(range(max(1, len(lines) - args.tail + 1), len(lines) + 1))
    ranked: list[int] = []
    for group in (sorted(critical), sorted(structural), sorted(head), sorted(tail)):
        for index in group:
            if index not in ranked:
                ranked.append(index)
    budget_exceeded = len(critical) > args.max_lines
    kept = set(ranked) if budget_exceeded else set(ranked[:args.max_lines])
    text = line_text(lines, kept)
    manifest = make_manifest(args.path, lines, critical, kept, args.critical, "structure_preserving_prune", budget_exceeded)
    if args.manifest:
        Path(args.manifest).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.verify:
        problems = verify_manifest(manifest, lines)
        if problems:
            for problem in problems:
                print(f"RSAVER VERIFY FAIL: {problem}", file=sys.stderr)
            return 1
    return emit(manifest, args.json, text, "compact", "compacted")


def command_dedupe(args: argparse.Namespace) -> int:
    all_lines: list[str] = []
    for path in args.paths:
        all_lines.extend(read_lines(path))
    critical = critical_indices(all_lines, args.critical)
    counts: dict[str, list[int]] = {}
    for index, line in enumerate(all_lines, 1):
        if index not in critical:
            counts.setdefault(line, []).append(index)

    def marker_for(line: str, duplicates: list[int]) -> str:
        return f"[RSaver: {len(duplicates) - 1} identical non-critical line(s) collapsed; original lines {format_indices(duplicates)}]"

    collapse: set[str] = set()
    for line, duplicates in counts.items():
        if len(duplicates) > 1:
            removed = (len(duplicates) - 1) * estimate(line)
            if estimate(marker_for(line, duplicates)) < removed:
                collapse.add(line)
    seen: set[str] = set()
    output: list[str] = []
    for index, line in enumerate(all_lines, 1):
        if index in critical or line not in collapse:
            output.append(line)
            continue
        if line in seen:
            continue
        seen.add(line)
        output.append(line)
        output.append(marker_for(line, counts[line]))
    original_text = "\n".join(all_lines)
    deduped_text = "\n".join(output)
    original_estimate = estimate(original_text)
    deduped_estimate = estimate(deduped_text)
    saved = original_estimate - deduped_estimate
    stats = {
        "method": "dependency_free_run_heuristic_v1",
        "original_estimate": original_estimate,
        "deduped_estimate": deduped_estimate,
        "saved_estimate": saved,
        "saved_percent": round(100 * saved / original_estimate, 2) if original_estimate else 0.0,
    }
    manifest = {"tool": "RSaver", "version": VERSION, "method": "exact_duplicate_collapse",
                "inputs": args.paths, "critical_lines_preserved": sorted(critical), "stats": stats}
    return emit(manifest, args.json, deduped_text, "dedupe", "deduped_text")


def verify_manifest(manifest: dict, lines: list[str]) -> list[str]:
    problems: list[str] = []
    original = "\n".join(lines)
    if manifest.get("original_sha256") != sha256_text(original):
        problems.append("original content hash does not match the manifest")
    kept = {index for start, end in manifest.get("kept_ranges", []) for index in range(start, end + 1)}
    critical = critical_indices(lines, manifest.get("critical_pattern", DEFAULT_CRITICAL))
    missing = sorted(critical - kept)
    if missing:
        problems.append(f"critical lines missing from kept ranges: {missing}")
    for key, digest in manifest.get("kept_range_sha256", {}).items():
        start, end = (int(part) for part in key.split("-"))
        if sha256_text("\n".join(lines[start - 1:end])) != digest:
            problems.append(f"kept range {key} content changed")
    return problems


def command_verify(args: argparse.Namespace) -> int:
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    path = args.file or manifest.get("file", "")
    if path == "-":
        raise ValueError("--file is required for verify when input was stdin")
    lines = read_lines(path)
    problems = verify_manifest(manifest, lines)
    if problems:
        for problem in problems:
            print(f"RSAVER VERIFY FAIL: {problem}", file=sys.stderr)
        return 1
    print(f"RSAVER VERIFY PASS: {manifest.get('file')} critical lines and range hashes intact")
    return 0


def command_recover(args: argparse.Namespace) -> int:
    lines = read_lines(args.file)
    start, end = (int(part) for part in args.range.split(":"))
    if not (1 <= start <= end <= len(lines)):
        raise ValueError(f"invalid range {args.range} for {len(lines)} lines")
    text = "\n".join(lines[start - 1:end])
    if args.json:
        print(json.dumps({"file": args.file, "range": [start, end], "text": text}, sort_keys=True))
    else:
        print(text)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=f"RSaver {VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)

    measure = sub.add_parser("measure", help="estimate the size of files or stdin")
    measure.add_argument("paths", nargs="+")
    measure.add_argument("--json", action="store_true", help="emit JSON instead of text")
    measure.set_defaults(func=command_measure)

    select = sub.add_parser("select", help="extract bounded line ranges around matches")
    select.add_argument("path")
    select.add_argument("--match", required=True, help="regular expression selecting anchor lines")
    select.add_argument("--context", type=int, default=2)
    select.add_argument("--max-lines", type=int, default=120)
    select.add_argument("--json", action="store_true")
    select.set_defaults(func=command_select)

    compact = sub.add_parser("compact", help="prune non-critical context while preserving evidence")
    compact.add_argument("path")
    compact.add_argument("--max-lines", type=int, default=120)
    compact.add_argument("--head", type=int, default=8)
    compact.add_argument("--tail", type=int, default=8)
    compact.add_argument("--critical", default=DEFAULT_CRITICAL)
    compact.add_argument("--manifest", help="write the recoverability manifest to this path")
    compact.add_argument("--verify", action="store_true", help="verify the manifest against the original before output")
    compact.add_argument("--json", action="store_true")
    compact.set_defaults(func=command_compact)

    dedupe = sub.add_parser("dedupe", help="collapse exact repeated non-critical lines")
    dedupe.add_argument("paths", nargs="+")
    dedupe.add_argument("--critical", default=DEFAULT_CRITICAL)
    dedupe.add_argument("--json", action="store_true")
    dedupe.set_defaults(func=command_dedupe)

    verify = sub.add_parser("verify", help="check a manifest against the original file")
    verify.add_argument("--manifest", required=True)
    verify.add_argument("--file", help="override the original file path")
    verify.set_defaults(func=command_verify)

    recover = sub.add_parser("recover", help="print exact original lines from a range")
    recover.add_argument("--file", required=True)
    recover.add_argument("--range", required=True, help="START:END, 1-based inclusive")
    recover.add_argument("--json", action="store_true")
    recover.set_defaults(func=command_recover)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if getattr(args, "context", 0) < 0 or getattr(args, "max_lines", 1) < 1:
        parser.error("--context must be >= 0 and --max-lines must be >= 1")
    try:
        return args.func(args)
    except (OSError, ValueError, re.error, json.JSONDecodeError, KeyError) as error:
        print(f"RSaver ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
