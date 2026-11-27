#!/usr/bin/env python3
"""OpenCode V2 lifecycle bridge for RFC Context Fabric and RCoder Runtime.

The OpenCode plugin calls one bounded JSON command per eligible model request
and one command after an assistant execution. This module is transport glue:

- RFC remains the owner of durable context, delivery receipts, and canaries.
- Runtime remains the owner of task contracts and deterministic packets.
- The bridge never creates a task engine or a second context store.

Every command reads a JSON object from stdin and writes one JSON object to
stdout. Invalid input and internal failures produce an empty object; a
supplemental context hook must never block the host.
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
from typing import Any, Dict, Iterable, Iterator, Mapping, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

import context_fabric_host as rfc_host  # noqa: E402
import runtime_task_host  # noqa: E402
from context_fabric import (  # noqa: E402
    DEFAULT_BUDGET_BYTES,
    ID_RE,
    ContextFabric,
    ContextFabricError,
    PromptAlreadyPrepared,
)

MAX_EVENT_BYTES = 2 * 1024 * 1024
MAX_RESPONSE_BYTES = 5_000_000
DEFAULT_CANARY_MAX_AGE_SECONDS = 3600
DEBUG_ENV = "RCODER_OPENCODE_DEBUG"


def _debug(message: str) -> None:
    if os.environ.get(DEBUG_ENV) == "1":
        print(f"opencode-host: {message}", file=sys.stderr)


def _read_event() -> Optional[dict]:
    raw = sys.stdin.buffer.read(MAX_EVENT_BYTES + 1)
    if not raw or len(raw) > MAX_EVENT_BYTES:
        return None
    try:
        event = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None
    return event if isinstance(event, dict) else None


def _workspace(event: Mapping[str, object]) -> Optional[Path]:
    value = event.get("cwd")
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        root = Path(value).expanduser().resolve(strict=True)
    except (OSError, RuntimeError):
        return None
    return root if root.is_dir() else None


def _identifier(event: Mapping[str, object], key: str) -> Optional[str]:
    value = event.get(key)
    return value if isinstance(value, str) and ID_RE.fullmatch(value) else None


def _delivery_identity(session_id: str, prompt_id: str) -> str:
    return hashlib.sha256(f"{session_id}\0{prompt_id}".encode("utf-8")).hexdigest()


def _delivery_paths(
    root: Path, session_id: str, prompt_id: str, *, create: bool
) -> tuple[Optional[Path], Optional[Path]]:
    directory = rfc_host._canary_directory(root, create=create)
    if directory is None:
        return None, None
    stem = _delivery_identity(session_id, prompt_id)
    token_path = directory / f"{stem}.token"
    metadata_path = directory / f"{stem}.json"
    for path in (token_path, metadata_path):
        if path.is_symlink():
            raise ValueError("RFC delivery state must not contain symbolic links")
    return token_path, metadata_path


def _read_metadata(path: Path) -> Optional[dict]:
    if path.is_symlink() or not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        return None
    if not isinstance(value, dict):
        return None
    session_id = value.get("session_id")
    prompt_id = value.get("prompt_id")
    created_at = value.get("created_at")
    if not isinstance(session_id, str) or not ID_RE.fullmatch(session_id):
        return None
    if not isinstance(prompt_id, str) or not ID_RE.fullmatch(prompt_id):
        return None
    if not isinstance(created_at, (int, float)) or created_at < 0:
        return None
    return value


def _iter_deliveries(root: Path, session_id: Optional[str] = None) -> Iterator[tuple[dict, Path, Path]]:
    directory = rfc_host._canary_directory(root, create=False)
    if directory is None:
        return
    for metadata_path in sorted(directory.glob("*.json")):
        if metadata_path.is_symlink():
            continue
        metadata = _read_metadata(metadata_path)
        if metadata is None:
            continue
        if session_id is not None and metadata["session_id"] != session_id:
            continue
        token_path = metadata_path.with_suffix(".token")
        if token_path.is_symlink() or not token_path.is_file():
            continue
        yield metadata, metadata_path, token_path


def cleanup_deliveries(
    root: Path,
    *,
    session_id: Optional[str] = None,
    now: Optional[float] = None,
    max_age_seconds: int = DEFAULT_CANARY_MAX_AGE_SECONDS,
) -> Dict[str, int]:
    """Remove completed or interrupted private canaries without touching SQLite.

    Session cleanup removes every delivery for that session. Age cleanup keeps
    a just-created delivery available across repeated host events while still
    collecting interrupted prompts from an earlier process.
    """
    if max_age_seconds < 0:
        raise ValueError("max_age_seconds must be non-negative")
    timestamp = time.time() if now is None else float(now)
    removed_deliveries = 0
    removed_orphans = 0
    for metadata, metadata_path, token_path in list(_iter_deliveries(root, session_id)):
        age = timestamp - float(metadata["created_at"])
        if session_id is None and age < max_age_seconds:
            continue
        for path in (metadata_path, token_path):
            try:
                path.unlink()
            except FileNotFoundError:
                pass
            except OSError as exc:
                _debug(f"could not remove {path.name}: {type(exc).__name__}")
        removed_deliveries += 1

    directory = rfc_host._canary_directory(root, create=False)
    if directory is not None and session_id is None:
        for token_path in directory.glob("*.token"):
            if token_path.is_symlink():
                continue
            metadata_path = token_path.with_suffix(".json")
            if metadata_path.is_file():
                continue
            try:
                age = timestamp - token_path.stat().st_mtime
            except OSError:
                continue
            if age < max_age_seconds:
                continue
            try:
                token_path.unlink()
                removed_orphans += 1
            except OSError:
                pass
    return {
        "removed_deliveries": removed_deliveries,
        "removed_orphan_tokens": removed_orphans,
    }


def _flag_disabled(event: Mapping[str, object], key: str, *env_names: str) -> bool:
    if event.get(key) is True:
        return True
    return any(os.environ.get(name) == "1" for name in env_names)


def _runtime_environment(event: Mapping[str, object]) -> Dict[str, str]:
    """Build the allowlisted child environment without inheriting provider keys."""
    environment: Dict[str, str] = dict(os.environ)
    if _flag_disabled(event, "runtime_disabled", "RCODER_RUNTIME_DISABLE", "RCODER_HOOKS_DISABLE"):
        environment["RCODER_RUNTIME_DISABLE"] = "1"
    runtime_path = event.get("runtime_path")
    if isinstance(runtime_path, str) and runtime_path.strip():
        environment["RCODER_RUNTIME_PATH"] = runtime_path.strip()
    return environment


def prepare_rfc_context(event: Mapping[str, object]) -> Optional[Dict[str, Any]]:
    """Create a unique RFC delivery and return the payload for this request."""
    if _flag_disabled(event, "rfc_disabled", rfc_host.DISABLE_ENV, rfc_host.RFC_DISABLE_ENV):
        return None
    root = _workspace(event)
    session_id = _identifier(event, "session_id")
    request_id = _identifier(event, "request_id")
    if root is None or session_id is None or request_id is None or not rfc_host._database_ready(root):
        return None

    cleanup_deliveries(root, now=time.time())

    token_path, metadata_path = _delivery_paths(root, session_id, request_id, create=True)
    if token_path is None or metadata_path is None:
        return None
    if token_path.exists() or metadata_path.exists():
        _debug("duplicate OpenCode request identity")
        return None

    token = secrets.token_urlsafe(24)
    fabric = ContextFabric(root)
    fabric.ensure_session(session_id)
    try:
        rfc_host._write_private_token(token_path, token)
        rfc_host._write_private_file(
            metadata_path,
            json.dumps(
                {
                    "schema": "rcoder-rfc-delivery-v1",
                    "session_id": session_id,
                    "prompt_id": request_id,
                    "created_at": time.time(),
                },
                separators=(",", ":"),
            ),
        )
        built = fabric.build_context(
            session_id,
            request_id,
            budget_bytes=DEFAULT_BUDGET_BYTES,
            ack_token=token,
        )
    except PromptAlreadyPrepared:
        for path in (token_path, metadata_path):
            try:
                path.unlink()
            except OSError:
                pass
        return None
    except BaseException:
        for path in (token_path, metadata_path):
            try:
                path.unlink()
            except OSError:
                pass
        raise

    return {
        "prompt_id": request_id,
        "text": built["text"],
        "payload_sha256": built["payload_sha256"],
        "payload_bytes": built["payload_bytes"],
    }


def runtime_context(event: Mapping[str, object]) -> Optional[Dict[str, Any]]:
    """Return the validated active Runtime packet through the existing adapter."""
    root = _workspace(event)
    if root is None:
        return None
    try:
        response = runtime_task_host.build_hook_response(
            {"hook_event_name": "UserPromptSubmit", "cwd": str(root)},
            environment=_runtime_environment(event),
        )
    except Exception as exc:  # supplemental context must fail open
        _debug(f"runtime context failed: {type(exc).__name__}")
        return None
    if not isinstance(response, dict):
        return None
    specific = response.get("hookSpecificOutput")
    if not isinstance(specific, dict):
        return None
    text = specific.get("additionalContext")
    if not isinstance(text, str) or not text.strip():
        return None
    return {"text": text}


def handle_context(event: Mapping[str, object]) -> Dict[str, Any]:
    """Build the independent RFC and Runtime payloads for one model request."""
    result: Dict[str, Any] = {}
    root = _workspace(event)
    if root is None:
        return result

    try:
        runtime = runtime_context(event)
    except Exception as exc:
        _debug(f"runtime context skipped: {type(exc).__name__}")
        runtime = None
    if runtime is not None:
        result["runtime"] = runtime

    try:
        rfc = prepare_rfc_context(event)
    except Exception as exc:
        _debug(f"RFC context skipped: {type(exc).__name__}")
        rfc = None
    if rfc is not None:
        result["rfc"] = rfc
    return result


def handle_response(event: Mapping[str, object]) -> Dict[str, Any]:
    """Match raw OpenCode assistant text to exactly one prepared delivery."""
    if _flag_disabled(event, "rfc_disabled", rfc_host.DISABLE_ENV, rfc_host.RFC_DISABLE_ENV):
        return {}
    root = _workspace(event)
    session_id = _identifier(event, "session_id")
    request_id = _identifier(event, "request_id")
    response = event.get("response")
    if (
        root is None
        or session_id is None
        or not isinstance(response, str)
        or not response.strip()
        or not rfc_host._database_ready(root)
    ):
        return {}
    if len(response.encode("utf-8")) > MAX_RESPONSE_BYTES:
        _debug("assistant response exceeds the RFC safety limit")
        return {}

    deliveries: list[tuple[dict, str]] = []
    for metadata, _metadata_path, token_path in _iter_deliveries(root, session_id):
        try:
            token = token_path.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if token:
            deliveries.append((metadata, token))
    if not deliveries:
        return {}

    if request_id is not None:
        selected = [item for item in deliveries if item[0]["prompt_id"] == request_id]
        if not selected:
            _debug("assistant response has no matching delivery")
            return {}
        conflicts = [
            token
            for metadata, token in deliveries
            if metadata["prompt_id"] != request_id and token in response
        ]
        if conflicts:
            _debug("assistant response acknowledged a different delivery")
            return {"ambiguous": True, "matches": len(conflicts)}
        metadata, token = selected[0]
    else:
        matching = [(metadata, token) for metadata, token in deliveries if token in response]
        if len(matching) > 1:
            # A response must not acknowledge two independent deliveries.
            _debug("ambiguous canary match rejected")
            return {"ambiguous": True, "matches": len(matching)}
        if matching:
            metadata, token = matching[0]
        else:
            metadata, token = max(deliveries, key=lambda item: float(item[0]["created_at"]))

    fabric = ContextFabric(root)
    try:
        recorded = fabric.record_response(
            session_id, metadata["prompt_id"], response, token
        )
    except (ContextFabricError, OSError, ValueError):
        return {}
    return {
        "recorded": True,
        "acknowledged": bool(recorded.get("acknowledged")),
        "prompt_id": metadata["prompt_id"],
    }


def handle_cleanup(event: Mapping[str, object]) -> Dict[str, Any]:
    root = _workspace(event)
    if root is None:
        return {}
    session_id = _identifier(event, "session_id")
    cleanup_deliveries(root, session_id=session_id)
    return {"cleaned": True}


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("context", "response", "cleanup"))
    args = parser.parse_args(argv)
    output: Dict[str, Any] = {}
    try:
        event = _read_event()
        if event is not None:
            if args.command == "context":
                output = handle_context(event)
            elif args.command == "response":
                output = handle_response(event)
            else:
                output = handle_cleanup(event)
    except Exception as exc:  # host hooks must fail open
        _debug(f"ignored {type(exc).__name__}")
        output = {}
    print(json.dumps(output, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
