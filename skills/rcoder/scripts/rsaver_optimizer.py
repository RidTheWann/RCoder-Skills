"""Conservative prose-only context optimization for RSaver.

The optimizer is deliberately narrower than a summarizer: it applies an allowlist
of phrase substitutions to prose lines and returns a copy. It never edits source
files, removes sentences, strips filler words, or rewrites code and evidence.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Callable

CONTENT_TYPES = ("auto", "prose", "markdown", "code", "structured", "evidence")

CODE_SUFFIXES = {
    ".py", ".pyi", ".c", ".cc", ".cpp", ".h", ".hpp", ".js", ".jsx", ".mjs",
    ".ts", ".tsx", ".rs", ".go", ".java", ".cs", ".kt", ".kts", ".swift",
    ".sh", ".bash", ".zsh", ".ps1", ".bat", ".cmd", ".sql", ".rb", ".php",
    ".ex", ".exs", ".lua", ".pl", ".r", ".jl", ".dart",
}
STRUCTURED_SUFFIXES = {
    ".json", ".jsonl", ".ndjson", ".yaml", ".yml", ".toml", ".xml", ".ini",
    ".cfg", ".conf", ".env", ".csv", ".tsv",
}
MARKDOWN_SUFFIXES = {".md", ".mdx", ".rst", ".adoc"}
EVIDENCE_SUFFIXES = {".log", ".out", ".err", ".trace"}

# Only substitutions with a stable, local equivalent are included.
PHRASE_RULES = (
    ("in order to", "to", re.compile(r"\bin\s+order\s+to\b", re.IGNORECASE)),
    ("due to the fact that", "because",
     re.compile(r"\bdue\s+to\s+the\s+fact\s+that\b", re.IGNORECASE)),
    ("at this point in time", "now",
     re.compile(r"\bat\s+this\s+point\s+in\s+time\b", re.IGNORECASE)),
    ("in the event that", "if",
     re.compile(r"\bin\s+the\s+event\s+that\b", re.IGNORECASE)),
    ("with regard to", "about", re.compile(r"\bwith\s+regard\s+to\b", re.IGNORECASE)),
    ("prior to", "before", re.compile(r"\bprior\s+to\b", re.IGNORECASE)),
    ("subsequent to", "after", re.compile(r"\bsubsequent\s+to\b", re.IGNORECASE)),
    ("a large number of", "many",
     re.compile(r"\ba\s+large\s+number\s+of\b", re.IGNORECASE)),
    ("as a result of", "because of",
     re.compile(r"\bas\s+a\s+result\s+of\b", re.IGNORECASE)),
)

# Any normative or evidence-bearing line is left untouched.
CONSTRAINT_RE = re.compile(
    r"\b(?:must|shall|should|required|requirement|constraints?|never|always|only|"
    r"unless|except|forbidden|prohibited|do\s+not|don't|cannot|can't|not\s+verified|"
    r"not\s+allowed|authorization|permission)\b",
    re.IGNORECASE,
)
EVIDENCE_RE = re.compile(
    r"(?:\b(?:ERROR|FATAL|PANIC|TRACEBACK|EXCEPTION|FAIL(?:ED|URE)?|PASS|"
    r"NOT\s+VERIFIED|INFERRED|UNKNOWN)\b|"
    r"\b(?:sha256|exit[_ -]?code|status)\s*[=:]|\b[0-9a-f]{40,}\b|https?://)",
    re.IGNORECASE,
)
LOG_LINE_RE = re.compile(
    r"^\s*(?:\[[0-9T:.,+\- Z]+\]\s*)?(?:DEBUG|INFO|WARN|WARNING|ERROR|FATAL|TRACE)\b|"
    r"^\s*(?:Traceback \(most recent call last\)|at\s+\S+|File \".+\", line \d+)|"
    r"^\s*(?:PASS|FAIL)(?:\b|:)",
    re.IGNORECASE,
)
CODE_LINE_RE = re.compile(
    r"^\s*(?:async\s+def|def|class|from\s+\S+\s+import|import\s+\S+|"
    r"(?:pub\s+)?(?:async\s+)?fn\s+\w+|use\s+\S+;|#include\s*[<\"]|"
    r"(?:const|let|var|function|export)\s+\S+|"
    r"(?:if|for|while|switch|return)\s*[\(\{]|"
    r"(?:package|namespace)\s+\S+)",
    re.IGNORECASE,
)
CALL_LINE_RE = re.compile(r"^\s*(?:[\w$]+\.)+[\w$]+\s*\(")
MARKDOWN_CONTROL_RE = re.compile(
    r"^\s{0,3}(?:#{1,6}\s|>\s|[-*+]\s|\d{1,3}[.)]\s|"
    r"(?:---+|___+|\*\*\*+)\s*$)"
)
KEY_VALUE_RE = re.compile(r"^\s*[\w./-]+\s*[:=]\s*\S")
URL_RE = re.compile(r"(?:https?://|www\.)", re.IGNORECASE)
MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]*\]\([^)]+\)|\[[^\]]+\]\[[^\]]*\]")
HTML_RE = re.compile(r"</?[A-Za-z][^>]*>")
FENCE_RE = re.compile(r"^\s{0,3}(\x60{3,}|~{3,})")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _looks_like_json(text: str) -> bool:
    stripped = text.strip()
    if not stripped or stripped[0] not in "{[":
        return False
    try:
        json.loads(stripped)
        return True
    except (ValueError, TypeError):
        return False


def _looks_like_log(text: str) -> bool:
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return False
    matches = sum(
        1 for line in lines if LOG_LINE_RE.search(line) or EVIDENCE_RE.search(line)
    )
    return matches >= 2 and matches / len(lines) >= 0.15


def classify_content(name: str, text: str) -> str:
    """Classify content conservatively so non-prose inputs are never rewritten."""
    suffix = Path(name).suffix.lower()
    if suffix in CODE_SUFFIXES:
        return "code"
    if suffix in STRUCTURED_SUFFIXES:
        return "structured"
    if suffix in EVIDENCE_SUFFIXES:
        return "evidence"
    if suffix in MARKDOWN_SUFFIXES:
        return "markdown"
    if _looks_like_json(text):
        return "structured"
    if _looks_like_log(text):
        return "evidence"
    if CODE_LINE_RE.search(text):
        return "code"
    if re.search(
        r"(?m)^\s{0,3}(?:#{1,6}\s|\x60{3,}|~~~|>\s|[-*+]\s)", text
    ):
        return "markdown"
    return "prose"


def _replacement_case(match: re.Match, replacement: str) -> str:
    source = match.group(0)
    if source.isupper():
        return replacement.upper()
    if source[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def _is_protected_line(body: str, markdown: bool) -> bool:
    if not body.strip() or body.startswith((" ", "\t")):
        return True
    if CONSTRAINT_RE.search(body) or EVIDENCE_RE.search(body):
        return True
    if URL_RE.search(body) or MARKDOWN_LINK_RE.search(body) or HTML_RE.search(body):
        return True
    if chr(96) in body or "|" in body or "{" in body or "}" in body:
        return True
    if KEY_VALUE_RE.match(body) or CODE_LINE_RE.match(body) or CALL_LINE_RE.match(body):
        return True
    if MARKDOWN_CONTROL_RE.match(body):
        return True
    if markdown and (
        body.lstrip().startswith(("---", "+++", "<!--")) or body.rstrip().endswith("  ")
    ):
        return True
    return False


def _tighten_line(body: str) -> tuple[str, dict[str, int]]:
    counts: dict[str, int] = {}
    output = body
    for source, replacement, pattern in PHRASE_RULES:
        output, count = pattern.subn(
            lambda match: _replacement_case(match, replacement), output
        )
        if count:
            counts[source] = counts.get(source, 0) + count
    return output, counts


def _transform(
    text: str,
    content_type: str,
    tighten_phrases: bool,
) -> tuple[str, dict[str, int], list[int]]:
    if not tighten_phrases or content_type in {"code", "structured", "evidence"}:
        return text, {}, []

    lines = text.splitlines(keepends=True)
    if not lines and text:
        lines = [text]

    output: list[str] = []
    totals: dict[str, int] = {}
    changed_lines: list[int] = []
    markdown = content_type == "markdown"

    first_line = lines[0].lstrip("\ufeff").strip() if lines else ""
    in_frontmatter = markdown and first_line == "---"
    fence_char = ""
    fence_size = 0

    for number, line in enumerate(lines, 1):
        if line.endswith("\r\n"):
            body, ending = line[:-2], "\r\n"
        elif line.endswith(("\n", "\r")):
            body, ending = line[:-1], line[-1:]
        else:
            body, ending = line, ""

        if in_frontmatter:
            output.append(line)
            if number > 1 and body.strip() in {"---", "..."}:
                in_frontmatter = False
            continue

        if markdown:
            fence = FENCE_RE.match(body)
            if fence:
                marker = fence.group(1)
                marker_char, marker_size = marker[0], len(marker)
                if not fence_char:
                    fence_char, fence_size = marker_char, marker_size
                elif marker_char == fence_char and marker_size >= fence_size:
                    fence_char, fence_size = "", 0
                output.append(line)
                continue
            if fence_char:
                output.append(line)
                continue

        if _is_protected_line(body, markdown):
            output.append(line)
            continue

        rewritten, counts = _tighten_line(body)
        if rewritten == body:
            output.append(line)
            continue

        changed_lines.append(number)
        for phrase, count in counts.items():
            totals[phrase] = totals.get(phrase, 0) + count
        output.append(rewritten + ending)

    return "".join(output), totals, changed_lines


def optimize_context(
    text: str,
    *,
    name: str = "<inline>",
    content_type: str = "auto",
    profile: str = "generic",
    estimator: Callable[[str, str], int],
    tighten_phrases: bool = True,
) -> dict:
    """Return an optimized copy with classification, hashes, and estimate metadata."""
    if content_type not in CONTENT_TYPES:
        raise ValueError(f"unsupported content type: {content_type}")

    detected = classify_content(name, text)
    warnings: list[str] = []
    selected = detected if content_type == "auto" else content_type

    # A prose override must not turn a Markdown document into unstructured prose.
    if content_type == "prose" and detected == "markdown":
        selected = "markdown"
        warnings.append("prose mode retained Markdown protections for this input")
    elif content_type in {"prose", "markdown"} and detected in {
        "code", "structured", "evidence"
    }:
        selected = detected
        warnings.append(
            f"requested {content_type} mode was ignored because the input was detected as {detected}"
        )

    original_estimate = estimator(text, profile)
    candidate, rule_counts, changed_lines = _transform(
        text, selected, tighten_phrases
    )
    optimized_estimate = estimator(candidate, profile)

    if candidate != text and optimized_estimate >= original_estimate:
        candidate = text
        optimized_estimate = original_estimate
        rule_counts = {}
        changed_lines = []
        warnings.append("estimated savings were not positive; original context retained")
    elif candidate == text:
        warnings.append("no safe allowlisted phrase transformations were applicable")

    saved = max(0, original_estimate - optimized_estimate)
    return {
        "source": name,
        "content_type": selected,
        "detected_content_type": detected,
        "strategy": "allowlisted_phrase_tightening" if changed_lines else "preserve_original",
        "source_modified": False,
        "original_sha256": _sha256(text),
        "optimized_sha256": _sha256(candidate),
        "transformations": {
            "changed_lines": len(changed_lines),
            "line_numbers": changed_lines[:100],
            "line_numbers_truncated": max(0, len(changed_lines) - 100),
            "phrase_counts": rule_counts,
        },
        "stats": {
            "profile": profile,
            "estimate_method": "content_class_pretoken_heuristic_v2",
            "original_estimate": original_estimate,
            "optimized_estimate": optimized_estimate,
            "saved_estimate": saved,
            "saved_percent": round(100 * saved / original_estimate, 2)
            if original_estimate else 0.0,
        },
        "warnings": warnings,
        "optimized_text": candidate,
    }
