#!/usr/bin/env python3
"""Claude Code host adapter for RFC Context Fabric.

UserPromptSubmit assembles and injects a fresh payload through the documented
additionalContext channel. Stop verifies the per-prompt canary against the
host's last_assistant_message and stores a token-free RFC transcript record.

If Claude omits prompt_id on an early prompt, the adapter creates a fresh
runtime ID and keeps a private session-to-delivery pointer until Stop.
The adapter is opt-in and fails open; it never blocks a prompt or stop event.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import sys
import time
from pathlib import Path
from typing import Optional

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


def _session_id(event: dict) -> Optional[str]:
    value = event.get("session_id")
    return value if isinstance(value, str) and ID_RE.fullmatch(value) else None


def _host_prompt_id(event: dict) -> tuple[bool, Optional[str]]:
    """Return (valid, prompt_id); missing is supported, malformed is not."""
    value = event.get("prompt_id")
    if value is None:
        return True, None
    if isinstance(value, str) and ID_RE.fullmatch(value):
        return True, value
    return False, None


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


def _pending_path(root: Path, session_id: str, *, create: bool) -> Optional[Path]:
    directory = _canary_directory(root, create=create)
    if directory is None:
        return None
    identity = hashlib.sha256(session_id.encode("utf-8")).hexdigest()
    path = directory / f"{identity}.pending"
    if path.is_symlink():
        raise ValueError("RFC pending-delivery file must not be a symbolic link")
    return path


def _read_pending(path: Optional[Path]) -> Optional[dict]:
    if path is None or not path.is_file() or path.is_symlink():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        return None
    if not isinstance(value, dict):
        return None
    prompt_id = value.get("prompt_id")
    host_prompt_id = value.get("host_prompt_id")
    if not isinstance(prompt_id, str) or not ID_RE.fullmatch(prompt_id):
        return None
    if host_prompt_id is not None and (
        not isinstance(host_prompt_id, str) or not ID_RE.fullmatch(host_prompt_id)
    ):
        return None
    return value


def _write_private_file(path: Path, content: str) -> None:
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")
    descriptor = os.open(str(temporary), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            try:
                os.fsync(stream.fileno())
            except OSError:
                pass
        os.replace(temporary, path)
    except BaseException:
        try:
            temporary.unlink()
        except OSError:
            pass
        raise
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass  # Windows ACLs are managed by the host.


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


def _discard_pending(root: Path, session_id: str, pending_path: Path) -> None:
    pending = _read_pending(pending_path)
    if pending:
        old_token = _canary_path(root, session_id, pending["prompt_id"], create=False)
        if old_token is not None:
            try:
                old_token.unlink()
            except OSError:
                pass
    try:
        pending_path.unlink()
    except FileNotFoundError:
        pass


def _new_prompt_id() -> str:
    return f"rfc-{time.time_ns()}-{secrets.token_hex(8)}"


def handle_user_prompt_submit(event: dict) -> Optional[dict]:
    """Return Claude's documented additionalContext response, or None for a no-op."""
    if os.environ.get(DISABLE_ENV) == "1" or os.environ.get(RFC_DISABLE_ENV) == "1":
        return None
    root = _workspace(event)
    session_id = _session_id(event)
    valid_prompt_id, host_prompt_id = _host_prompt_id(event)
    if root is None or session_id is None or not valid_prompt_id or not _database_ready(root):
        return None

    prompt_id = host_prompt_id or _new_prompt_id()
    fabric = ContextFabric(root)
    fabric.ensure_session(session_id)
    token_path = _canary_path(root, session_id, prompt_id, create=True)
    pending_path = _pending_path(root, session_id, create=True)
    if token_path is None or pending_path is None:
        return None

    previous = _read_pending(pending_path)
    if previous:
        if previous.get("host_prompt_id") == host_prompt_id and previous.get("prompt_id") == prompt_id:
            # A duplicate invocation for the same host prompt must not rotate its canary.
            if token_path.is_file():
                return None
        _discard_pending(root, session_id, pending_path)

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
        pending_data = json.dumps(
            {"prompt_id": prompt_id, "host_prompt_id": host_prompt_id},
            separators=(",", ":"),
        )
        _write_private_file(pending_path, pending_data)
    except PromptAlreadyPrepared:
        try:
            token_path.unlink()
        except OSError:
            pass
        return None
    except BaseException:
        for path in (token_path, pending_path):
            try:
                path.unlink()
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
    session_id = _session_id(event)
    valid_prompt_id, host_prompt_id = _host_prompt_id(event)
    response = event.get("last_assistant_message")
    if (
        root is None or session_id is None or not valid_prompt_id
        or not isinstance(response, str) or not response or not _database_ready(root)
    ):
        return None

    pending_path = _pending_path(root, session_id, create=False)
    pending = _read_pending(pending_path)
    if pending:
        prepared_host_id = pending.get("host_prompt_id")
        if prepared_host_id is not None and host_prompt_id is not None and prepared_host_id != host_prompt_id:
            return None
        # If the submit event had no prompt_id, its private generated ID is
        # authoritative for this in-order Stop event even if Stop supplies one.
        prompt_id = pending["prompt_id"]
    elif host_prompt_id is not None:
        prompt_id = host_prompt_id
    else:
        return None

    token_path = _canary_path(root, session_id, prompt_id, create=False)
    if token_path is None or not token_path.is_file() or token_path.is_symlink():
        return None
    token = token_path.read_text(encoding="utf-8").strip()
    if not token:
        return None

    fabric = ContextFabric(root)
    result = fabric.record_response(session_id, prompt_id, response, token)
    token_path.unlink()
    if pending_path is not None:
        try:
            pending_path.unlink()
        except FileNotFoundError:
            pass
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
