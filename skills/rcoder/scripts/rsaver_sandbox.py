#!/usr/bin/env python3
"""Atomic multi-file patch sandbox with automatic rollback on syntax or test failure."""
from __future__ import annotations

import json
import py_compile
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from platform_runtime import resolve_python_command, to_native_path, to_posix_rel


class SandboxEditError(Exception):
    """Raised when a patch hunk cannot be applied deterministically."""


def _write_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text.replace("\r\n", "\n"))


def _validate_syntax(target: Path) -> str | None:
    suffix = target.suffix.lower()
    if suffix == ".py":
        try:
            with tempfile.TemporaryDirectory() as temporary:
                compiled = Path(temporary) / (target.stem + ".pyc")
                py_compile.compile(str(target), cfile=str(compiled), doraise=True)
        except py_compile.PyCompileError as error:
            return f"Python syntax error in {target.name}: {error.msg}"
        except (OSError, ValueError) as error:
            return f"Python syntax check failed in {target.name}: {error}"
    elif suffix == ".json":
        try:
            json.loads(target.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as error:
            return f"JSON syntax error in {target.name}: {error}"
    return None


def transactional_apply_and_verify(
    workspace_root: Path,
    edits: list[dict[str, str]],
    verify_cmd: list[str] | None = None,
    timeout_sec: int = 60,
) -> dict[str, Any]:
    """Apply exact-match edits, run verification, and roll back every touched file on failure."""
    root = workspace_root.resolve()
    backups: dict[Path, bytes | None] = {}
    touched_rel: list[str] = []

    def rollback() -> None:
        for path, original_bytes in reversed(list(backups.items())):
            if original_bytes is None:
                if path.exists():
                    path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(original_bytes)

    try:
        if not edits:
            raise SandboxEditError("No edits provided.")
        for index, item in enumerate(edits):
            rel = to_posix_rel(item.get("path", ""), root)
            if not rel:
                raise SandboxEditError(f"Edit #{index} missing valid 'path'.")
            target = to_native_path(rel, root).resolve(strict=False)
            if not target.is_relative_to(root):
                raise SandboxEditError(f"Path traversal rejected: {rel}")
            if target not in backups:
                backups[target] = target.read_bytes() if target.exists() else None
                touched_rel.append(rel)
            old_text = item.get("old_text", "")
            new_text = item.get("new_text", "")
            if not isinstance(old_text, str) or not isinstance(new_text, str):
                raise SandboxEditError(f"Edit #{index} old_text and new_text must be strings.")
            if not target.exists():
                if old_text:
                    raise SandboxEditError(f"File '{rel}' does not exist for non-empty old_text.")
                _write_lf(target, new_text)
                continue
            current = target.read_text(encoding="utf-8").replace("\r\n", "\n")
            normalized_old = old_text.replace("\r\n", "\n")
            normalized_new = new_text.replace("\r\n", "\n")
            if not normalized_old:
                updated = current + normalized_new
            else:
                matches = current.count(normalized_old)
                if matches == 0:
                    raise SandboxEditError(f"old_text not found in '{rel}'.")
                if matches > 1:
                    raise SandboxEditError(
                        f"Ambiguous old_text in '{rel}' ({matches} occurrences). Include more context lines."
                    )
                updated = current.replace(normalized_old, normalized_new, 1)
            _write_lf(target, updated)

        for path in backups:
            if path.exists():
                error = _validate_syntax(path)
                if error:
                    rollback()
                    return {
                        "ok": False, "rolled_back": True, "stage": "syntax_check",
                        "error": error, "files": touched_rel,
                    }

        if verify_cmd:
            command = list(verify_cmd)
            if command and command[0] in {"python", "python3"}:
                command = [*resolve_python_command(), *command[1:]]
            try:
                process = subprocess.run(
                    command, cwd=str(root), capture_output=True, text=True,
                    timeout=timeout_sec, check=False,
                )
            except (OSError, subprocess.SubprocessError) as error:
                rollback()
                return {
                    "ok": False, "rolled_back": True, "stage": "verification_command",
                    "error": str(error), "files": touched_rel,
                }
            if process.returncode != 0:
                rollback()
                return {
                    "ok": False, "rolled_back": True, "stage": "verification_command",
                    "exit_code": process.returncode,
                    "stdout_tail": process.stdout[-2000:],
                    "stderr_tail": process.stderr[-2000:],
                    "files": touched_rel,
                }
        return {"ok": True, "rolled_back": False, "files_committed": touched_rel}
    except Exception as error:
        rollback()
        return {
            "ok": False, "rolled_back": True, "stage": "patch_apply",
            "error": str(error), "files": touched_rel,
        }
