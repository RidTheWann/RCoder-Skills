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

VERSION = "1.6.0"
PIECES = re.compile(r"[^\W\d_]+|\d+|[^\s\w]", re.UNICODE)
DEFAULT_CRITICAL = (
    r"(?i)(error|fail|exception|traceback|fatal|panic|exit[ _-]?code|"
    r"status[=:]\s*\d+|sha256|\b[0-9a-f]{40,}\b|https?://|"
    r"\bnot verified\b|\binferred\b|\bunknown\b)"
)
HEADING = re.compile(r"^\s{0,3}#{1,6}\s")

PROFILES = {
    "generic": {"digits": 3, "word_chars": 7.0, "nonascii_chars": 4.5,
                "cjk_chars": 0.8, "emoji": 2, "symbol_chars": 2.7},
    "openai-cl100k": {"digits": 3, "word_chars": 5.0, "nonascii_chars": 3.6,
                      "cjk_chars": 1.0, "emoji": 2, "symbol_chars": 2.3},
    "openai-o200k": {"digits": 3, "word_chars": 7.5, "nonascii_chars": 5.0,
                     "cjk_chars": 0.7, "emoji": 2, "symbol_chars": 3.0},
    "gpt2": {"digits": 99, "word_chars": 4.5, "nonascii_chars": 3.0,
             "cjk_chars": 1.3, "emoji": 3, "symbol_chars": 2.0},
    "cjk-native": {"digits": 3, "word_chars": 6.0, "nonascii_chars": 4.0,
                   "cjk_chars": 0.6, "emoji": 2, "symbol_chars": 2.5},
}
CHUNK_RE = re.compile(
    r"'(?:s|t|re|ve|m|ll|d)| ?[^\W\d_]+|\d+| ?[^\s\w]+|\s+|.",
    re.IGNORECASE | re.UNICODE,
)
SPECIAL_RE = re.compile(r"<\|[A-Za-z0-9_]+\|>")
CJK_RANGES = (
    (0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0xF900, 0xFAFF),
    (0x3040, 0x30FF), (0xAC00, 0xD7AF), (0x1F300, 0x1FAFF),
)


def is_emoji(char: str) -> bool:
    return 0x1F300 <= ord(char) <= 0x1FAFF


def is_cjk(char: str) -> bool:
    code = ord(char)
    return any(start <= code <= end for start, end in CJK_RANGES[:5])


def classify_chunk(chunk: str) -> str:
    body = chunk.lstrip(" ")
    if not body:
        return "whitespace"
    if SPECIAL_RE.fullmatch(body):
        return "special"
    if body.isdigit():
        return "digits"
    if is_emoji(body[0]):
        return "emoji"
    if is_cjk(body[0]):
        return "cjk"
    if body.isalpha():
        return "word" if body.isascii() else "word_nonascii"
    if any(is_cjk(char) or is_emoji(char) for char in body):
        return "mixed_unicode"
    if body[0].isspace():
        return "whitespace"
    return "symbol"


def estimate_v2(text: str, profile: str = "generic") -> int:
    settings = PROFILES.get(profile, PROFILES["generic"])
    total = 0
    special_count = len(SPECIAL_RE.findall(text))
    stripped = SPECIAL_RE.sub("", text)
    for match in CHUNK_RE.finditer(stripped):
        chunk = match.group(0)
        kind = classify_chunk(chunk)
        if kind == "special":
            continue
        if kind == "digits":
            total += max(1, -(-len(chunk) // settings["digits"]))
        elif kind == "word":
            total += max(1, -(-len(chunk) // int(settings["word_chars"])))
        elif kind == "word_nonascii":
            total += max(1, -(-len(chunk) // int(settings["nonascii_chars"])))
        elif kind == "cjk":
            total += max(1, int(len(chunk) * settings["cjk_chars"]))
        elif kind == "emoji":
            total += settings["emoji"] * len(chunk)
        elif kind == "mixed_unicode":
            total += sum(settings["emoji"] if is_emoji(char) else
                         max(1, int(settings["cjk_chars"])) if is_cjk(char) else 1 for char in chunk)
        elif kind == "symbol":
            total += max(1, -(-len(chunk) // int(settings["symbol_chars"])))
        else:
            total += max(1, -(-len(chunk) // 4))
    return total + special_count


def exact_count(text: str, profile: str, tokenizer_command: str | None) -> tuple[int | None, str]:
    if tokenizer_command:
        import subprocess
        completed = subprocess.run(
            tokenizer_command, shell=True, input=text, text=True,
            capture_output=True, check=False, timeout=20,
        )
        if completed.returncode != 0:
            raise ValueError(f"tokenizer command failed: {completed.stderr.strip()}")
        return int(completed.stdout.strip().splitlines()[0]), "external-tokenizer-command"
    try:
        import tiktoken
    except ImportError:
        return None, "unavailable"
    encoding_name = {
        "openai-cl100k": "cl100k_base",
        "openai-o200k": "o200k_base",
        "gpt2": "gpt2",
    }.get(profile, "cl100k_base")
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text, disallowed_special=())), f"tiktoken:{encoding_name}"


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
                  budget_exceeded: bool = False, profile: str = "generic") -> dict:
    kept_ranges = to_ranges(kept)
    omitted = set(range(1, len(lines) + 1)) - kept
    omitted_ranges = to_ranges(omitted)
    kept_text = line_text(lines, kept)
    original_text = "\n".join(lines)
    original_estimate = estimate_v2(original_text, profile)
    compact_estimate = estimate_v2(kept_text, profile)
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
            "method": "content_class_pretoken_heuristic_v2",
            "profile": profile,
            "original_estimate": original_estimate,
            "compact_estimate": compact_estimate,
            "chars_over_4_original": chars_over_four(original_text),
            "chars_over_4_compact": chars_over_four(kept_text),
            "saved_estimate": saved,
            "saved_percent": round(100 * saved / original_estimate, 2) if original_estimate else 0.0,
            "v1_legacy": {
                "method": "dependency_free_run_heuristic_v1",
                "original_estimate": estimate(original_text),
                "compact_estimate": estimate(kept_text),
            },
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


SECTION_ORDER = {"prefix": 0, "working": 1, "history": 2, "tail": 3}
PRIORITY_DROP_ORDER = {"optional": 0, "useful": 1, "required": 2}


def plan_envelope(envelope: dict) -> dict:
    window = int(envelope.get("window_tokens", 0))
    output_reserve = int(envelope.get("output_reserve", 0))
    reasoning_reserve = int(envelope.get("reasoning_reserve", 0))
    tool_schema = int(envelope.get("tool_schema_tokens", 0))
    cache_min = int(envelope.get("cache_min_tokens", 0))
    items = envelope.get("items", [])
    if window <= 0:
        raise ValueError("window_tokens must be positive")
    if not isinstance(items, list):
        raise ValueError("items must be a list")
    for index, item in enumerate(items):
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise ValueError(f"item {index}: missing string id")
        if int(item.get("tokens", 0)) < 0:
            raise ValueError(f"item {item['id']}: tokens must be non-negative")
        if item.get("section", "working") not in SECTION_ORDER:
            raise ValueError(f"item {item['id']}: invalid section")
        if item.get("priority", "useful") not in PRIORITY_DROP_ORDER:
            raise ValueError(f"item {item['id']}: invalid priority")
        if item.get("stability", "dynamic") not in {"static", "dynamic"}:
            raise ValueError(f"item {item['id']}: invalid stability")

    ordered = sorted(enumerate(items), key=lambda pair: (SECTION_ORDER[pair[1].get("section", "working")], pair[0]))
    available_input = window - output_reserve - reasoning_reserve
    if available_input < 0:
        raise ValueError("output and reasoning reserves exceed the context window")
    item_budget = max(0, available_input - tool_schema)

    required = [pair for pair in ordered if pair[1].get("priority", "useful") == "required"]
    optional = [pair for pair in ordered if pair[1].get("priority", "useful") == "optional"]
    useful = [pair for pair in ordered if pair[1].get("priority", "useful") == "useful"]
    kept_ids = {pair[1]["id"] for pair in required}
    used = sum(int(pair[1].get("tokens", 0)) for pair in required)
    for group in (optional, useful):
        for _, item in group:
            cost = int(item.get("tokens", 0))
            if used + cost <= item_budget:
                kept_ids.add(item["id"])
                used += cost
    warnings = []
    if used > item_budget:
        warnings.append("required_items_exceed_budget")
    if tool_schema > available_input:
        warnings.append("tool_schema_exceeds_available_input")

    decisions = []
    seen_dynamic = False
    cache_prefix_tokens = 0
    cache_fragmented = False
    input_estimate = tool_schema
    for _, item in ordered:
        kept = item["id"] in kept_ids
        static = item.get("stability", "dynamic") == "static"
        cacheable = kept and static and not seen_dynamic
        if static and seen_dynamic and kept:
            cache_fragmented = True
        if not static:
            seen_dynamic = True
        if cacheable:
            cache_prefix_tokens += int(item.get("tokens", 0))
        if kept:
            input_estimate += int(item.get("tokens", 0))
        reason = "kept_required" if item.get("priority", "useful") == "required" else (
            "kept_within_budget" if kept else "deferred_by_budget")
        decisions.append({
            "id": item["id"],
            "section": item.get("section", "working"),
            "tokens": int(item.get("tokens", 0)),
            "priority": item.get("priority", "useful"),
            "stability": item.get("stability", "dynamic"),
            "decision": "keep" if kept else "defer",
            "reason": reason,
            "cacheable_prefix": cacheable,
            "recover": None if kept else f"restore item {item['id']} from its source",
        })
    cache_prefix_tokens += tool_schema
    cache_eligible = cache_min > 0 and cache_prefix_tokens >= cache_min
    if cache_min > 0 and not cache_eligible:
        warnings.append("cache_prefix_below_minimum")
    if cache_fragmented:
        warnings.append("cache_prefix_fragmented_by_dynamic_item")

    projected_total = input_estimate + output_reserve + reasoning_reserve
    return {
        "tool": "RSaver",
        "version": VERSION,
        "budget": {
            "window_tokens": window,
            "output_reserve": output_reserve,
            "reasoning_reserve": reasoning_reserve,
            "tool_schema_tokens": tool_schema,
            "available_input": available_input,
            "item_budget": item_budget,
            "input_estimate": input_estimate,
            "cacheable_prefix_estimate": cache_prefix_tokens,
            "ordinary_input_estimate": input_estimate - cache_prefix_tokens,
            "projected_total": projected_total,
            "headroom": window - projected_total,
        },
        "cache": {
            "minimum_tokens": cache_min,
            "eligible": cache_eligible,
            "contiguous_static_prefix": not cache_fragmented,
        },
        "decisions": decisions,
        "deferred_count": sum(1 for decision in decisions if decision["decision"] == "defer"),
        "warnings": warnings,
        "estimate_method": "caller_supplied_token_counts",
    }


def command_gate(args: argparse.Namespace) -> int:
    source = Path(args.envelope).read_text(encoding="utf-8") if args.envelope != "-" else sys.stdin.read()
    envelope = json.loads(source)
    plan = plan_envelope(envelope)
    if args.json:
        print(json.dumps(plan, indent=2, sort_keys=True))
        return 0
    budget = plan["budget"]
    print(f"RSaver Gate: input={budget['input_estimate']} cacheable={budget['cacheable_prefix_estimate']} "
          f"ordinary={budget['ordinary_input_estimate']} output_reserve={budget['output_reserve']} "
          f"reasoning_reserve={budget['reasoning_reserve']} projected={budget['projected_total']}/{budget['window_tokens']} "
          f"headroom={budget['headroom']}")
    print(f"RSaver Gate: kept={len(plan['decisions']) - plan['deferred_count']} deferred={plan['deferred_count']} "
          f"cache_eligible={plan['cache']['eligible']}")
    for warning in plan["warnings"]:
        print(f"RSaver WARNING: {warning}", file=sys.stderr)
    return 0


def command_budget(args: argparse.Namespace) -> int:
    window = args.window
    output_reserve = args.output_reserve
    reasoning_reserve = args.reasoning_reserve
    available = window - output_reserve - reasoning_reserve
    if available < 0:
        raise ValueError("output and reasoning reserves exceed the context window")
    result = {
        "tool": "RSaver", "version": VERSION,
        "window_tokens": window,
        "output_reserve": output_reserve,
        "reasoning_reserve": reasoning_reserve,
        "tool_schema_tokens": args.tool_schema,
        "available_input": available,
        "item_budget": max(0, available - args.tool_schema),
        "reserve_percent": round(100 * (output_reserve + reasoning_reserve) / window, 2),
    }
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"RSaver Budget: window={window} output={output_reserve} reasoning={reasoning_reserve} "
              f"tool_schema={args.tool_schema} available_input={available} item_budget={result['item_budget']}")
    return 0


def command_measure(args: argparse.Namespace) -> int:
    rows = []
    for path in args.paths:
        lines = read_lines(path)
        text = "\n".join(lines)
        exact, source = (None, "not requested")
        if getattr(args, "exact", False) or getattr(args, "tokenizer_command", None):
            exact, source = exact_count(text, args.profile, getattr(args, "tokenizer_command", None))
        rows.append({
            "path": path,
            "lines": len(lines),
            "estimate": estimate_v2(text, args.profile),
            "v1_legacy": estimate(text),
            "chars_over_4": chars_over_four(text),
            "exact": exact,
            "exact_source": source,
        })
    total_estimate = sum(row["estimate"] for row in rows)
    if args.json:
        print(json.dumps({"estimate_method": "content_class_pretoken_heuristic_v2",
                          "profile": args.profile, "files": rows,
                          "total_estimate": total_estimate}, indent=2, sort_keys=True))
    else:
        for row in rows:
            exact_text = str(row["exact"]) if row["exact"] is not None else "unavailable"
            print(f"{row['path']}: lines={row['lines']} estimate_v2={row['estimate']} "
                  f"v1={row['v1_legacy']} chars/4={row['chars_over_4']} exact={exact_text} ({row['exact_source']})")
        print(f"TOTAL estimate_v2={total_estimate} (heuristic; exact only when a tokenizer is available)")
    return 0


def command_compare(args: argparse.Namespace) -> int:
    rows = []
    for path in args.paths:
        text = "\n".join(read_lines(path))
        v1 = estimate(text)
        v2 = estimate_v2(text, args.profile)
        chars = chars_over_four(text)
        exact, source = exact_count(text, args.profile, args.tokenizer_command)
        rows.append({
            "path": path,
            "v1_legacy": v1,
            "v2_heuristic": v2,
            "chars_over_4": chars,
            "exact": exact,
            "exact_source": source,
            "v2_error_percent": round(100 * (v2 - exact) / exact, 2) if exact else None,
            "v1_error_percent": round(100 * (v1 - exact) / exact, 2) if exact else None,
            "chars_error_percent": round(100 * (chars - exact) / exact, 2) if exact else None,
        })
    if args.json:
        print(json.dumps({"profile": args.profile, "rows": rows}, indent=2, sort_keys=True))
    else:
        for row in rows:
            exact_text = str(row["exact"]) if row["exact"] is not None else "unavailable"
            v2_error = f"{row['v2_error_percent']}%" if row["v2_error_percent"] is not None else "n/a"
            print(f"{row['path']}: exact={exact_text} ({row['exact_source']}) v2={row['v2_heuristic']} "
                  f"error={v2_error} v1={row['v1_legacy']} chars/4={row['chars_over_4']}")
        if all(row["exact"] is None for row in rows):
            print("Exact counts unavailable; install tiktoken or pass --tokenizer-command to calibrate.")
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
    manifest = make_manifest(args.path, lines, matched, selected, args.match, "bounded_symbol_select",
                             budget_exceeded, args.profile)
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
    manifest = make_manifest(args.path, lines, critical, kept, args.critical, "structure_preserving_prune",
                             budget_exceeded, args.profile)
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
    original_estimate = estimate_v2(original_text, args.profile)
    deduped_estimate = estimate_v2(deduped_text, args.profile)
    saved = original_estimate - deduped_estimate
    stats = {
        "method": "content_class_pretoken_heuristic_v2",
        "profile": args.profile,
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

    gate = sub.add_parser("gate", help="filter a context envelope against input/cache/output budgets")
    gate.add_argument("envelope", help="JSON envelope path, or - for stdin")
    gate.add_argument("--json", action="store_true")
    gate.set_defaults(func=command_gate)

    budget = sub.add_parser("budget", help="allocate a context window across input, output, and reasoning")
    budget.add_argument("--window", type=int, required=True)
    budget.add_argument("--output-reserve", type=int, default=4096)
    budget.add_argument("--reasoning-reserve", type=int, default=8192)
    budget.add_argument("--tool-schema", type=int, default=0)
    budget.add_argument("--json", action="store_true")
    budget.set_defaults(func=command_budget)

    measure = sub.add_parser("measure", help="estimate the size of files or stdin")
    measure.add_argument("paths", nargs="+")
    measure.add_argument("--profile", choices=sorted(PROFILES), default="generic")
    measure.add_argument("--exact", action="store_true", help="use tiktoken when available")
    measure.add_argument("--tokenizer-command", help="shell command that reads text on stdin and prints a token count")
    measure.add_argument("--json", action="store_true", help="emit JSON instead of text")
    measure.set_defaults(func=command_measure)

    compare = sub.add_parser("compare", help="compare heuristic estimates with an exact tokenizer")
    compare.add_argument("paths", nargs="+")
    compare.add_argument("--profile", choices=sorted(PROFILES), default="generic")
    compare.add_argument("--tokenizer-command", help="shell command that reads text on stdin and prints a token count")
    compare.add_argument("--json", action="store_true")
    compare.set_defaults(func=command_compare)

    select = sub.add_parser("select", help="extract bounded line ranges around matches")
    select.add_argument("path")
    select.add_argument("--match", required=True, help="regular expression selecting anchor lines")
    select.add_argument("--context", type=int, default=2)
    select.add_argument("--max-lines", type=int, default=120)
    select.add_argument("--profile", choices=sorted(PROFILES), default="generic")
    select.add_argument("--json", action="store_true")
    select.set_defaults(func=command_select)

    compact = sub.add_parser("compact", help="prune non-critical context while preserving evidence")
    compact.add_argument("path")
    compact.add_argument("--max-lines", type=int, default=120)
    compact.add_argument("--head", type=int, default=8)
    compact.add_argument("--tail", type=int, default=8)
    compact.add_argument("--critical", default=DEFAULT_CRITICAL)
    compact.add_argument("--profile", choices=sorted(PROFILES), default="generic")
    compact.add_argument("--manifest", help="write the recoverability manifest to this path")
    compact.add_argument("--verify", action="store_true", help="verify the manifest against the original before output")
    compact.add_argument("--json", action="store_true")
    compact.set_defaults(func=command_compact)

    dedupe = sub.add_parser("dedupe", help="collapse exact repeated non-critical lines")
    dedupe.add_argument("paths", nargs="+")
    dedupe.add_argument("--critical", default=DEFAULT_CRITICAL)
    dedupe.add_argument("--profile", choices=sorted(PROFILES), default="generic")
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
