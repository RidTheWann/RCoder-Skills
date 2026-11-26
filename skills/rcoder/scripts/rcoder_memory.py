#!/usr/bin/env python3
"""Cross-platform episodic failure-to-fix memory and FTS5 symbol ledger."""
from __future__ import annotations

import contextlib
import hashlib
import json
import re
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from platform_runtime import to_posix_rel

TOKEN_RE = re.compile(r"[a-z0-9_]{3,}")
PRIVATE_KEY_RE = re.compile(
    r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----[\s\S]+?-----END [A-Z0-9 ]*PRIVATE KEY-----"
)
INLINE_SECRET_RE = re.compile(
    r"(?:sk-[A-Za-z0-9_-]{16,}|(?:AKIA|ASIA)[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9_]{20,}|"
    r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})"
)
ASSIGNMENT_SECRET_RE = re.compile(
    r"(?i)(\b(?:api[_-]?key|secret|token|password|passwd|pwd)\b\s*[:=]\s*)"
    r"(?:'([^'\n]*)'|\"([^\"\n]*)\"|([^\s,;#]+))"
)


def _tokenize(text: str) -> set[str]:
    return set(TOKEN_RE.findall(text.lower()))


def _sanitize(text: str) -> str:
    cleaned = text.replace("\r\n", "\n").strip()
    cleaned = PRIVATE_KEY_RE.sub("[REDACTED_SECRET]", cleaned)
    cleaned = INLINE_SECRET_RE.sub("[REDACTED_SECRET]", cleaned)
    def redact_assignment(match: re.Match[str]) -> str:
        if match.group(2) is not None:
            value = "'[REDACTED_SECRET]'"
        elif match.group(3) is not None:
            value = '"[REDACTED_SECRET]"'
        else:
            value = "[REDACTED_SECRET]"
        return match.group(1) + value

    return ASSIGNMENT_SECRET_RE.sub(redact_assignment, cleaned)


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


class RCoderMemoryStore:
    """SQLite FTS5 ledger of decisions, fixes, invariants, and security findings."""

    def __init__(self, repo_root: Path) -> None:
        self.db_path = repo_root.resolve() / ".rcoder" / "memory.sqlite3"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextlib.contextmanager
    def _conn(self):
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS episodes (
                    id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    files_json TEXT NOT NULL,
                    symbols_json TEXT NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    hit_count INTEGER DEFAULT 0,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS episodes_fts USING fts5(
                    id UNINDEXED,
                    title,
                    summary,
                    files,
                    symbols,
                    tokenize='porter unicode61'
                )
                """
            )

    def record(
        self,
        kind: str,
        title: str,
        summary: str,
        files: Optional[List[str]] = None,
        symbols: Optional[List[str]] = None,
        confidence: float = 1.0,
    ) -> str:
        if kind not in {"fix", "adr", "invariant", "security"}:
            raise ValueError(f"unsupported episode kind: {kind}")
        clean_title = _sanitize(title)
        clean_summary = _sanitize(summary)
        norm_files = sorted({to_posix_rel(item, self.db_path.parent.parent) for item in (files or []) if item})
        norm_symbols = sorted({symbol.strip() for symbol in (symbols or []) if symbol.strip()})
        ep_id = hashlib.sha256(
            f"{kind}:{clean_title}:{','.join(norm_files)}".encode("utf-8")
        ).hexdigest()[:16]
        now = time.time()
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO episodes (id, kind, title, summary, files_json, symbols_json,
                                      confidence, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    summary=excluded.summary,
                    files_json=excluded.files_json,
                    symbols_json=excluded.symbols_json,
                    confidence=MAX(episodes.confidence, excluded.confidence),
                    updated_at=excluded.updated_at
                """,
                (
                    ep_id, kind, clean_title, clean_summary,
                    json.dumps(norm_files), json.dumps(norm_symbols),
                    confidence, now, now,
                ),
            )
            conn.execute("DELETE FROM episodes_fts WHERE id = ?", (ep_id,))
            conn.execute(
                "INSERT INTO episodes_fts (id, title, summary, files, symbols) VALUES (?, ?, ?, ?, ?)",
                (ep_id, clean_title, clean_summary, " ".join(norm_files), " ".join(norm_symbols)),
            )
        return ep_id

    def recall_for_context(
        self,
        query: str = "",
        target_files: Optional[List[str]] = None,
        limit: int = 6,
    ) -> List[Dict[str, Any]]:
        tokens: List[str] = []
        for raw in query.split() + list(target_files or []):
            cleaned = "".join(
                char if char.isalnum() or char in "_-." else " " for char in raw
            ).strip()
            for part in cleaned.split():
                if len(part) >= 3:
                    tokens.append(f'"{part}"')
        if not tokens:
            return []

        fts_query = " OR ".join(dict.fromkeys(tokens[:16]))
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT e.id, e.kind, e.title, e.summary, e.files_json, e.symbols_json,
                       e.confidence, bm25(episodes_fts) AS rank
                FROM episodes_fts
                JOIN episodes e ON e.id = episodes_fts.id
                WHERE episodes_fts MATCH ?
                ORDER BY rank ASC, e.confidence DESC
                LIMIT ?
                """,
                (fts_query, limit),
            ).fetchall()
            ids = [row["id"] for row in rows]
            if ids:
                conn.executemany(
                    "UPDATE episodes SET hit_count = hit_count + 1 WHERE id = ?",
                    [(item,) for item in ids],
                )

        return [
            {
                "id": row["id"],
                "kind": row["kind"],
                "title": row["title"],
                "summary": row["summary"],
                "files": json.loads(row["files_json"]),
                "symbols": json.loads(row["symbols_json"]),
                "confidence": row["confidence"],
            }
            for row in rows
        ]

    def recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT id, kind, title, summary, files_json, symbols_json, confidence, hit_count "
                "FROM episodes ORDER BY updated_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "kind": row["kind"],
                "title": row["title"],
                "summary": row["summary"],
                "files": json.loads(row["files_json"]),
                "symbols": json.loads(row["symbols_json"]),
                "confidence": row["confidence"],
                "hit_count": row["hit_count"],
            }
            for row in rows
        ]
