#!/usr/bin/env python3
"""Cross-platform episodic failure-to-fix memory store."""
from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any

from platform_runtime import to_posix_rel

TOKEN_RE = re.compile(r"[a-z0-9_]{3,}")
INLINE_SECRET_RE = re.compile(
    r"(?:sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9_]{20,}|"
    r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})"
)


def _tokenize(text: str) -> set[str]:
    return set(TOKEN_RE.findall(text.lower()))


def _sanitize(text: str) -> str:
    return INLINE_SECRET_RE.sub("[REDACTED_SECRET]", text.replace("\r\n", "\n").strip())


class EpisodicLessonStore:
    """Append-only JSONL lesson store portable across Windows, Linux, and macOS."""

    def __init__(self, workspace_root: Path) -> None:
        self.root = workspace_root.resolve()
        self.store_path = self.root / ".rcoder" / "lessons.jsonl"

    def record_lesson(
        self,
        symptom: str,
        root_cause: str,
        verified_fix: str,
        related_files: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        clean_symptom = _sanitize(symptom)
        clean_cause = _sanitize(root_cause)
        clean_fix = _sanitize(verified_fix)
        norm_files = sorted({to_posix_rel(item, self.root) for item in (related_files or []) if item})
        norm_tags = sorted({tag.strip().lower() for tag in (tags or []) if tag.strip()})
        fingerprint = hashlib.sha256(
            f"{clean_symptom}|{clean_fix}".encode("utf-8")
        ).hexdigest()[:12]
        entry = {
            "id": fingerprint,
            "ts": int(time.time()),
            "symptom": clean_symptom,
            "root_cause": clean_cause,
            "verified_fix": clean_fix,
            "files": norm_files,
            "tags": norm_tags,
        }
        existing = self._load_all()
        if any(item.get("id") == fingerprint for item in existing):
            return {"recorded": False, "duplicate": True, "lesson": entry}
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        with self.store_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
        return {"recorded": True, "duplicate": False, "lesson": entry}

    def _load_all(self) -> list[dict[str, Any]]:
        if not self.store_path.exists():
            return []
        lessons: list[dict[str, Any]] = []
        try:
            text = self.store_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                lessons.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return lessons

    def recall(self, query: str, limit: int = 3, min_score: float = 0.12) -> list[dict[str, Any]]:
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []
        scored: list[tuple[float, dict[str, Any]]] = []
        for item in self._load_all():
            corpus = " ".join([
                str(item.get("symptom", "")),
                str(item.get("root_cause", "")),
                str(item.get("verified_fix", "")),
                " ".join(str(part) for part in item.get("files", [])),
                " ".join(str(part) for part in item.get("tags", [])),
            ])
            corpus_tokens = _tokenize(corpus)
            if not corpus_tokens:
                continue
            score = len(query_tokens & corpus_tokens) / len(query_tokens | corpus_tokens)
            if score >= min_score:
                scored.append((round(score, 4), item))
        scored.sort(key=lambda pair: (-pair[0], -pair[1].get("ts", 0)))
        return [{"relevance": score, **lesson} for score, lesson in scored[:limit]]
