#!/usr/bin/env python3
"""RFC Context Fabric: explicit, provenance-aware context persistence for agents.

A store does not give a model memory. Every request must call build_context() and
inject the returned payload into that request. This module keeps durable context,
records exactly what was assembled, validates a per-session/per-prompt canary,
and removes the canary from exported transcripts.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import hmac
import json
import os
import re
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union

SCHEMA_VERSION = 1
DEFAULT_BUDGET_BYTES = 16_000
KINDS = {"objective", "constraint", "decision", "fact", "evidence", "unresolved", "next_action"}
DEFAULT_PRIORITY = {
    "objective": 0,
    "constraint": 0,
    "next_action": 0,
    "decision": 1,
    "unresolved": 1,
    "fact": 2,
    "evidence": 2,
}
ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
PRIVATE_KEY_RE = re.compile(
    r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----[\s\S]+?-----END [A-Z0-9 ]*PRIVATE KEY-----"
)
INLINE_SECRET_RE = re.compile(
    r"(?:sk-[A-Za-z0-9_-]{16,}|(?:AKIA|ASIA)[0-9A-Z]{16}|"
    r"gh[pousr]_[A-Za-z0-9_]{20,}|"
    r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})"
)
ASSIGNMENT_SECRET_RE = re.compile(
    r"(?i)(\b(?:api[_-]?key|secret|token|password|passwd|pwd)\b\s*[:=]\s*)"
    r"(?:'([^'\n]*)'|\"([^\"\n]*)\"|([^\s,;#]+))"
)


class ContextFabricError(RuntimeError):
    """Base error for invalid Context Fabric operations."""


class PromptAlreadyPrepared(ContextFabricError):
    """Raised when a session/prompt identity is reused."""


class DeliveryNotFound(ContextFabricError):
    """Raised when an acknowledgement references an unknown delivery."""


class CanaryMismatch(ContextFabricError):
    """Raised when the supplied canary does not match the prepared delivery."""


def _normalise_text(value: str, field: str, *, allow_empty: bool = False, strip: bool = True) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be text")
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    if strip:
        value = value.strip()
    if not value.strip() and not allow_empty:
        raise ValueError(f"{field} must not be empty")
    if len(value.encode("utf-8")) > 5_000_000:
        raise ValueError(f"{field} exceeds the 5 MB safety limit")
    return value


def _redact_sensitive(value: str) -> str:
    cleaned = PRIVATE_KEY_RE.sub("[REDACTED_SECRET]", value)
    cleaned = INLINE_SECRET_RE.sub("[REDACTED_SECRET]", cleaned)

    def replace_assignment(match: re.Match[str]) -> str:
        if match.group(2) is not None:
            replacement = "'[REDACTED_SECRET]'"
        elif match.group(3) is not None:
            replacement = '"[REDACTED_SECRET]"'
        else:
            replacement = "[REDACTED_SECRET]"
        return match.group(1) + replacement

    return ASSIGNMENT_SECRET_RE.sub(replace_assignment, cleaned)


def _validate_id(value: str, field: str) -> str:
    if not isinstance(value, str) or not ID_RE.fullmatch(value):
        raise ValueError(f"{field} must be 1-128 safe ASCII characters")
    return value


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class ContextFabric:
    """SQLite-backed context store with explicit request hydration and receipts."""

    def __init__(self, workspace_root: Union[str, Path]) -> None:
        self.root = Path(workspace_root).expanduser().resolve()
        if not self.root.is_dir():
            raise ValueError(f"workspace root is not a directory: {self.root}")
        self.state_dir = self.root / ".rcoder"
        if self.state_dir.is_symlink():
            raise ValueError(".rcoder must not be a symlink")
        self.state_dir.mkdir(parents=True, exist_ok=True)
        if not self.state_dir.is_dir():
            raise ValueError(".rcoder is not a directory")
        self.db_path = self.state_dir / "context-fabric.sqlite3"
        if self.db_path.is_symlink():
            raise ValueError("Context Fabric database must not be a symlink")
        try:
            os.chmod(self.state_dir, 0o700)
        except OSError:
            pass  # Windows ACLs are managed by the host, not chmod.
        self._initialise()

    @contextlib.contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 10000")
        try:
            yield conn
        finally:
            conn.close()

    @contextlib.contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        with self._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                yield conn
                conn.commit()
            except BaseException:
                conn.rollback()
                raise

    def _initialise(self) -> None:
        # SQLite journal mode can only be changed outside an active transaction.
        with self._connection() as conn:
            conn.execute("PRAGMA journal_mode = WAL")
        with self._transaction() as conn:
            version = int(conn.execute("PRAGMA user_version").fetchone()[0])
            if version > SCHEMA_VERSION:
                raise ContextFabricError(
                    f"database schema {version} is newer than supported schema {SCHEMA_VERSION}"
                )
            if version == 0:
                conn.executescript(
                    """
                    CREATE TABLE sessions (
                        session_id TEXT PRIMARY KEY,
                        created_at REAL NOT NULL,
                        last_seen_at REAL NOT NULL
                    );
                    CREATE TABLE artifacts (
                        content_sha256 TEXT PRIMARY KEY,
                        content TEXT NOT NULL,
                        size_bytes INTEGER NOT NULL,
                        created_at REAL NOT NULL
                    );
                    CREATE TABLE context_items (
                        item_id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL REFERENCES sessions(session_id),
                        kind TEXT NOT NULL,
                        title TEXT NOT NULL,
                        source_ref TEXT NOT NULL,
                        content_sha256 TEXT NOT NULL REFERENCES artifacts(content_sha256),
                        confidence REAL NOT NULL CHECK(confidence >= 0 AND confidence <= 1),
                        priority INTEGER NOT NULL CHECK(priority >= 0 AND priority <= 5),
                        pinned INTEGER NOT NULL DEFAULT 0 CHECK(pinned IN (0, 1)),
                        created_at REAL NOT NULL,
                        expires_at REAL
                    );
                    CREATE INDEX context_items_session_order
                        ON context_items(session_id, priority, created_at DESC, item_id);
                    CREATE TABLE prompt_deliveries (
                        session_id TEXT NOT NULL REFERENCES sessions(session_id),
                        prompt_id TEXT NOT NULL,
                        created_at REAL NOT NULL,
                        payload_sha256 TEXT NOT NULL,
                        selected_item_ids_json TEXT NOT NULL,
                        ack_token_sha256 TEXT,
                        acknowledged_at REAL,
                        PRIMARY KEY(session_id, prompt_id)
                    );
                    CREATE TABLE transcript_messages (
                        message_id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        prompt_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        created_at REAL NOT NULL,
                        FOREIGN KEY(session_id, prompt_id)
                            REFERENCES prompt_deliveries(session_id, prompt_id)
                    );
                    CREATE INDEX transcript_delivery_order
                        ON transcript_messages(session_id, prompt_id, created_at, message_id);
                    CREATE UNIQUE INDEX prompt_canary_unique
                        ON prompt_deliveries(ack_token_sha256) WHERE ack_token_sha256 IS NOT NULL;
                    PRAGMA user_version = 1;
                    """
                )
        try:
            os.chmod(self.db_path, 0o600)
        except OSError:
            pass

    def ensure_session(
        self,
        session_id: str,
        *,
        now: Optional[Union[int, float]] = None,
    ) -> Dict[str, Any]:
        """Create or refresh a session without requiring a context item first."""
        session_id = _validate_id(session_id, "session_id")
        timestamp = float(time.time() if now is None else now)
        if timestamp < 0:
            raise ValueError("now must be non-negative")
        with self._transaction() as conn:
            existing = conn.execute(
                "SELECT 1 FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
            conn.execute(
                "INSERT INTO sessions(session_id, created_at, last_seen_at) VALUES (?, ?, ?) "
                "ON CONFLICT(session_id) DO UPDATE SET last_seen_at = MAX(last_seen_at, excluded.last_seen_at)",
                (session_id, timestamp, timestamp),
            )
        return {"session_id": session_id, "created": existing is None}

    def store_context(
        self,
        session_id: str,
        kind: str,
        title: str,
        content: str,
        *,
        source_ref: str = "",
        confidence: float = 1.0,
        priority: Optional[int] = None,
        pinned: bool = False,
        ttl_seconds: Optional[int] = None,
        now: Optional[Union[int, float]] = None,
    ) -> Dict[str, Any]:
        session_id = _validate_id(session_id, "session_id")
        if kind not in KINDS:
            raise ValueError(f"kind must be one of: {', '.join(sorted(KINDS))}")
        title = _redact_sensitive(_normalise_text(title, "title"))
        content = _redact_sensitive(_normalise_text(content, "content", strip=False))
        source_ref = _redact_sensitive(_normalise_text(source_ref, "source_ref", allow_empty=True))
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if priority is None:
            priority = DEFAULT_PRIORITY[kind]
        if not isinstance(priority, int) or not 0 <= priority <= 5:
            raise ValueError("priority must be an integer from 0 to 5")
        if ttl_seconds is not None and (not isinstance(ttl_seconds, int) or ttl_seconds < 0):
            raise ValueError("ttl_seconds must be a non-negative integer or None")
        timestamp = float(time.time() if now is None else now)
        if timestamp < 0:
            raise ValueError("now must be non-negative")
        expires_at = timestamp + ttl_seconds if ttl_seconds is not None else None
        digest = _sha256(content)
        item_id = hashlib.sha256(
            f"{session_id}\0{kind}\0{title}\0{digest}".encode("utf-8")
        ).hexdigest()[:24]
        size_bytes = len(content.encode("utf-8"))
        with self._transaction() as conn:
            conn.execute(
                "INSERT INTO sessions(session_id, created_at, last_seen_at) VALUES (?, ?, ?) "
                "ON CONFLICT(session_id) DO UPDATE SET last_seen_at = MAX(last_seen_at, excluded.last_seen_at)",
                (session_id, timestamp, timestamp),
            )
            conn.execute(
                "INSERT OR IGNORE INTO artifacts(content_sha256, content, size_bytes, created_at) VALUES (?, ?, ?, ?)",
                (digest, content, size_bytes, timestamp),
            )
            conn.execute(
                "INSERT OR IGNORE INTO context_items(item_id, session_id, kind, title, source_ref, "
                "content_sha256, confidence, priority, pinned, created_at, expires_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (item_id, session_id, kind, title, source_ref, digest, float(confidence),
                 priority, int(bool(pinned)), timestamp, expires_at),
            )
        return {"item_id": item_id, "content_sha256": digest, "size_bytes": size_bytes,
                "redacted": "[REDACTED_SECRET]" in (title + content + source_ref)}

    @staticmethod
    def _render_item(row: sqlite3.Row) -> str:
        lines = [f"## [{row['kind']}] {row['title']}"]
        if row["source_ref"]:
            lines.append(f"Source: {row['source_ref']}")
        lines.append(f"Confidence: {row['confidence']:.3f}")
        lines.extend(["", row["content"], ""])
        return "\n".join(lines)

    def build_context(
        self,
        session_id: str,
        prompt_id: str,
        *,
        budget_bytes: int = DEFAULT_BUDGET_BYTES,
        ack_token: Optional[str] = None,
        now: Optional[Union[int, float]] = None,
    ) -> Dict[str, Any]:
        """Build the context payload that the caller must inject into this request."""
        session_id = _validate_id(session_id, "session_id")
        prompt_id = _validate_id(prompt_id, "prompt_id")
        if not isinstance(budget_bytes, int) or budget_bytes < 128:
            raise ValueError("budget_bytes must be an integer of at least 128")
        if ack_token is not None:
            ack_token = _normalise_text(ack_token, "ack_token")
            if len(ack_token) < 8 or "\n" in ack_token:
                raise ValueError("ack_token must be a single line of at least 8 characters")
        timestamp = float(time.time() if now is None else now)
        with self._transaction() as conn:
            session = conn.execute(
                "SELECT session_id FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
            if session is None:
                raise ContextFabricError(f"unknown session_id: {session_id}")
            existing = conn.execute(
                "SELECT 1 FROM prompt_deliveries WHERE session_id = ? AND prompt_id = ?",
                (session_id, prompt_id),
            ).fetchone()
            if existing:
                raise PromptAlreadyPrepared(
                    "this session_id/prompt_id pair already exists; use a new prompt_id for each request"
                )
            rows = conn.execute(
                "SELECT i.item_id, i.kind, i.title, i.source_ref, i.confidence, a.content "
                "FROM context_items i JOIN artifacts a USING(content_sha256) "
                "WHERE i.session_id = ? AND (i.expires_at IS NULL OR i.expires_at > ? OR i.pinned = 1) "
                "ORDER BY i.priority ASC, i.created_at DESC, i.item_id ASC",
                (session_id, timestamp),
            ).fetchall()
            header = (
                "# Context Fabric\n"
                f"session_id: {session_id}\n"
                f"prompt_id: {prompt_id}\n"
                "\nThis payload is the explicit context for this request. "
                "The model has no implicit state from prior requests.\n\n"
            )
            canary_block = ""
            token_digest = None
            if ack_token is not None:
                token_digest = _sha256(ack_token)
                canary_block = (
                    "\n[CONTEXT_FABRIC_CANARY]\n"
                    "For delivery verification, append this exact HTML comment as the final line "
                    "of your response, without presenting it as user-facing prose: "
                    f"<!-- RFC-ACK: {ack_token} -->\n"
                )
            base = header + canary_block
            if len(base.encode("utf-8")) > budget_bytes:
                raise ValueError("budget_bytes is too small for the request header and canary")
            selected: List[str] = []
            excluded: List[str] = []
            chunks: List[str] = []
            current_bytes = len(base.encode("utf-8"))
            for row in rows:
                chunk = self._render_item(row)
                chunk_bytes = len(chunk.encode("utf-8"))
                if current_bytes + chunk_bytes <= budget_bytes:
                    selected.append(row["item_id"])
                    chunks.append(chunk)
                    current_bytes += chunk_bytes
                else:
                    excluded.append(row["item_id"])
            payload = base + "".join(chunks)
            payload_digest = _sha256(payload)
            if token_digest is not None:
                reused_token = conn.execute(
                    "SELECT 1 FROM prompt_deliveries WHERE ack_token_sha256 = ? LIMIT 1",
                    (token_digest,),
                ).fetchone()
                if reused_token:
                    raise CanaryMismatch("ack tokens must be unique to one session_id/prompt_id delivery")
            conn.execute(
                "INSERT INTO prompt_deliveries(session_id, prompt_id, created_at, payload_sha256, "
                "selected_item_ids_json, ack_token_sha256) VALUES (?, ?, ?, ?, ?, ?)",
                (session_id, prompt_id, timestamp, payload_digest,
                 json.dumps(selected, separators=(",", ":")), token_digest),
            )
            conn.execute(
                "UPDATE sessions SET last_seen_at = MAX(last_seen_at, ?) WHERE session_id = ?",
                (timestamp, session_id),
            )
        return {
            "session_id": session_id,
            "prompt_id": prompt_id,
            "text": payload,
            "payload_sha256": payload_digest,
            "selected_item_ids": selected,
            "excluded_item_ids": excluded,
            "payload_bytes": len(payload.encode("utf-8")),
            "ack_required": ack_token is not None,
        }

    def record_response(
        self,
        session_id: str,
        prompt_id: str,
        response: str,
        ack_token: str,
        *,
        now: Optional[Union[int, float]] = None,
    ) -> Dict[str, Any]:
        """Verify an echo in the raw response, then persist only the token-free transcript."""
        session_id = _validate_id(session_id, "session_id")
        prompt_id = _validate_id(prompt_id, "prompt_id")
        response = _normalise_text(response, "response", allow_empty=True, strip=False)
        ack_token = _normalise_text(ack_token, "ack_token")
        timestamp = float(time.time() if now is None else now)
        with self._transaction() as conn:
            delivery = conn.execute(
                "SELECT ack_token_sha256 FROM prompt_deliveries WHERE session_id = ? AND prompt_id = ?",
                (session_id, prompt_id),
            ).fetchone()
            if delivery is None:
                raise DeliveryNotFound("no prepared delivery for this session_id/prompt_id pair")
            expected = delivery["ack_token_sha256"]
            if expected is None or not hmac.compare_digest(expected, _sha256(ack_token)):
                raise CanaryMismatch("ack token does not match this session_id/prompt_id delivery")
            acknowledged = ack_token in response
            safe_response = response.replace(ack_token, "") if acknowledged else response
            safe_response = _redact_sensitive(safe_response)
            message_id = hashlib.sha256(
                f"{session_id}\0{prompt_id}\0assistant\0{safe_response}".encode("utf-8")
            ).hexdigest()
            conn.execute(
                "INSERT OR IGNORE INTO transcript_messages(message_id, session_id, prompt_id, role, content, created_at) "
                "VALUES (?, ?, ?, 'assistant', ?, ?)",
                (message_id, session_id, prompt_id, safe_response, timestamp),
            )
            if acknowledged:
                conn.execute(
                    "UPDATE prompt_deliveries SET acknowledged_at = ? WHERE session_id = ? AND prompt_id = ?",
                    (timestamp, session_id, prompt_id),
                )
        return {"session_id": session_id, "prompt_id": prompt_id,
                "acknowledged": acknowledged, "transcript_token_free": True}

    def export_transcript(self, session_id: str, prompt_id: str) -> Dict[str, Any]:
        session_id = _validate_id(session_id, "session_id")
        prompt_id = _validate_id(prompt_id, "prompt_id")
        with self._connection() as conn:
            delivery = conn.execute(
                "SELECT created_at, payload_sha256, acknowledged_at FROM prompt_deliveries "
                "WHERE session_id = ? AND prompt_id = ?", (session_id, prompt_id)
            ).fetchone()
            if delivery is None:
                raise DeliveryNotFound("no prepared delivery for this session_id/prompt_id pair")
            messages = conn.execute(
                "SELECT role, content, created_at FROM transcript_messages "
                "WHERE session_id = ? AND prompt_id = ? ORDER BY created_at, message_id",
                (session_id, prompt_id),
            ).fetchall()
        return {
            "session_id": session_id,
            "prompt_id": prompt_id,
            "created_at": delivery["created_at"],
            "payload_sha256": delivery["payload_sha256"],
            "acknowledged": delivery["acknowledged_at"] is not None,
            "messages": [dict(row) for row in messages],
        }

    def gc(self, *, now: Union[int, float]) -> Dict[str, Union[int, float]]:
        """Delete expired unpinned context at an explicit deterministic time boundary."""
        if not isinstance(now, (int, float)) or now < 0:
            raise ValueError("gc requires a non-negative explicit now timestamp")
        with self._transaction() as conn:
            expired = conn.execute(
                "SELECT item_id FROM context_items WHERE pinned = 0 AND expires_at IS NOT NULL AND expires_at <= ?",
                (float(now),),
            ).fetchall()
            if expired:
                conn.executemany(
                    "DELETE FROM context_items WHERE item_id = ?",
                    [(row["item_id"],) for row in expired],
                )
            orphaned = conn.execute(
                "SELECT content_sha256 FROM artifacts WHERE NOT EXISTS "
                "(SELECT 1 FROM context_items WHERE context_items.content_sha256 = artifacts.content_sha256)"
            ).fetchall()
            if orphaned:
                conn.executemany(
                    "DELETE FROM artifacts WHERE content_sha256 = ?",
                    [(row["content_sha256"],) for row in orphaned],
                )
        return {"as_of": float(now), "expired_items_deleted": len(expired),
                "orphan_artifacts_deleted": len(orphaned)}

    def stats(self) -> Dict[str, int]:
        with self._connection() as conn:
            return {
                "sessions": int(conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]),
                "context_items": int(conn.execute("SELECT COUNT(*) FROM context_items").fetchone()[0]),
                "artifacts": int(conn.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0]),
                "prompt_deliveries": int(conn.execute("SELECT COUNT(*) FROM prompt_deliveries").fetchone()[0]),
                "transcript_messages": int(conn.execute("SELECT COUNT(*) FROM transcript_messages").fetchone()[0]),
            }


def _read_text(path: Optional[str]) -> str:
    if not path or path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="workspace root")
    sub = parser.add_subparsers(dest="command", required=True)
    put = sub.add_parser("put", help="store a context item")
    put.add_argument("--session", required=True)
    put.add_argument("--kind", required=True, choices=sorted(KINDS))
    put.add_argument("--title", required=True)
    put.add_argument("--source", default="")
    put.add_argument("--priority", type=int)
    put.add_argument("--ttl-seconds", type=int)
    put.add_argument("--pin", action="store_true")
    put.add_argument("--file", default="-", help="UTF-8 input file or - for stdin")
    build = sub.add_parser("build", help="assemble context for one model request")
    build.add_argument("--session", required=True)
    build.add_argument("--prompt", required=True)
    build.add_argument("--budget-bytes", type=int, default=DEFAULT_BUDGET_BYTES)
    build.add_argument("--ack-token-file", help="read canary token from a private file")
    build.add_argument("--now", type=float)
    ack = sub.add_parser("ack", help="verify a model response and store token-free transcript")
    ack.add_argument("--session", required=True)
    ack.add_argument("--prompt", required=True)
    ack.add_argument("--token-file", required=True)
    ack.add_argument("--response-file", default="-", help="response file or - for stdin")
    ack.add_argument("--now", type=float)
    export = sub.add_parser("export", help="export the token-free transcript")
    export.add_argument("--session", required=True)
    export.add_argument("--prompt", required=True)
    gc = sub.add_parser("gc", help="collect expired unpinned context using an explicit timestamp")
    gc.add_argument("--now", type=float, required=True)
    sub.add_parser("stats", help="show local store counters")
    args = parser.parse_args(argv)
    try:
        fabric = ContextFabric(args.root)
        if args.command == "put":
            result = fabric.store_context(
                args.session, args.kind, args.title, _read_text(args.file),
                source_ref=args.source, priority=args.priority, ttl_seconds=args.ttl_seconds,
                pinned=args.pin,
            )
        elif args.command == "build":
            token = Path(args.ack_token_file).read_text(encoding="utf-8").strip() if args.ack_token_file else None
            result = fabric.build_context(args.session, args.prompt, budget_bytes=args.budget_bytes,
                                          ack_token=token, now=args.now)
        elif args.command == "ack":
            token = Path(args.token_file).read_text(encoding="utf-8").strip()
            result = fabric.record_response(args.session, args.prompt, _read_text(args.response_file),
                                            token, now=args.now)
        elif args.command == "export":
            result = fabric.export_transcript(args.session, args.prompt)
        elif args.command == "gc":
            result = fabric.gc(now=args.now)
        else:
            result = fabric.stats()
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (OSError, ValueError, sqlite3.Error, ContextFabricError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
