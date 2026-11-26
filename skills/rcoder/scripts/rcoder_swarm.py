#!/usr/bin/env python3
"""Advisory file-lease coordinator and canonical SHA-256 handoff capsule checksum."""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

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
        lock_path = self.leases_path.with_suffix(".lock")
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        if lock_path.exists() and time.time() - lock_path.stat().st_mtime > 60:
            lock_path.unlink(missing_ok=True)
        deadline = time.time() + timeout_sec
        while True:
            try:
                descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                break
            except FileExistsError:
                if time.time() >= deadline:
                    raise RuntimeError("timed out acquiring the file-lease lock")
                time.sleep(0.02)
        try:
            yield
        finally:
            os.close(descriptor)
            lock_path.unlink(missing_ok=True)

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
