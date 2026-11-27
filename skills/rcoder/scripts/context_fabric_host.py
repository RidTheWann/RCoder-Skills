#!/usr/bin/env python3
"""Claude Code host adapter for RFC Context Fabric.

UserPromptSubmit assembles and injects a fresh payload through the documented
additionalContext channel. Stop verifies the per-prompt canary against the
host's last_assistant_message and stores a token-free RFC transcript record.

The adapter is opt-in: it does nothing unless .rcoder/context-fabric.sqlite3
already exists. It fails open and never blocks a prompt or stop event.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import sys
from pathlib import Path
from typing import Any, Optional

from context_fabric import ContextFabric, DEFAULT_BUDGET_BYTES, ID_RE, PromptAlreadyPrepared

MAX_EVENT_BYTES = 1_000_000
DISABLE_ENV = "RCODER_HOOKS_DISABLE"
RFC_DISABLE_ENV = "RCODER_RFC_DISABLE"
DEBUG_ENV = "RCODER_RFC_DEBUG"


def _read_event() -> Optional[dict]:
    raw = sys.stdin.buffer.read(MAX_EVENT_BYTES + 1)
    if not raw or len(raw) > MAX_EVENT_BYTES:
        return None
    try:
        event = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None
    return event if isinstance(event, dict) else None


def _workspace(event: dict) -> Optional[Path]:
    value = event.get("cwd")
    if not isinstance(value, str) or not value.strip():
        return None
    root = Path(value).expanduser().resolve()
    return root if root.is_dir() else None


def _identity(event: dict) -> Optional[tuple[str, str]]:
    session_id = event.get("session_id")
    prompt_id = event.get("prompt_id")
    if not isinstance(session_id, str) or not ID_RE.fullmatch(session_id):
        return None
    if not isinstance(prompt_id, str) or not ID_RE.fullmatch(prompt_id):
        return None
    return session_id, prompt_id


def _database_ready(root: Path) -> bool:
    state_dir = root / ".rcoder"
    database = state_dir / "context-fabric.sqlite3"
    return (
        not state_dir.is_symlink()
        and state_dir.is_dir()
        and not database.is_symlink()
        and database.is_file()
    )


def _canary_directory(root: Path, *, create: bool) -> Optional[Path]:
    state_dir = root / ".rcoder"
    private_dir = state_dir / "private"
    canary_dir = private_dir / "rfc-canaries"
    if state_dir.is_symlink() or not state_dir.is_dir():
        raise ValueError("RFC state directory is unavailable or unsafe")
    for directory in (private_dir, canary_dir):
        if directory.is_symlink():
            raise ValueError("RFC private state must not contain symbolic links")
        if create:
            directory.mkdir(mode=0o700, exist_ok=True)
        elif not directory.is_dir():
            return None
        if not directory.is_dir():
            raise ValueError("RFC private state path is not a directory")
        try:
            os.chmod(directory, 0o700)
        except OSError:
            pass  # Windows ACLs are managed by the host.
    return canary_dir


def _canary_path(root: Path, session_id: str, prompt_id: str, *, create: bool) -> Optional[Path]:
    directory = _canary_directory(root, create=create)
    if directory is None:
        return None
    identity = hashlib.sha256(f"{session_id}\0{prompt_id}".encode("utf-8")).hexdigest()
    path = directory / f"{identity}.token"
    if path.is_symlink():
        raise ValueError("RFC canary token file must not be a symbolic link")
    return path


def _write_private_token(path: Path, token: str) -> None:
    descriptor = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(token + "\n")
            stream.flush()
            try:
                os.fsync(stream.fileno())
            except OSError:
                pass
    except BaseException:
        try:
            path.unlink()
        except OSError:
            pass
        raise
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass  # Windows ACLs are managed by the host.


def handle_user_prompt_submit(event: dict) -> Optional[dict]:
    """Return Claude's documented additionalContext response, or None for a no-op."""
    if os.environ.get(DISABLE_ENV) == "1" or os.environ.get(RFC_DISABLE_ENV) == "1":
        return None
    root = _workspace(event)
    identity = _identity(event)
    if root is None or identity is None or not _database_ready(root):
        return None

    session_id, prompt_id = identity
    fabric = ContextFabric(root)
    fabric.ensure_session(session_id)
    token_path = _canary_path(root, session_id, prompt_id, create=True)
    if token_path is None:
        return None
    # A duplicate hook invocation for the same prompt must not overwrite its canary.
    if token_path.exists():
        return None
    token = secrets.token_urlsafe(24)
    try:
        _write_private_token(token_path, token)
    except FileExistsError:
        return None
    try:
        built = fabric.build_context(
            session_id,
            prompt_id,
            budget_bytes=DEFAULT_BUDGET_BYTES,
            ack_token=token,
        )
    except PromptAlreadyPrepared:
        try:
            token_path.unlink()
        except OSError:
            pass
        return None
    except BaseException:
        try:
            token_path.unlink()
        except OSError:
            pass
        raise

    return {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": built["text"],
        }
    }


def handle_stop(event: dict) -> Optional[dict]:
    """Capture the final assistant response for the exact prompt delivery."""
    if os.environ.get(DISABLE_ENV) == "1" or os.environ.get(RFC_DISABLE_ENV) == "1":
        return None
    root = _workspace(event)
    identity = _identity(event)
    response = event.get("last_assistant_message")
    if root is None or identity is None or not isinstance(response, str) or not response:
        return None
    if not _database_ready(root):
        return None

    session_id, prompt_id = identity
    token_path = _canary_path(root, session_id, prompt_id, create=False)
    if token_path is None or not token_path.is_file() or token_path.is_symlink():
        return None
    token = token_path.read_text(encoding="utf-8").strip()
    if not token:
        return None

    fabric = ContextFabric(root)
    result = fabric.record_response(session_id, prompt_id, response, token)
    # The raw token is needed only until this exact Stop event is evaluated.
    token_path.unlink()
    return result


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("event", choices=("user-prompt-submit", "stop"))
    args = parser.parse_args(argv)
    try:
        event = _read_event()
        if event is None:
            return 0
        if args.event == "user-prompt-submit":
            output = handle_user_prompt_submit(event)
            if output is not None:
                print(json.dumps(output, ensure_ascii=False))
        else:
            handle_stop(event)
    except Exception as exc:  # host hooks must fail open, never wedge the agent.
        if os.environ.get(DEBUG_ENV) == "1":
            print(f"rfc-host: ignored {type(exc).__name__}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
