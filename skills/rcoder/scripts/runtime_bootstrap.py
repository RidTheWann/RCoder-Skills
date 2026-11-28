#!/usr/bin/env python3
"""Best-effort launcher for the optional Rust RCoder Runtime companion.

The local MCP server is the activation signal: when this process starts, the
companion attaches to its PID and remains alive until the MCP process exits.
This module never writes to MCP stdout and never blocks MCP startup.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, Mapping, Optional, Sequence


_RUNTIME_ENV_KEYS = {
    "PATH", "HOME", "USERPROFILE", "SYSTEMROOT", "WINDIR",
    "TEMP", "TMP", "TMPDIR", "LOCALAPPDATA", "APPDATA", "LANG", "LC_ALL",
}


def runtime_environment(source: Optional[Mapping[str, str]] = None) -> dict[str, str]:
    """Pass only operating-system basics; never copy host API keys into the sidecar."""
    environment = os.environ if source is None else source
    return {key: value for key, value in environment.items() if key.upper() in _RUNTIME_ENV_KEYS}


def start_runtime_companion(
    project_root: Path,
    *,
    runtime_binary: Optional[str] = None,
    parent_pid: Optional[int] = None,
    platform: Optional[str] = None,
    popen: Optional[Callable] = None,
) -> bool:
    """Start the Runtime sidecar when installed; fail open when unavailable."""
    if os.environ.get("RCODER_RUNTIME_DISABLE", "").strip().lower() in {"1", "true", "yes", "on"}:
        return False

    explicit_binary = runtime_binary or os.environ.get("RCODER_RUNTIME_PATH")
    binary = explicit_binary or shutil.which("rcoder-runtime")
    if not binary:
        name = "rcoder-runtime.exe" if os.name == "nt" else "rcoder-runtime"
        for directory in (".rcoder/bin", ".local/bin"):
            home = os.environ.get("HOME") or os.environ.get("USERPROFILE")
            if not home:
                break
            candidate = Path(home) / directory / name
            if candidate.is_file():
                binary = str(candidate)
                break
    if not binary:
        return False

    try:
        root = project_root.expanduser().resolve(strict=True)
        if not root.is_dir():
            return False
    except (OSError, RuntimeError):
        return False

    actual_platform = platform or sys.platform
    command: Sequence[str] = (
        binary,
        "attach",
        "--project",
        str(root),
        "--parent-pid",
        str(parent_pid if parent_pid is not None else os.getpid()),
    )
    launch = popen or subprocess.Popen
    options = {
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "close_fds": True,
        "env": runtime_environment(),
    }
    if actual_platform == "win32":
        options["creationflags"] = 0x00000008 | 0x08000000  # DETACHED_PROCESS | CREATE_NO_WINDOW
    else:
        options["start_new_session"] = True

    try:
        launch(list(command), **options)
        return True
    except (OSError, ValueError):
        if os.environ.get("RCODER_RUNTIME_DEBUG") == "1":
            print("RCoder Runtime companion could not be started; MCP remains available.",
                  file=sys.stderr)
        return False
