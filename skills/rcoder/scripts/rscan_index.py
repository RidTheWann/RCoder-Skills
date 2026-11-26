#!/usr/bin/env python3
"""Incremental SQLite symbol index with transitive test blast-radius solver."""
from __future__ import annotations

import ast
import contextlib
import hashlib
import json
import re
import sqlite3
from collections import deque
from pathlib import Path
from typing import Any

from platform_runtime import to_posix_rel


def _lf_sha256(data: bytes) -> str:
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def _extract_python_symbols(source: str) -> list[dict[str, Any]]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    symbols: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            kind = "class" if isinstance(node, ast.ClassDef) else "function"
            symbols.append({
                "name": node.name,
                "kind": kind,
                "start_line": node.lineno,
                "end_line": getattr(node, "end_lineno", node.lineno),
            })
    return symbols


JS_FUNCTION_RE = re.compile(
    r"\b(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]{1,})\s*\("
)
JS_CLASS_RE = re.compile(r"\bclass\s+([A-Za-z_$][\w$]{1,})")
GO_FUNC_RE = re.compile(r"^func\s+(?:\([^)]*\)\s*)?([A-Za-z_]\w*)\s*\(", re.MULTILINE)
GO_STRUCT_RE = re.compile(r"^type\s+([A-Za-z_]\w*)\s+struct\b", re.MULTILINE)
RUST_FN_RE = re.compile(r"^(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?fn\s+([A-Za-z_]\w*)\s*\(", re.MULTILINE)
RUST_STRUCT_RE = re.compile(r"^(?:pub(?:\([^)]*\))?\s+)?struct\s+([A-Za-z_]\w*)", re.MULTILINE)


def _extract_heuristic_symbols(source: str, suffix: str) -> list[dict[str, Any]]:
    if suffix == ".py":
        return _extract_python_symbols(source)
    patterns: list[tuple[re.Pattern[str], str]] = []
    if suffix in {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"}:
        patterns = [(JS_FUNCTION_RE, "function"), (JS_CLASS_RE, "class")]
    elif suffix == ".go":
        patterns = [(GO_FUNC_RE, "function"), (GO_STRUCT_RE, "class")]
    elif suffix == ".rs":
        patterns = [(RUST_FN_RE, "function"), (RUST_STRUCT_RE, "class")]
    symbols: list[dict[str, Any]] = []
    seen: set[tuple[str, str, int]] = set()
    for pattern, kind in patterns:
        for match in pattern.finditer(source):
            name = match.group(1)
            line = source.count("\n", 0, match.start()) + 1
            key = (name, kind, line)
            if key in seen:
                continue
            seen.add(key)
            symbols.append({"name": name, "kind": kind, "start_line": line, "end_line": line})
    return symbols


class IncrementalRepoIndex:
    """SQLite-backed incremental symbol index that is safe on Windows, Linux, and macOS."""

    def __init__(self, workspace_root: Path, db_path: str | Path | None = None) -> None:
        self.root = workspace_root.resolve()
        self.db_path = Path(db_path) if db_path else self.root / ".rcoder" / "index.db"
        self._memory_connection: sqlite3.Connection | None = None
        if str(self.db_path) != ":memory:":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        if str(self.db_path) == ":memory:":
            if self._memory_connection is None:
                self._memory_connection = sqlite3.connect(":memory:")
                self._memory_connection.row_factory = sqlite3.Row
            return self._memory_connection
        connection = sqlite3.connect(str(self.db_path))
        connection.row_factory = sqlite3.Row
        return connection

    @contextlib.contextmanager
    def _session(self):
        connection = self._connect()
        try:
            yield connection
        finally:
            if str(self.db_path) != ":memory:":
                connection.close()

    def _init_schema(self) -> None:
        with self._session() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS files (
                    path TEXT PRIMARY KEY,
                    mtime_ns INTEGER NOT NULL,
                    size INTEGER NOT NULL,
                    sha256 TEXT NOT NULL,
                    symbols_json TEXT NOT NULL
                );
                """
            )
            connection.commit()

    def sync_files(self, rel_paths: list[str]) -> dict[str, int]:
        reindexed = 0
        cached = 0
        seen: set[str] = set()
        with self._session() as connection:
            existing = {
                row["path"]: (row["mtime_ns"], row["size"], row["sha256"])
                for row in connection.execute("SELECT path, mtime_ns, size, sha256 FROM files")
            }
            for rel in rel_paths:
                posix = to_posix_rel(rel, self.root)
                full = self.root / posix
                if not full.is_file():
                    continue
                seen.add(posix)
                stat_result = full.stat()
                previous = existing.get(posix)
                if previous and previous[0] == stat_result.st_mtime_ns and previous[1] == stat_result.st_size:
                    cached += 1
                    continue
                raw = full.read_bytes()
                digest = _lf_sha256(raw)
                symbols = _extract_heuristic_symbols(
                    raw.decode("utf-8", errors="replace"), Path(posix).suffix.lower()
                )
                connection.execute(
                    """
                    INSERT INTO files(path, mtime_ns, size, sha256, symbols_json)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(path) DO UPDATE SET
                        mtime_ns=excluded.mtime_ns,
                        size=excluded.size,
                        sha256=excluded.sha256,
                        symbols_json=excluded.symbols_json
                    """,
                    (posix, stat_result.st_mtime_ns, stat_result.st_size, digest,
                     json.dumps(symbols)),
                )
                reindexed += 1
            stale = set(existing) - seen
            if stale:
                connection.executemany("DELETE FROM files WHERE path = ?", [(item,) for item in stale])
            connection.commit()
        return {"reindexed": reindexed, "cached": cached, "removed": len(stale)}

    def find_symbol(self, symbol_name: str) -> list[dict[str, Any]]:
        matches: list[dict[str, Any]] = []
        needle = symbol_name.lower()
        with self._session() as connection:
            for row in connection.execute("SELECT path, symbols_json FROM files"):
                for symbol in json.loads(row["symbols_json"]):
                    if needle in symbol["name"].lower():
                        matches.append({"path": row["path"], **symbol})
        return matches


def compute_test_blast_radius(
    changed_files: list[str],
    forward_edges: dict[str, list[str]],
    all_files: list[str],
) -> dict[str, Any]:
    """Compute reverse-dependency blast radius and map impacted modules to test files."""
    reverse_edges: dict[str, set[str]] = {}
    for source, targets in forward_edges.items():
        for target in targets:
            reverse_edges.setdefault(target, set()).add(source)

    impacted: set[str] = {to_posix_rel(item) for item in changed_files}
    queue: deque[str] = deque(impacted)
    while queue:
        current = queue.popleft()
        for caller in reverse_edges.get(current, ()):
            if caller not in impacted:
                impacted.add(caller)
                queue.append(caller)

    test_candidates = [
        item for item in all_files
        if "test" in Path(item).name.lower() or "spec" in Path(item).name.lower()
    ]
    selected_tests: set[str] = set()
    for module in impacted:
        stem = Path(module).stem
        for candidate in test_candidates:
            if candidate == module or stem in Path(candidate).stem:
                selected_tests.add(candidate)

    return {
        "changed_count": len(changed_files),
        "impacted_modules": sorted(impacted),
        "recommended_tests": sorted(selected_tests),
    }
