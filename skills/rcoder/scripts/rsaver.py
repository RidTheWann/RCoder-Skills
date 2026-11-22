#!/usr/bin/env python3
"""RSaver: evidence-preserving context reduction with a recoverable manifest.

RSaver prunes or deduplicates context instead of rewriting it. Retained lines are
copied verbatim, and every omitted range is recorded so it can be recovered
exactly. Token figures are deterministic dependency-free estimates for relative
comparison only, not model billing or hard context-limit measurements.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import sys
import zlib
from pathlib import Path

VERSION = "1.11.0"
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
NORMALIZE_RE = (
    (re.compile(r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?\b"), "<TIMESTAMP>"),
    (re.compile(r"\b\d{2}:\d{2}:\d{2}(?:\.\d+)?\b"), "<TIME>"),
    (re.compile(r"\b0x[0-9a-fA-F]+\b"), "<HEX>"),
    (re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"), "<UUID>"),
    (re.compile(r"\b\d+\b"), "<N>"),
)


def normalize_template(line: str) -> str:
    template = line
    for pattern, placeholder in NORMALIZE_RE:
        template = pattern.sub(placeholder, template)
    return template


class MarkerFactory:
    """Emits marker strings that cannot collide with existing content."""

    def __init__(self, source: str) -> None:
        self.source = source
        self.used: set[str] = set()
        self.counter = 0

    def make(self, label: str) -> str:
        while True:
            marker = f"[RSaver#{self.counter}: {label}]"
            self.counter += 1
            if marker not in self.source and marker not in self.used:
                self.used.add(marker)
                return marker


def collapse_phrase_repeats(text: str, profile: str = "generic", min_chars: int = 4, min_repeats: int = 2) -> tuple[str, list[dict]]:
    n = len(text)
    markers = MarkerFactory(text)
    i = 0
    result: list[str] = []
    collapsed: list[dict] = []
    while i < n:
        best_l = 0
        best_k = 1
        for l in range(min_chars, min(1000, (n - i) // 2 + 1)):
            sub = text[i:i + l]
            if not sub.strip():
                continue
            k = 1
            j = i + l
            while j + l <= n and text[j:j + l] == sub:
                k += 1
                j += l
            if k >= min_repeats and (k * l) > (best_k * best_l):
                best_l = l
                best_k = k
        if best_k >= min_repeats and best_l >= min_chars:
            unit = text[i:i + best_l]
            marker = markers.make(f"repeat x{best_k - 1}")
            if estimate_v2(marker, profile) < (best_k - 1) * estimate_v2(unit, profile):
                result.append(unit)
                result.append(marker)
                collapsed.append({"marker": marker, "omitted": unit * (best_k - 1)})
                i += best_k * best_l
                continue
        result.append(text[i])
        i += 1
    return "".join(result), collapsed


def collapse_command_blocks(lines: list[str], normalize: bool = False) -> tuple[list[str], list[dict]]:
    n = len(lines)
    norm_lines = [normalize_template(l) if normalize else l for l in lines]
    markers = MarkerFactory("\n".join(lines))
    output: list[str] = []
    collapsed: list[dict] = []
    i = 0
    while i < n:
        best_b = 0
        best_repeats = 1
        for b in range(2, min(25, (n - i) // 2 + 1)):
            pattern = norm_lines[i:i + b]
            repeats = 1
            j = i + b
            while j + b <= n and norm_lines[j:j + b] == pattern:
                repeats += 1
                j += b
            if repeats > 1 and (repeats * b) > (best_repeats * best_b):
                best_b = b
                best_repeats = repeats
        if best_repeats > 1 and best_b >= 2:
            for line in lines[i:i + best_b]:
                output.append(line)
            start_orig = i + best_b + 1
            end_orig = i + best_b * best_repeats
            marker = markers.make(f"block {best_b} lines repeated x{best_repeats - 1} orig {start_orig}-{end_orig}")
            output.append(marker)
            omitted = "\n".join(lines[i + best_b:i + best_b * best_repeats])
            collapsed.append({"marker": marker, "omitted": omitted})
            i += best_b * best_repeats
        else:
            output.append(lines[i])
            i += 1
    return output, collapsed


def _reference_prefix(text: str) -> str:
    """Pick a marker prefix that cannot collide with literal text already in the payload."""
    for prefix in ("@", "\u00a7", "\u00b6", "\u2021", "\u00b5", "\u203b"):
        if prefix not in text:
            return prefix
    # Fall back to a rare multi-char sentinel rather than emitting an ambiguous marker.
    index = 0
    while True:
        sentinel = f"\u00a7\u00a7{index}\u00a7\u00a7"
        if sentinel not in text:
            return sentinel
        index += 1


def dedupe_frequency_dict(text: str, profile: str = "generic", min_chars: int = 4, min_occurrences: int = 2) -> tuple[str, dict]:
    from collections import Counter
    words = re.findall(r"\b[A-Za-z0-9_/-]{4,}\b", text)
    word_counts = Counter(words)
    phrases = Counter()
    for line in text.splitlines():
        line_words = re.findall(r"\b[A-Za-z0-9_/-]{3,}\b", line)
        for n in range(2, 7):
            for i in range(len(line_words) - n + 1):
                p = " ".join(line_words[i:i + n])
                if len(p) >= 8 and p in line:
                    phrases[p] += 1

    candidates = {}
    for item, c in list(phrases.items()) + list(word_counts.items()):
        if c >= min_occurrences and item in text:
            cost = estimate_v2(item, profile)
            savings = (c - 1) * cost - 1
            if savings > 0:
                candidates[item] = (c, savings)

    sorted_items = sorted(candidates.keys(), key=lambda x: (len(x), candidates[x][1]), reverse=True)
    prefix = _reference_prefix(text)
    dictionary: dict[str, str] = {}
    deduped = text
    ref_idx = 0
    for item in sorted_items:
        if deduped.count(item) >= min_occurrences:
            ref = f"{prefix}{ref_idx}"
            ref_idx += 1
            dictionary[ref] = item
            parts = deduped.split(item)
            deduped = parts[0] + item + ref.join(parts[1:])
    return deduped, dictionary


def restore_words_and_blocks(payload: str, dictionary: dict = None, blocks: list[dict] = None, inline_repeats: list[dict] = None) -> str:
    restored = payload
    if dictionary:
        for ref in sorted(dictionary.keys(), key=lambda r: int(r[1:]) if r[1:].isdigit() else 0, reverse=True):
            restored = restored.replace(ref, dictionary[ref])
    if inline_repeats:
        for item in inline_repeats:
            restored = restored.replace(item["marker"], item["omitted"])
    if blocks:
        for item in blocks:
            restored = restored.replace(item["marker"], item["omitted"])
    return restored


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
OBJECTIVE_RE = re.compile(r"(?i)\b(objective|goal)\s*:")
CONSTRAINT_RE = re.compile(r"(?i)\b(constraint|must not|do not|authorization|scope)\b")
OPEN_RE = re.compile(r"(?i)\b(unknown|unverified|not verified|hypothesis|tbd)\b")
COMPLETE_RE = re.compile(r"(?i)\b(done|complete|finished|all tests pass)\b")
EVIDENCE_RE = re.compile(r"(?i)\b(confirmed|proved|verified)\b")
LABEL_RE = re.compile(r"(?i)\b(VERIFIED|INFERRED|NOT VERIFIED)\b")


def detect_drift(lines: list[str], recent_window: int, repeat_threshold: int) -> dict:
    signals = []
    recent = lines[-recent_window:] if recent_window > 0 else lines
    recent_start = max(1, len(lines) - len(recent) + 1)
    if not any(OBJECTIVE_RE.search(line) for line in recent):
        signals.append({"signal": "objective_absent_from_recent_window", "severity": "high",
                        "lines": [], "action": "re-anchor the objective at the start and end of the next request"})
    if not any(CONSTRAINT_RE.search(line) for line in recent):
        signals.append({"signal": "constraint_absent_from_recent_window", "severity": "high",
                        "lines": [], "action": "restate hard constraints with exact IDs"})
    commands: dict[str, list[int]] = {}
    for offset, line in enumerate(recent):
        stripped = line.strip()
        if stripped.startswith(("$ ", "CMD ", "RUN ", "TOOL ", "CALL ", "READ ")):
            commands.setdefault(stripped, []).append(recent_start + offset)
    for command, locations in commands.items():
        if len(locations) >= repeat_threshold:
            signals.append({"signal": "repeated_command", "severity": "medium",
                            "lines": locations, "command": command,
                            "action": "stop repeating and record the result before the next attempt"})
    open_lines = [recent_start + offset for offset, line in enumerate(recent) if OPEN_RE.search(line)]
    complete_lines = [recent_start + offset for offset, line in enumerate(recent) if COMPLETE_RE.search(line)]
    if open_lines and complete_lines:
        signals.append({"signal": "completion_claim_with_open_unknowns", "severity": "high",
                        "lines": complete_lines + open_lines,
                        "action": "separate confirmed results from unresolved hypotheses"})
    unlabeled = [recent_start + offset for offset, line in enumerate(recent)
                 if EVIDENCE_RE.search(line) and not LABEL_RE.search(line)]
    if unlabeled:
        signals.append({"signal": "unlabeled_confidence_claim", "severity": "low",
                        "lines": unlabeled, "action": "label each claim VERIFIED, INFERRED, or NOT VERIFIED"})
    return {
        "tool": "RSaver", "version": VERSION, "method": "deterministic_text_signals",
        "lines_scanned": len(lines), "recent_window": len(recent),
        "signals": signals, "signal_count": len(signals),
        "diagnosis": "NOT VERIFIED: signals are heuristics, not a model state diagnosis",
    }


def build_anchor(state: dict, max_tokens: int) -> dict:
    objective = state.get("objective")
    if not isinstance(objective, str) or not objective.strip():
        raise ValueError("state must contain a non-empty objective")
    constraints = [str(item) for item in state.get("constraints", [])]
    facts = [str(item) for item in state.get("verified_facts", [])]
    decisions = [str(item) for item in state.get("decisions", [])]
    unresolved = [str(item) for item in state.get("unresolved", [])]
    boundary = str(state.get("security_boundary", ""))
    next_action = str(state.get("next_action", ""))
    opening = ["===== RSAVER ANCHOR START =====",
               "[RSAVER: refer to items by ID, not by position in the context]",
               f"[OBJECTIVE-1] {objective.strip()}"]
    for index, item in enumerate(constraints[:3], 1):
        opening.append(f"[CONSTRAINT-{index}] {item}")
    if boundary:
        opening.append(f"[SECURITY-BOUNDARY] {boundary}")
    for index, item in enumerate(facts[:5], 1):
        opening.append(f"[FACT-{index}] {item}")
    for index, item in enumerate(decisions[:3], 1):
        opening.append(f"[DECISION-{index}] {item}")
    for index, item in enumerate(unresolved[:3], 1):
        opening.append(f"[UNRESOLVED-{index}] {item}")
    if next_action:
        opening.append(f"[NEXT-ACTION] {next_action}")
    closing = ["===== RSAVER ANCHOR END =====",
               f"[OBJECTIVE-1] {objective.strip()}"]
    for index, item in enumerate(constraints[:3], 1):
        closing.append(f"[CONSTRAINT-{index}] {item}")
    if next_action:
        closing.append(f"[NEXT-ACTION] {next_action}")
    closing.append("===== END ANCHOR =====")
    block = "\n".join(opening + closing)
    warnings = []
    if len(constraints) > 3:
        warnings.append("too_many_repeated_constraints")
    used = estimate_v2(block)
    if used > max_tokens:
        warnings.append("anchor_exceeds_budget")
    return {
        "tool": "RSaver", "version": VERSION, "method": "dual_end_explicit_id_anchor",
        "block": block, "opening": "\n".join(opening), "closing": "\n".join(closing),
        "estimate": used, "max_tokens": max_tokens, "warnings": warnings,
        "ids": [f"OBJECTIVE-1"] + [f"CONSTRAINT-{i}" for i in range(1, min(len(constraints), 3) + 1)]
        + [f"FACT-{i}" for i in range(1, min(len(facts), 5) + 1)]
        + [f"DECISION-{i}" for i in range(1, min(len(decisions), 3) + 1)]
        + [f"UNRESOLVED-{i}" for i in range(1, min(len(unresolved), 3) + 1)]
        + (["NEXT-ACTION"] if next_action else []),
    }


BILLING_CAVEAT = (
    "RSaver cannot zero, reverse, or refund provider billing. Token charges are determined "
    "by the provider; use this evidence only under the provider's published support policy."
)


def command_pack(args: argparse.Namespace) -> int:
    text = sys.stdin.read() if args.path == "-" else Path(args.path).read_text(encoding="utf-8", errors="replace")
    original_estimate = estimate_v2(text, args.profile)
    method = getattr(args, "method", "zlib")
    dictionary = {}
    inline_repeats = []
    blocks = []
    if method == "dict":
        working_text = text
        if "\n" in text:
            block_lines, blocks = collapse_command_blocks(text.splitlines())
            has_trailing_nl = text.endswith("\n")
            working_text = "\n".join(block_lines) + ("\n" if has_trailing_nl else "")
        working_text, inline_repeats = collapse_phrase_repeats(working_text, profile=args.profile)
        payload, dictionary = dedupe_frequency_dict(working_text, profile=args.profile)
        packed_estimate = estimate_v2(payload, args.profile)
        worthwhile = packed_estimate < original_estimate
        saved = original_estimate - packed_estimate
        pack_method = "frequency_dict_zero_dup"
    else:
        payload = base64.b64encode(zlib.compress(text.encode("utf-8"), 9)).decode("ascii")
        packed_estimate = estimate_v2(payload, args.profile)
        worthwhile = packed_estimate < original_estimate
        saved = original_estimate - packed_estimate
        pack_method = "zlib9_base64_roundtrip"
    result = {
        "tool": "RSaver", "version": VERSION, "method": pack_method,
        "source": args.path, "original_sha256": sha256_text(text),
        "original_chars": len(text), "compressed_chars": len(payload),
        "original_estimate": original_estimate, "packed_estimate": packed_estimate,
        "saved_estimate": saved,
        "saved_percent": round(100 * saved / original_estimate, 2) if original_estimate else 0.0,
        "worthwhile": worthwhile, "payload": payload,
        "billing_note": BILLING_CAVEAT,
    }
    if dictionary:
        result["dictionary"] = dictionary
    if blocks:
        result["blocks"] = blocks
    if inline_repeats:
        result["inline_repeats"] = inline_repeats
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        if worthwhile or args.force:
            print(payload)
            print(f"RSaver pack ({pack_method}): {original_estimate} -> {packed_estimate} estimate", file=sys.stderr)
        else:
            print(text)
            print("RSaver pack: packed form costs more; original kept (use --force to emit anyway)",
                  file=sys.stderr)
    return 0


def command_unpack(args: argparse.Namespace) -> int:
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    method = manifest.get("method")
    if method == "zlib9_base64_roundtrip":
        text = zlib.decompress(base64.b64decode(manifest["payload"])).decode("utf-8")
    elif method == "frequency_dict_zero_dup":
        text = restore_words_and_blocks(
            manifest["payload"],
            dictionary=manifest.get("dictionary"),
            blocks=manifest.get("blocks"),
            inline_repeats=manifest.get("inline_repeats"),
        )
    else:
        raise ValueError("unsupported pack method")
    if sha256_text(text) != manifest.get("original_sha256"):
        raise ValueError("original hash mismatch after unpack")
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"RSaver unpack: restored {len(text)} characters to {args.out}")
    elif args.json:
        print(json.dumps({"text": text, "verified": True}, sort_keys=True))
    else:
        print(text)
    return 0


def matching_lines(lines: list[str], needles: list[str]) -> list[dict]:
    return [{"line": index, "text": line}
            for index, line in enumerate(lines, 1)
            if any(needle in line for needle in needles)]


def command_crosscheck(args: argparse.Namespace) -> int:
    expected = json.loads(Path(args.expect).read_text(encoding="utf-8"))
    diff_lines = read_lines(args.diff) if args.diff else []
    test_lines = read_lines(args.test_log) if args.test_log else []
    claim_lines = read_lines(args.claim) if args.claim else []
    checks = []
    required = [str(item) for item in expected.get("required_files", [])]
    forbidden = [str(item) for item in expected.get("forbidden_paths", [])]
    required_hits = matching_lines(diff_lines, required) if required else []
    missing = [path for path in required if not any(path in hit["text"] for hit in required_hits)]
    checks.append({
        "id": "required_edits",
        "status": "pass" if required and not missing else ("unverified" if not required else "fail"),
        "evidence": required_hits, "missing": missing,
    })
    forbidden_hits = matching_lines(diff_lines, forbidden) if forbidden else []
    checks.append({
        "id": "scope_boundary",
        "status": "pass" if not forbidden_hits else "fail",
        "evidence": forbidden_hits,
    })
    failure_markers = [str(item) for item in expected.get("failure_markers", ["FAIL", "ERROR", "Traceback"])]
    success_markers = [str(item) for item in expected.get("success_markers", ["PASS", "ok"])]
    failures = matching_lines(test_lines, failure_markers)
    successes = matching_lines(test_lines, success_markers)
    checks.append({
        "id": "test_result",
        "status": "fail" if failures else ("pass" if successes else "unverified"),
        "evidence": failures or successes,
    })
    completion = matching_lines(claim_lines, ["done", "complete", "finished", "success"])
    inconsistent = bool(completion and any(item["status"] == "fail" for item in checks))
    checks.append({
        "id": "claim_consistency",
        "status": "fail" if inconsistent else ("unverified" if not completion else "pass"),
        "evidence": completion,
    })
    usage = None
    if args.usage:
        raw = json.loads(Path(args.usage).read_text(encoding="utf-8"))
        usage = {
            "input_tokens": raw.get("input_tokens", raw.get("prompt_tokens")),
            "output_tokens": raw.get("output_tokens", raw.get("completion_tokens")),
            "cached_tokens": raw.get("input_tokens_details", {}).get("cached_tokens"),
            "reasoning_tokens": raw.get("output_tokens_details", {}).get("reasoning_tokens"),
            "source": "provider usage file",
            "billing_effect": "NOT CHANGED by RSaver",
        }
    statuses = {item["status"] for item in checks}
    verdict = "FAIL" if "fail" in statuses else ("UNVERIFIED" if "unverified" in statuses else "PASS")
    report = {
        "tool": "RSaver", "version": VERSION, "method": "deterministic_artifact_crosscheck",
        "verdict": verdict, "checks": checks, "usage": usage,
        "billing_note": BILLING_CAVEAT,
        "evidence_pack": "\n".join(
            [f"objective: {expected.get('objective', 'not supplied')}", f"verdict: {verdict}"]
            + [f"{item['id']}: {item['status']}" for item in checks]
        ),
    }
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"RSaver crosscheck: {verdict}")
        for item in checks:
            print(f"  {item['id']}: {item['status']} ({len(item['evidence'])} evidence line(s))")
        print("RSaver billing: " + BILLING_CAVEAT, file=sys.stderr)
    return 0


def command_drift(args: argparse.Namespace) -> int:
    lines = read_lines(args.path)
    report = detect_drift(lines, args.recent_window, args.repeat_threshold)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"RSaver drift: {report['signal_count']} signal(s) in {report['lines_scanned']} lines")
        for signal in report["signals"]:
            print(f"  [{signal['severity']}] {signal['signal']} lines={signal['lines']}")
        print("RSaver drift: heuristic signals only; NOT a model state diagnosis")
    return 0


def command_anchor(args: argparse.Namespace) -> int:
    state = json.loads(Path(args.state).read_text(encoding="utf-8") if args.state != "-" else sys.stdin.read())
    result = build_anchor(state, args.max_tokens)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(result["block"])
        print(f"RSaver anchor: estimate={result['estimate']}/{result['max_tokens']} ids={len(result['ids'])}",
              file=sys.stderr)
        for warning in result["warnings"]:
            print(f"RSAVER WARNING: {warning}", file=sys.stderr)
    return 0


def command_reanchor(args: argparse.Namespace) -> int:
    state = json.loads(Path(args.state).read_text(encoding="utf-8"))
    envelope = json.loads(Path(args.envelope).read_text(encoding="utf-8"))
    anchor = build_anchor(state, args.max_tokens)
    items = list(envelope.get("items", []))
    items.insert(0, {"id": "rsaver-anchor-start", "section": "prefix", "tokens": estimate_v2(anchor["opening"]),
                     "stability": "static", "priority": "required"})
    items.append({"id": "rsaver-anchor-end", "section": "tail", "tokens": estimate_v2(anchor["closing"]),
                  "stability": "dynamic", "priority": "required"})
    envelope = dict(envelope)
    envelope["items"] = items
    plan = plan_envelope(envelope)
    result = {"tool": "RSaver", "version": VERSION, "method": "reanchor_then_gate",
              "anchor": anchor, "gate": plan,
              "warnings": anchor["warnings"] + plan["warnings"]}
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        budget = plan["budget"]
        print(f"RSaver re-anchor: anchor={anchor['estimate']} input={budget['input_estimate']} "
              f"projected={budget['projected_total']}/{budget['window_tokens']} "
              f"deferred={plan['deferred_count']} cache_eligible={plan['cache']['eligible']}")
        for warning in result["warnings"]:
            print(f"RSAVER WARNING: {warning}", file=sys.stderr)
    return 0


def plan_envelope(envelope: dict) -> dict:
    window = int(envelope.get("window_tokens", 0))
    output_reserve = int(envelope.get("output_reserve", 0))
    reasoning_reserve = int(envelope.get("reasoning_reserve", 0))
    tool_schema = int(envelope.get("tool_schema_tokens", 0))
    cache_min = int(envelope.get("cache_min_tokens", 0))
    profile = envelope.get("profile", "generic")
    items = envelope.get("items", [])
    if window <= 0:
        raise ValueError("window_tokens must be positive")
    if not isinstance(items, list):
        raise ValueError("items must be a list")
    for index, item in enumerate(items):
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise ValueError(f"item {index}: missing string id")
        if item.get("tokens") is None and "text" in item:
            item["tokens"] = estimate_v2(str(item["text"]), profile)
        elif item.get("tokens") is None:
            item["tokens"] = 0
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
    target_savings = getattr(args, "target_savings", 0.0)
    if target_savings > 0.0:
        orig_text = "\n".join(lines)
        orig_est = estimate_v2(orig_text, args.profile)
        max_compact_tokens = max(1, int(orig_est * (1.0 - min(target_savings, 99.0) / 100.0)))
        critical_est = estimate_v2(line_text(lines, critical), args.profile)
        budget_exceeded = critical_est > max_compact_tokens
        kept_candidates = set(critical)
        for index in ranked:
            if index in kept_candidates:
                continue
            if len(kept_candidates) >= args.max_lines:
                break
            trial = kept_candidates | {index}
            if estimate_v2(line_text(lines, trial), args.profile) <= max_compact_tokens:
                kept_candidates.add(index)
        kept = kept_candidates
    else:
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
    raw_lines = list(all_lines)
    critical = critical_indices(all_lines, args.critical)
    do_norm = getattr(args, "normalize", False)
    do_blocks = getattr(args, "blocks", False)
    do_words = getattr(args, "words", False)

    blocks: list[dict] = []
    if do_blocks:
        all_lines, blocks = collapse_command_blocks(all_lines, normalize=do_norm)
        critical = critical_indices(all_lines, args.critical)

    counts: dict[str, list[int]] = {}
    samples: dict[str, str] = {}
    for index, line in enumerate(all_lines, 1):
        if index not in critical:
            key = normalize_template(line) if do_norm else line
            counts.setdefault(key, []).append(index)
            if key not in samples:
                samples[key] = line

    def marker_for(key: str, duplicates: list[int]) -> str:
        label = "similar" if do_norm else "identical"
        return f"[RSaver: {len(duplicates) - 1} {label} non-critical line(s) collapsed; original lines {format_indices(duplicates)}]"

    collapse: set[str] = set()
    for key, duplicates in counts.items():
        if len(duplicates) > 1:
            sample_line = samples[key]
            removed = (len(duplicates) - 1) * estimate(sample_line)
            if estimate(marker_for(key, duplicates)) < removed:
                collapse.add(key)
    seen: set[str] = set()
    output: list[str] = []
    for index, line in enumerate(all_lines, 1):
        key = normalize_template(line) if do_norm else line
        if index in critical or key not in collapse:
            output.append(line)
            continue
        if key in seen:
            continue
        seen.add(key)
        output.append(line)
        output.append(marker_for(key, counts[key]))
    deduped_text = "\n".join(output)

    dictionary: dict[str, str] = {}
    inline_repeats: list[dict] = []
    if do_words:
        deduped_text, inline_repeats = collapse_phrase_repeats(deduped_text, profile=args.profile)
        deduped_text, dictionary = dedupe_frequency_dict(deduped_text, profile=args.profile)

    original_text = "\n".join(raw_lines)
    original_estimate = estimate_v2(original_text, args.profile)
    deduped_estimate = estimate_v2(deduped_text, args.profile)
    saved = original_estimate - deduped_estimate
    method = "frequency_dict_zero_dup" if do_words else (
        "command_block_collapse" if do_blocks else (
            "normalized_template_collapse" if do_norm else "exact_duplicate_collapse"
        )
    )
    stats = {
        "method": method,
        "profile": args.profile,
        "original_estimate": original_estimate,
        "deduped_estimate": deduped_estimate,
        "saved_estimate": saved,
        "saved_percent": round(100 * saved / original_estimate, 2) if original_estimate else 0.0,
    }
    manifest = {"tool": "RSaver", "version": VERSION,
                "method": method,
                "inputs": args.paths, "critical_lines_preserved": sorted(critical), "stats": stats}
    if dictionary:
        manifest["dictionary"] = dictionary
    if blocks:
        manifest["blocks"] = blocks
    if inline_repeats:
        manifest["inline_repeats"] = inline_repeats
    return emit(manifest, args.json, deduped_text, "dedupe", "deduped_text")


AUDIT_SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "vendor", "dist", "build", "target", ".venv", "venv",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".next", ".nuxt", ".turbo",
    "coverage", "DerivedData", ".gradle", ".idea", ".ssh", ".aws", ".gnupg", ".kube", ".docker",
}
AUDIT_SECRET_RE = re.compile(
    r"(?i)(^\.env(\..*)?$|^id_(rsa|dsa|ecdsa|ed25519)(\.pub)?$|\.(pem|key|p12|pfx|jks|keystore|kdbx)$|"
    r"^(\.npmrc|\.pypirc|\.netrc|\.git-credentials|credentials|secrets?\.(json|ya?ml|toml))$)"
)
AUDIT_LOCKFILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "cargo.lock", "go.sum", "poetry.lock",
    "pipfile.lock", "composer.lock", "gemfile.lock", "uv.lock", "bun.lockb", "packages.lock.json",
}
AUDIT_ADVICE = {
    "lockfile": "exclude from context; look up one entry with `rsaver select --match <package>`",
    "minified": "never load; read the unminified source instead",
    "generated": "exclude from context; regenerate from the source of truth",
    "log": "`rsaver compact --target-savings 80 --manifest <m.json> --verify` before loading",
    "data": "sample with `rsaver select --match <key>`; do not load the whole file",
    "large-source": "`rsaver select --match <symbol>` for a bounded window instead of the whole file",
    "large-docs": "load one section with `rsaver select --match <heading>`",
}
AUDIT_WASTE = {"lockfile", "minified", "generated", "log", "data"}
AUDIT_IGNORE_PATTERNS = {
    "lockfile": ["package-lock.json", "yarn.lock", "pnpm-lock.yaml", "Cargo.lock", "go.sum", "poetry.lock"],
    "minified": ["*.min.js", "*.min.css", "*.map"],
    "generated": ["*.snap", "*.pb.go", "*_pb2.py", "*.generated.*"],
    "log": ["*.log"],
    "data": ["*.csv", "*.tsv", "*.jsonl", "*.ndjson"],
}


def audit_category(name: str, size: int, large_threshold_bytes: int) -> str:
    lower = name.lower()
    if lower in AUDIT_LOCKFILES:
        return "lockfile"
    if lower.endswith((".min.js", ".min.css", ".map")):
        return "minified"
    if lower.endswith((".snap", ".pb.go", "_pb2.py", ".g.dart")) or ".generated." in lower:
        return "generated"
    if lower.endswith((".log", ".out")):
        return "log"
    if lower.endswith((".csv", ".tsv", ".jsonl", ".ndjson", ".sql")):
        return "data"
    if lower.endswith(".json") and size >= large_threshold_bytes:
        return "data"
    if lower.endswith((".md", ".rst", ".txt")):
        return "large-docs" if size >= large_threshold_bytes else "docs"
    return "large-source" if size >= large_threshold_bytes else "source"


def duplicate_line_upper_bound(text: str, profile: str) -> int:
    """Estimated tokens in repeated non-critical lines beyond their first occurrence (an upper bound)."""
    seen: set[str] = set()
    total = 0
    critical = re.compile(DEFAULT_CRITICAL)
    for line in text.splitlines():
        if not line.strip() or critical.search(line):
            continue
        key = normalize_template(line)
        if key in seen:
            total += estimate_v2(line, profile)
        else:
            seen.add(key)
    return total


def audit_project(root: Path, profile: str, top: int, max_files: int, max_read_bytes: int,
                  large_tokens: int) -> dict:
    """Read-only, bounded project context-cost audit. Never emits file contents."""
    root = root.resolve()
    large_threshold_bytes = large_tokens * 4
    rows: list[dict] = []
    skipped = {"secret": 0, "binary": 0, "symlink": 0, "unreadable": 0}
    truncated = False
    stack = [root]
    scanned = 0
    while stack and not truncated:
        folder = stack.pop()
        try:
            entries = sorted(os.scandir(folder), key=lambda entry: entry.name.lower())
        except OSError:
            skipped["unreadable"] += 1
            continue
        for entry in entries:
            if entry.is_symlink():
                skipped["symlink"] += 1
                continue
            if entry.is_dir(follow_symlinks=False):
                if entry.name not in AUDIT_SKIP_DIRS:
                    stack.append(Path(entry.path))
                continue
            if not entry.is_file(follow_symlinks=False):
                continue
            if AUDIT_SECRET_RE.search(entry.name):
                skipped["secret"] += 1
                continue
            if scanned >= max_files:
                truncated = True
                break
            scanned += 1
            try:
                size = entry.stat(follow_symlinks=False).st_size
                with open(entry.path, "rb") as handle:
                    head = handle.read(4096)
                    if b"\x00" in head:
                        skipped["binary"] += 1
                        continue
                    data = head + handle.read(max(0, max_read_bytes - len(head)))
            except OSError:
                skipped["unreadable"] += 1
                continue
            text = data.decode("utf-8", errors="replace")
            sized_only = size > max_read_bytes
            tokens = (size + 3) // 4 if sized_only else estimate_v2(text, profile)
            category = audit_category(entry.name, size, large_threshold_bytes)
            rows.append({
                "path": Path(entry.path).relative_to(root).as_posix(),
                "bytes": size,
                "tokens": tokens,
                "category": category,
                "size_only_estimate": sized_only,
                "_text": None if sized_only else text,
            })
    rows.sort(key=lambda row: (-row["tokens"], row["path"]))
    total = sum(row["tokens"] for row in rows)
    by_category: dict[str, dict] = {}
    for row in rows:
        bucket = by_category.setdefault(row["category"], {"files": 0, "tokens": 0})
        bucket["files"] += 1
        bucket["tokens"] += row["tokens"]
    top_rows = []
    for row in rows[:top]:
        duplicate = (duplicate_line_upper_bound(row["_text"], profile)
                     if row["_text"] is not None and row["category"] not in AUDIT_WASTE else 0)
        top_rows.append({
            "path": row["path"], "bytes": row["bytes"], "tokens": row["tokens"],
            "share_percent": round(100 * row["tokens"] / total, 2) if total else 0.0,
            "category": row["category"], "size_only_estimate": row["size_only_estimate"],
            "duplicate_line_tokens_upper_bound": duplicate,
            "advice": AUDIT_ADVICE.get(row["category"], "no reduction needed unless it is repeatedly re-read"),
        })
    waste = sum(bucket["tokens"] for name, bucket in by_category.items() if name in AUDIT_WASTE)
    patterns = sorted({pattern for name in by_category if name in AUDIT_WASTE
                       for pattern in AUDIT_IGNORE_PATTERNS.get(name, [])})
    return {
        "tool": "RSaver", "version": VERSION, "command": "audit", "profile": profile,
        "estimate_method": "content_class_pretoken_heuristic_v2",
        "root": str(root), "files_scanned": len(rows), "truncated": truncated,
        "limits": {"max_files": max_files, "max_read_bytes": max_read_bytes, "large_tokens": large_tokens},
        "skipped": skipped, "total_estimate": total,
        "avoidable_estimate": waste,
        "avoidable_percent": round(100 * waste / total, 2) if total else 0.0,
        "by_category": dict(sorted(by_category.items(), key=lambda item: -item[1]["tokens"])),
        "top_files": top_rows,
        "suggested_exclusions": patterns,
        "note": ("Relative estimates only, not provider billing. File contents are never printed. "
                 "avoidable_estimate counts categories that are rarely worth loading whole."),
    }


def command_audit(args: argparse.Namespace) -> int:
    root = Path(args.root)
    if not root.is_dir():
        raise ValueError(f"--root is not a directory: {args.root}")
    report = audit_project(root, args.profile, args.top, args.max_files, args.max_read_bytes,
                           args.large_tokens)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    print(f"RSaver audit: {report['files_scanned']} files, ~{report['total_estimate']} tokens "
          f"({'truncated at --max-files' if report['truncated'] else 'complete'})")
    print(f"Avoidable if excluded or reduced: ~{report['avoidable_estimate']} tokens "
          f"({report['avoidable_percent']}%)")
    print("By category:")
    for name, bucket in report["by_category"].items():
        print(f"  {name}: files={bucket['files']} tokens={bucket['tokens']}")
    print(f"Top {len(report['top_files'])} files:")
    for row in report["top_files"]:
        print(f"  {row['tokens']:>8} {row['share_percent']:>6}%  {row['path']}  [{row['category']}]")
        print(f"           -> {row['advice']}")
    if report["suggested_exclusions"]:
        print("Suggested exclusions: " + ", ".join(report["suggested_exclusions"]))
    print(report["note"])
    return 0



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

    pack = sub.add_parser("pack", help="compress text when the packed estimate is actually smaller")
    pack.add_argument("path")
    pack.add_argument("--profile", choices=sorted(PROFILES), default="generic")
    pack.add_argument("--method", choices=["zlib", "dict"], default="zlib", help="pack method: zlib (binary) or dict (readable frequency dictionary)")
    pack.add_argument("--force", action="store_true", help="emit the packed form even when it costs more")
    pack.add_argument("--json", action="store_true")
    pack.set_defaults(func=command_pack)

    unpack = sub.add_parser("unpack", help="restore exact text from a pack manifest")
    unpack.add_argument("--manifest", required=True)
    unpack.add_argument("--out", help="write restored text to this file")
    unpack.add_argument("--json", action="store_true")
    unpack.set_defaults(func=command_unpack)

    crosscheck = sub.add_parser("crosscheck", help="verify a claimed edit against artifacts and provider usage")
    crosscheck.add_argument("--expect", required=True, help="JSON expectations file")
    crosscheck.add_argument("--diff", help="file containing the observed diff")
    crosscheck.add_argument("--test-log", help="file containing test output")
    crosscheck.add_argument("--claim", help="file containing the model's completion claim")
    crosscheck.add_argument("--usage", help="file containing provider usage JSON")
    crosscheck.add_argument("--json", action="store_true")
    crosscheck.set_defaults(func=command_crosscheck)

    drift = sub.add_parser("drift", help="scan a transcript for deterministic drift signals")
    drift.add_argument("path")
    drift.add_argument("--recent-window", type=int, default=40)
    drift.add_argument("--repeat-threshold", type=int, default=3)
    drift.add_argument("--json", action="store_true")
    drift.set_defaults(func=command_drift)

    anchor = sub.add_parser("anchor", help="build a dual-end re-anchoring block with explicit IDs")
    anchor.add_argument("state", help="JSON state file, or - for stdin")
    anchor.add_argument("--max-tokens", type=int, default=400)
    anchor.add_argument("--json", action="store_true")
    anchor.set_defaults(func=command_anchor)

    reanchor = sub.add_parser("reanchor", help="insert anchor blocks into an envelope and re-run the gate")
    reanchor.add_argument("--envelope", required=True)
    reanchor.add_argument("--state", required=True)
    reanchor.add_argument("--max-tokens", type=int, default=400)
    reanchor.add_argument("--json", action="store_true")
    reanchor.set_defaults(func=command_reanchor)

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
    compact.add_argument("--target-savings", type=float, default=0.0,
                         help="target token savings percentage (e.g. 80 for 80%%+ reduction)")
    compact.add_argument("--critical", default=DEFAULT_CRITICAL)
    compact.add_argument("--profile", choices=sorted(PROFILES), default="generic")
    compact.add_argument("--manifest", help="write the recoverability manifest to this path")
    compact.add_argument("--verify", action="store_true", help="verify the manifest against the original before output")
    compact.add_argument("--json", action="store_true")
    compact.set_defaults(func=command_compact)

    dedupe = sub.add_parser("dedupe", help="collapse exact repeated non-critical lines")
    dedupe.add_argument("paths", nargs="+")
    dedupe.add_argument("--normalize", action="store_true",
                        help="group non-critical lines by normalized template (timestamps, hex, numbers, UUIDs)")
    dedupe.add_argument("--blocks", action="store_true",
                        help="collapse repeating contiguous multi-line command and output blocks")
    dedupe.add_argument("--words", action="store_true",
                        help="eliminate duplicate words and phrases with zero-token references")
    dedupe.add_argument("--critical", default=DEFAULT_CRITICAL)
    dedupe.add_argument("--profile", choices=sorted(PROFILES), default="generic")
    dedupe.add_argument("--json", action="store_true")
    dedupe.set_defaults(func=command_dedupe)

    audit = sub.add_parser("audit", help="rank files by estimated context cost and suggest exclusions (read-only)")
    audit.add_argument("--root", default=".")
    audit.add_argument("--top", type=int, default=15)
    audit.add_argument("--max-files", type=int, default=5000)
    audit.add_argument("--max-read-bytes", type=int, default=262144)
    audit.add_argument("--large-tokens", type=int, default=4000,
                       help="files above this estimate get a bounded-read recommendation")
    audit.add_argument("--profile", choices=sorted(PROFILES), default="generic")
    audit.add_argument("--json", action="store_true")
    audit.set_defaults(func=command_audit)

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
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    parser = build_parser()
    args = parser.parse_args()
    if getattr(args, "context", 0) < 0 or getattr(args, "max_lines", 1) < 1:
        parser.error("--context must be >= 0 and --max-lines must be >= 1")
    if getattr(args, "target_savings", 0.0) < 0.0 or getattr(args, "target_savings", 0.0) > 99.0:
        parser.error("--target-savings must be between 0 and 99")
    for key in ("recent_window", "repeat_threshold", "max_tokens", "top", "max_files",
                "max_read_bytes", "large_tokens"):
        if key in vars(args) and getattr(args, key) < 1:
            parser.error(f"--{key.replace('_', '-')} must be >= 1")
    try:
        return args.func(args)
    except (OSError, ValueError, re.error, json.JSONDecodeError, KeyError) as error:
        print(f"RSaver ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
