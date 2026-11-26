#!/usr/bin/env python3
"""File leases, handoff checksums, and DAG-parallel swarm orchestration."""
from __future__ import annotations

import concurrent.futures
import contextlib
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from platform_runtime import to_posix_rel


def canonical_digest(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class SwarmCoordinator:
    """Manages TTL file write-leases and checksummed subagent handoff capsules."""

    def __init__(self, workspace_root: Path) -> None:
        self.root = workspace_root.resolve()
        self.leases_path = self.root / ".rcoder" / "leases.json"

    @contextlib.contextmanager
    def _lease_lock(self, timeout_sec: float = 5.0):
        """Serialize lease read/check/write with an OS lock, not a stale PID lockfile.

        The lock file is intentionally persistent: unlinking a locked inode can let a
        second process create and lock a replacement while the first still owns the
        original. Advisory locks are released by the OS if the process exits.
        """
        lock_path = self.leases_path.with_suffix(".lock")
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
        deadline = time.monotonic() + timeout_sec
        locked = False
        try:
            if os.name == "nt":
                import msvcrt
                while not locked:
                    try:
                        os.lseek(descriptor, 0, os.SEEK_SET)
                        msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
                        locked = True
                    except OSError:
                        if time.monotonic() >= deadline:
                            raise RuntimeError("timed out acquiring the file-lease lock")
                        time.sleep(0.02)
                # Initialize the lock byte only after acquiring the exclusive lock.
                # Concurrent first-time callers can otherwise both observe an empty
                # file and race to write it while the other caller holds the byte lock.
                if os.fstat(descriptor).st_size == 0:
                    os.lseek(descriptor, 0, os.SEEK_SET)
                    os.write(descriptor, b"0")
            else:
                import fcntl
                while not locked:
                    try:
                        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        locked = True
                    except BlockingIOError:
                        if time.monotonic() >= deadline:
                            raise RuntimeError("timed out acquiring the file-lease lock")
                        time.sleep(0.02)
            yield
        finally:
            if locked:
                if os.name == "nt":
                    import msvcrt
                    os.lseek(descriptor, 0, os.SEEK_SET)
                    msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)

    def _read_leases(self, now: float) -> dict[str, dict[str, Any]]:
        if not self.leases_path.exists():
            return {}
        try:
            raw = json.loads(self.leases_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, ValueError):
            return {}
        if not isinstance(raw, dict):
            return {}
        active: dict[str, dict[str, Any]] = {}
        for path, meta in raw.items():
            if not isinstance(meta, dict):
                continue
            try:
                expires = float(meta.get("expires_at", 0))
            except (TypeError, ValueError):
                continue
            if expires > now:
                active[str(path)] = meta
        return active

    def _write_leases(self, leases: dict[str, dict[str, Any]]) -> None:
        self.leases_path.parent.mkdir(parents=True, exist_ok=True)
        with self.leases_path.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(leases, indent=2, sort_keys=True) + "\n")

    def claim_files(self, agent_id: str, files: list[str], ttl_sec: int = 300) -> dict[str, Any]:
        with self._lease_lock():
            now = time.time()
            leases = self._read_leases(now)
            normalized = sorted({to_posix_rel(item, self.root) for item in files if item})
            conflicts: list[dict[str, Any]] = []
            for rel in normalized:
                holder = leases.get(rel)
                if holder and holder.get("agent_id") != agent_id:
                    conflicts.append({
                        "file": rel,
                        "held_by": holder["agent_id"],
                        "expires_at": holder.get("expires_at"),
                    })
            if conflicts:
                return {"granted": False, "conflicts": conflicts}
            for rel in normalized:
                leases[rel] = {"agent_id": agent_id, "expires_at": now + ttl_sec}
            self._write_leases(leases)
            return {"granted": True, "agent_id": agent_id, "claimed": normalized}

    def release_files(self, agent_id: str, files: list[str] | None = None) -> dict[str, Any]:
        with self._lease_lock():
            leases = self._read_leases(time.time())
            targets = {to_posix_rel(item, self.root) for item in files} if files else None
            released: list[str] = []
            for rel in list(leases):
                if leases[rel].get("agent_id") == agent_id and (targets is None or rel in targets):
                    del leases[rel]
                    released.append(rel)
            self._write_leases(leases)
            return {"released": sorted(released)}

    def pack_handoff(
        self,
        from_agent: str,
        to_agent: str,
        objective: str,
        target_files: list[str],
        verified_receipts: list[str],
        notes: str = "",
    ) -> dict[str, Any]:
        body = {
            "from_agent": from_agent,
            "to_agent": to_agent,
            "objective": objective.strip(),
            "target_files": sorted({to_posix_rel(item, self.root) for item in target_files if item}),
            "verified_receipts": [receipt.replace("\r\n", "\n").strip() for receipt in verified_receipts],
            "notes": notes.replace("\r\n", "\n").strip(),
        }
        return {**body, "sha256": canonical_digest(body)}

    @staticmethod
    def verify_handoff(capsule: dict[str, Any]) -> bool:
        """Verify the checksum; this is integrity, not cryptographic authentication."""
        expected = capsule.get("sha256")
        if not isinstance(expected, str) or len(expected) != 64:
            return False
        body = {key: value for key, value in capsule.items() if key != "sha256"}
        return canonical_digest(body) == expected


AGENT_CAPABILITIES: Dict[str, Dict[str, Any]] = {
    "rcoder-explorer": {"tier": "fast", "read_only": True, "max_tokens": 4000},
    "rcoder-saver": {"tier": "fast", "read_only": True, "max_tokens": 2000},
    "rcoder-planner": {"tier": "reasoning", "read_only": True, "max_tokens": 8000},
    "rcoder-debugger": {"tier": "reasoning", "read_only": False, "max_tokens": 12000},
    "rcoder-reviewer": {"tier": "reasoning", "read_only": True, "max_tokens": 6000},
    "rcoder-security-reviewer": {"tier": "reasoning", "read_only": True, "max_tokens": 8000},
    "rcoder-verifier": {"tier": "balanced", "read_only": True, "max_tokens": 6000},
}


@dataclass
class SwarmTask:
    task_id: str
    agent: str
    objective: str
    target_paths: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)
    isolate_worktree: bool = False
    status: str = "pending"
    result: Dict[str, Any] = field(default_factory=dict)
    duration_ms: int = 0


class SwarmBlackboard:
    """Concurrency-safe shared state backed by SQLite WAL."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS blackboard (
                    run_id TEXT NOT NULL,
                    key TEXT NOT NULL,
                    agent TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    updated_at REAL NOT NULL,
                    PRIMARY KEY (run_id, key)
                )
                """
            )

    @contextlib.contextmanager
    def _conn(self):
        conn = sqlite3.connect(str(self.db_path), timeout=15.0)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def put(self, run_id: str, key: str, agent: str, payload: Any) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO blackboard (run_id, key, agent, payload, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(run_id, key) DO UPDATE SET
                    agent=excluded.agent,
                    payload=excluded.payload,
                    updated_at=excluded.updated_at
                """,
                (run_id, key, agent, json.dumps(payload, ensure_ascii=False), time.time()),
            )

    def snapshot(self, run_id: str) -> Dict[str, Any]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT key, agent, payload FROM blackboard WHERE run_id = ?",
                (run_id,),
            ).fetchall()
        return {key: {"agent": agent, "data": json.loads(payload)} for key, agent, payload in rows}


class WorktreeManager:
    """Temporary Git worktrees so parallel code-writing agents do not overwrite each other."""

    def __init__(self, repo_root: Path, scratch_root: Path) -> None:
        self.repo_root = repo_root
        self.scratch_root = scratch_root

    def is_git_repo(self) -> bool:
        return (self.repo_root / ".git").exists()

    def create(self, run_id: str, task_id: str) -> Optional[Path]:
        if not self.is_git_repo():
            return None
        wt_path = self.scratch_root / f"{run_id}-{task_id}"
        if wt_path.exists():
            self.remove(wt_path)
        wt_path.parent.mkdir(parents=True, exist_ok=True)
        proc = subprocess.run(
            ["git", "worktree", "add", "--detach", str(wt_path), "HEAD"],
            cwd=str(self.repo_root),
            capture_output=True,
            text=True,
        )
        return wt_path if proc.returncode == 0 else None

    def collect_diff(self, wt_path: Path) -> str:
        listed = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard", "-z"],
            cwd=str(wt_path), capture_output=True, check=False,
        )
        if listed.returncode != 0:
            return ""
        untracked = [item.decode("utf-8", errors="surrogateescape")
                     for item in listed.stdout.split(b"\0") if item]
        intent_added = False
        try:
            if untracked:
                staged = subprocess.run(
                    ["git", "add", "--intent-to-add", "--", *untracked],
                    cwd=str(wt_path), capture_output=True, text=True, check=False,
                )
                if staged.returncode != 0:
                    return ""
                intent_added = True
            proc = subprocess.run(
                ["git", "diff", "--binary", "--no-ext-diff"],
                cwd=str(wt_path), capture_output=True, text=True, check=False,
            )
            return proc.stdout if proc.returncode == 0 else ""
        finally:
            if intent_added:
                subprocess.run(
                    ["git", "reset", "--quiet", "--", *untracked],
                    cwd=str(wt_path), capture_output=True, text=True, check=False,
                )

    def remove(self, wt_path: Path) -> None:
        if not wt_path.exists():
            return
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(wt_path)],
            cwd=str(self.repo_root),
            capture_output=True,
            text=True,
        )
        shutil.rmtree(wt_path, ignore_errors=True)


class RCoderSwarm:
    """Topological-wave DAG scheduler with a mandatory verifier gate."""

    def __init__(self, repo_root: Path, max_workers: int = 4) -> None:
        self.repo_root = repo_root.resolve()
        self.state_dir = self.repo_root / ".rcoder" / "swarm"
        self.board = SwarmBlackboard(self.state_dir / "blackboard.sqlite3")
        self.worktrees = WorktreeManager(self.repo_root, self.state_dir / "worktrees")
        self.max_workers = max(1, min(max_workers, (os.cpu_count() or 2)))

    def _build_waves(self, tasks: List[SwarmTask]) -> List[List[SwarmTask]]:
        by_id = {task.task_id: task for task in tasks}
        if len(by_id) != len(tasks):
            raise ValueError("Duplicate task_id detected in swarm graph.")
        for task in tasks:
            for dependency in task.depends_on:
                if dependency not in by_id:
                    raise ValueError(
                        f"Task '{task.task_id}' depends on unknown task '{dependency}'."
                    )

        completed: set[str] = set()
        remaining = dict(by_id)
        waves: List[List[SwarmTask]] = []

        while remaining:
            ready = [
                task for task in remaining.values()
                if all(dependency in completed for dependency in task.depends_on)
            ]
            if not ready:
                raise ValueError("Cyclic dependency detected in swarm DAG.")
            waves.append(ready)
            for task in ready:
                completed.add(task.task_id)
                remaining.pop(task.task_id)
        return waves

    def execute(
        self,
        tasks: List[SwarmTask],
        runner: Callable[[SwarmTask, Path, Dict[str, Any]], Dict[str, Any]],
        require_verifier: bool = True,
    ) -> Dict[str, Any]:
        if require_verifier:
            verifier_tasks = [task for task in tasks if task.agent == "rcoder-verifier"]
            if not verifier_tasks:
                verifier_tasks = [SwarmTask(
                    task_id="gate-verify",
                    agent="rcoder-verifier",
                    objective="Verify all swarm outputs, diffs, and invariant checks.",
                    depends_on=[task.task_id for task in tasks],
                )]
                tasks = list(tasks) + verifier_tasks
            else:
                work_ids = {task.task_id for task in tasks if task.agent != "rcoder-verifier"}
                for verifier in verifier_tasks:
                    verifier.depends_on = sorted(set(verifier.depends_on) | work_ids)

        run_id = hashlib.sha256(
            f"{time.time_ns()}-{len(tasks)}".encode("utf-8")
        ).hexdigest()[:12]
        waves = self._build_waves(tasks)

        def _run_one(task: SwarmTask) -> SwarmTask:
            started = time.perf_counter()
            caps = AGENT_CAPABILITIES.get(
                task.agent, {"tier": "balanced", "read_only": True}
            )
            wt_path: Optional[Path] = None
            exec_root = self.repo_root
            try:
                if task.isolate_worktree and not caps.get("read_only", True):
                    wt_path = self.worktrees.create(run_id, task.task_id)
                    if wt_path:
                        exec_root = wt_path
                context = {
                    "run_id": run_id,
                    "capabilities": caps,
                    "blackboard": self.board.snapshot(run_id),
                }
                out = runner(task, exec_root, context)
                if wt_path:
                    out["worktree_diff"] = self.worktrees.collect_diff(wt_path)
                task.status = "completed"
                task.result = out
                self.board.put(run_id, f"task:{task.task_id}", task.agent, out)
            except Exception as exc:
                task.status = "failed"
                task.result = {"error": str(exc)}
                self.board.put(run_id, f"error:{task.task_id}", task.agent, task.result)
            finally:
                if wt_path:
                    self.worktrees.remove(wt_path)
                task.duration_ms = int((time.perf_counter() - started) * 1000)
            return task

        for wave in waves:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as pool:
                futures = [pool.submit(_run_one, task) for task in wave]
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    if result.status == "failed" and result.agent == "rcoder-verifier":
                        break

        return {
            "run_id": run_id,
            "waves": len(waves),
            "tasks": [asdict(task) for task in tasks],
            "blackboard": self.board.snapshot(run_id),
        }
