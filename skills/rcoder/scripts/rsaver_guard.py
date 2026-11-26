#!/usr/bin/env python3
"""AST/brace-anchored skeletonizer, reversible redactor, and git-drift guard for RSaver.

The module is intentionally standard-library only and side-effect free. It never
executes project code and never writes files on its own; callers choose whether to
persist a reversible vault. Skeleton output is lossy by design and always carries
``L<start>-L<end>`` anchors so omitted ranges remain recoverable from the original.
"""
from __future__ import annotations

import ast
import hashlib
import math
import re
import subprocess
from pathlib import Path
from typing import Any

SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "PRIVATE_KEY",
        re.compile(
            r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----[\s\S]+?-----END [A-Z0-9 ]*PRIVATE KEY-----"
        ),
    ),
    ("AWS_KEY", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("GITHUB_TOKEN", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,}\b")),
    (
        "JWT",
        re.compile(
            r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"
        ),
    ),
    (
        "OPENAI_OR_API_KEY",
        re.compile(r"\bsk-(?:proj-|live-|test-)?[A-Za-z0-9_-]{20,}\b"),
    ),
    (
        "BEARER_ASSIGNMENT",
        re.compile(
            r"""(?i)\b(?:api[_-]?key|secret|token|password|passwd|pwd)\b\s*[:=]\s*"""
            r"""['"]([^'"\n]{12,})['"]"""
        ),
    ),
    (
        "BEARER_ASSIGNMENT_UNQUOTED",
        re.compile(
            r"(?i)\b(?:api[_-]?key|secret|token|password|passwd|pwd)\b\s*[:=]\s*"
            r"([^\s,'\";#}]{12,})"
        ),
    ),
]

HIGH_ENTROPY_CANDIDATE_RE = re.compile(r"""['"]([A-Za-z0-9+/=_-]{24,})['"]""")
PLACEHOLDER_RE = re.compile(r"\[REDACTED:[A-Z0-9_]+:[0-9a-f]{10}\]")

DOC_SUFFIXES = {".md", ".txt", ".rst", ".adoc"}
BRACE_SUFFIXES = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".go", ".rs", ".java", ".kt", ".swift"}
DECLARATION_RE = re.compile(
    r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?"
    r"(?:function|class|interface|type|enum|struct|impl|trait|fn|func)\b"
)


def shannon_entropy(data: str) -> float:
    """Return Shannon entropy in bits per character."""
    if not data:
        return 0.0
    frequencies: dict[str, int] = {}
    for character in data:
        frequencies[character] = frequencies.get(character, 0) + 1
    length = len(data)
    return -sum((count / length) * math.log2(count / length) for count in frequencies.values())


class ReversibleRedactor:
    """Deterministic + Shannon-entropy secret redactor with a session-scoped vault."""

    def __init__(self, entropy_threshold: float = 4.3) -> None:
        self.entropy_threshold = entropy_threshold
        self.vault: dict[str, str] = {}
        self.counts: dict[str, int] = {}

    def _token_for(self, kind: str, secret: str) -> str:
        digest = hashlib.sha256(secret.encode("utf-8")).hexdigest()[:10]
        placeholder = f"[REDACTED:{kind}:{digest}]"
        self.vault[placeholder] = secret
        self.counts[kind] = self.counts.get(kind, 0) + 1
        return placeholder

    def redact(self, text: str) -> tuple[str, int]:
        out = text
        for kind, pattern in SECRET_PATTERNS:

            def replace(match: re.Match[str], redaction_kind: str = kind) -> str:
                whole = match.group(0)
                if PLACEHOLDER_RE.search(whole):
                    return whole
                if match.lastindex:
                    secret_value = match.group(1)
                    if PLACEHOLDER_RE.search(secret_value):
                        return whole
                    return whole.replace(secret_value, self._token_for(redaction_kind, secret_value))
                return self._token_for(redaction_kind, whole)

            out = pattern.sub(replace, out)

        def entropy_replace(match: re.Match[str]) -> str:
            candidate = match.group(1)
            if PLACEHOLDER_RE.search(candidate):
                return match.group(0)
            if candidate.count("/") > 2 and not candidate.startswith(("eyJ", "sk-")):
                return match.group(0)
            if shannon_entropy(candidate) >= self.entropy_threshold:
                return match.group(0).replace(candidate, self._token_for("HIGH_ENTROPY", candidate))
            return match.group(0)

        out = HIGH_ENTROPY_CANDIDATE_RE.sub(entropy_replace, out)
        return out, sum(self.counts.values())

    def restore(self, text: str) -> str:
        out = text
        for placeholder in sorted(self.vault, key=len, reverse=True):
            out = out.replace(placeholder, self.vault[placeholder])
        return out

    @classmethod
    def from_vault(cls, vault: dict[str, str], entropy_threshold: float = 4.3) -> "ReversibleRedactor":
        redactor = cls(entropy_threshold=entropy_threshold)
        redactor.vault = {str(key): str(value) for key, value in vault.items()}
        return redactor


def _doc_hint(node: ast.AST) -> str:
    doc = ast.get_docstring(node, clean=True)  # type: ignore[arg-type]
    if not doc:
        return ""
    first_line = doc.splitlines()[0].strip()[:80]
    return f'  """{first_line}"""' if first_line else ""


def _signature(lines: list[str], start: int, body_start: int) -> str:
    stop = max(start, body_start)
    signature = " ".join(line.strip() for line in lines[start - 1:stop]).strip()
    return signature[:300]


def compress_python_skeleton(source: str, file_label: str = "") -> str:
    """Strip function bodies while preserving exact ``L<start>-L<end>`` anchors, types, and docstrings."""
    lines = source.splitlines()
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError, RecursionError):
        return "\n".join(f"L{index}: {line}" for index, line in enumerate(lines, 1))

    output: list[str] = []
    if file_label:
        output.append(f"# FILE: {file_label} (total_lines={len(lines)})")

    for node in tree.body:
        start = getattr(node, "lineno", 1)
        end = getattr(node, "end_lineno", start)
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            output.append(f"L{start}-L{end}: {lines[start - 1].strip()}")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            signature_end = (node.body[0].lineno if node.body else end + 1) - 1
            signature = _signature(lines, start, signature_end)
            output.append(f"L{start}-L{end}: {signature} ...{_doc_hint(node)}")
        elif isinstance(node, ast.ClassDef):
            output.append(f"L{start}-L{end}: {lines[start - 1].strip()}")
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    item_start = item.lineno
                    item_end = getattr(item, "end_lineno", item.lineno)
                    item_signature_end = (item.body[0].lineno if item.body else item_end + 1) - 1
                    item_signature = _signature(lines, item_start, item_signature_end)
                    output.append(f"  L{item_start}-L{item_end}: {item_signature} ...{_doc_hint(item)}")
        else:
            snippet = lines[start - 1].strip()
            if snippet and not snippet.startswith("#"):
                output.append(f"L{start}-L{end}: {snippet[:100]}")

    return "\n".join(output)


def _masked_source(source: str) -> str:
    """Blank strings and comments while preserving offsets, for brace counting."""
    result = list(source)
    length = len(source)
    index = 0
    while index < length:
        character = source[index]
        if character in {"'", '"', "`"}:
            quote = character
            result[index] = " "
            index += 1
            while index < length:
                if source[index] == "\\":
                    result[index] = " "
                    if index + 1 < length:
                        result[index + 1] = " "
                    index += 2
                    continue
                if source[index] == quote:
                    result[index] = " "
                    index += 1
                    break
                if source[index] != "\n":
                    result[index] = " "
                index += 1
            continue
        if character == "/" and index + 1 < length and source[index + 1] == "/":
            while index < length and source[index] != "\n":
                result[index] = " "
                index += 1
            continue
        if character == "/" and index + 1 < length and source[index + 1] == "*":
            result[index] = result[index + 1] = " "
            index += 2
            while index + 1 < length and not (source[index] == "*" and source[index + 1] == "/"):
                if source[index] != "\n":
                    result[index] = " "
                index += 1
            if index + 1 < length:
                result[index] = result[index + 1] = " "
            index += 2
            continue
        index += 1
    return "".join(result)


def compress_brace_skeleton(source: str, file_label: str = "") -> str:
    """Replace balanced brace bodies of top-level declarations with anchors and ``...``."""
    lines = source.splitlines()
    masked = _masked_source(source)
    line_starts = [0]
    for line in lines[:-1]:
        line_starts.append(line_starts[-1] + len(line) + 1)

    def line_of(offset: int) -> int:
        low, high = 0, len(line_starts) - 1
        while low < high:
            middle = (low + high + 1) // 2
            if line_starts[middle] <= offset:
                low = middle
            else:
                high = middle - 1
        return low + 1

    entries: list[tuple[int, int, str]] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        start_offset = line_starts[index]
        if DECLARATION_RE.match(line):
            open_offset = masked.find("{", start_offset)
            if open_offset >= 0 and line_of(open_offset) <= index + 4:
                depth = 0
                close_offset = -1
                for offset in range(open_offset, len(masked)):
                    if masked[offset] == "{":
                        depth += 1
                    elif masked[offset] == "}":
                        depth -= 1
                        if depth == 0:
                            close_offset = offset
                            break
                if close_offset >= 0:
                    start = line_of(start_offset)
                    end = line_of(close_offset)
                    header = " ".join(
                        part.strip() for part in source[start_offset:open_offset].splitlines()
                    )
                    entries.append((start, end, header[:300]))
                    index = end
                    continue
        index += 1

    if not entries:
        return "\n".join(f"L{index}: {line}" for index, line in enumerate(lines, 1))

    output: list[str] = []
    if file_label:
        output.append(f"// FILE: {file_label} (total_lines={len(lines)})")
    cursor = 0
    for start, end, header in entries:
        if start <= cursor:
            continue
        for number in range(cursor + 1, start):
            line = lines[number - 1]
            if line.strip():
                output.append(f"L{number}: {line[:200]}")
        output.append(f"L{start}-L{end}: {header} {{ ... }}")
        cursor = end
    for number in range(cursor + 1, len(lines) + 1):
        line = lines[number - 1]
        if line.strip():
            output.append(f"L{number}: {line[:200]}")
    return "\n".join(output)


def compress_skeleton(source: str, file_label: str = "", suffix: str = ".py") -> str:
    """Dispatch to the Python AST or brace-aware skeletonizer."""
    if suffix.lower() == ".py":
        return compress_python_skeleton(source, file_label)
    if suffix.lower() in BRACE_SUFFIXES:
        return compress_brace_skeleton(source, file_label)
    return "\n".join(f"L{index}: {line}" for index, line in enumerate(source.splitlines(), 1))


def crosscheck_git_drift(
    workspace: Path,
    target_files: list[str],
    claimed_files: list[str] | None = None,
) -> dict[str, Any]:
    """Compare ``git status`` against stated objective targets and agent file claims."""
    try:
        process = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(workspace),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        git_available = process.returncode == 0
    except (OSError, subprocess.SubprocessError):
        git_available = False
        process = None

    modified: set[str] = set()
    if git_available and process is not None:
        for line in process.stdout.splitlines():
            if len(line) >= 4:
                path_part = line[3:].strip().split(" -> ")[-1].strip('"')
                modified.add(path_part.replace("\\", "/"))

    def normalize(values: list[str]) -> set[str]:
        normalized: set[str] = set()
        for value in values:
            if not isinstance(value, str) or not value.strip():
                continue
            item = value.replace("\\", "/")
            while item.startswith("./"):
                item = item[2:]
            normalized.add(item)
        return normalized

    normalized_targets = normalize(target_files)
    normalized_claims = normalize(claimed_files or [])

    untouched_targets = sorted(normalized_targets - modified) if git_available else []
    unplanned_edits = (
        sorted(modified - normalized_targets) if (git_available and normalized_targets) else []
    )
    unverified_claims = (
        sorted(normalized_claims - modified) if (git_available and normalized_claims) else []
    )
    drift_detected = bool(untouched_targets or unplanned_edits or unverified_claims)

    return {
        "git_available": git_available,
        "status": "DRIFT_DETECTED" if drift_detected else "ALIGNED",
        "modified_files": sorted(modified),
        "untouched_targets": untouched_targets,
        "unplanned_edits": unplanned_edits,
        "unverified_claims": unverified_claims,
    }
