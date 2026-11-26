#!/usr/bin/env python3
"""Cross-platform runtime resolver and POSIX path canonicalizer for RCoder."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any


def to_posix_rel(path_value: str | Path, workspace_root: Path | None = None) -> str:
    """Convert a Windows or POSIX path into a canonical workspace-relative POSIX string."""
    raw = str(path_value).strip().replace("\\", "/")
    if workspace_root is not None:
        root_resolved = workspace_root.resolve(strict=False)
        candidate = Path(path_value)
        if candidate.is_absolute():
            try:
                raw = candidate.resolve(strict=False).relative_to(root_resolved).as_posix()
            except ValueError:
                raw = candidate.as_posix()
    posix = PurePosixPath(raw).as_posix()
    if posix.startswith("./"):
        posix = posix[2:]
    if posix == ".":
        return ""
    return posix.lstrip("/")


def to_native_path(posix_rel: str, workspace_root: Path) -> Path:
    """Hydrate a canonical POSIX relative path back into an OS-native Path safely."""
    clean = to_posix_rel(posix_rel)
    parts = [part for part in clean.split("/") if part and part != "."]
    if any(part == ".." for part in parts):
        raise ValueError(f"Parent traversal rejected in canonical path: {posix_rel!r}")
    return workspace_root.joinpath(*parts)


def is_usable_python(executable: str) -> bool:
    """Verify that an executable is a real Python >= 3.9 interpreter."""
    normalized = executable.replace("\\", "/").lower()
    if "windowsapps/python" in normalized:
        return False
    try:
        process = subprocess.run(
            [executable, "-c", "import sys; print(int(sys.version_info >= (3, 9)))"],
            capture_output=True, text=True, timeout=4, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return process.returncode == 0 and process.stdout.strip() == "1"


def resolve_python_command() -> list[str]:
    """Return the healthiest Python invocation across Linux, macOS, Windows, and Termux."""
    if sys.executable and is_usable_python(sys.executable):
        return [sys.executable]
    for name in ("python3", "python"):
        found = shutil.which(name)
        if found and is_usable_python(found):
            return [found]
    if os.name == "nt":
        launcher = shutil.which("py")
        if launcher:
            try:
                process = subprocess.run(
                    [launcher, "-3", "-c", "import sys; print(sys.executable)"],
                    capture_output=True, text=True, timeout=4, check=False,
                )
                target = process.stdout.strip()
                if process.returncode == 0 and target and is_usable_python(target):
                    return [target]
            except (OSError, subprocess.SubprocessError):
                pass
    return ["python3"]


def normalize_portable_mcp_config(config: dict[str, Any]) -> dict[str, Any]:
    """Rewrite RCoder MCP entries so repository configs never embed OS-specific absolute paths."""
    servers = config.get("mcpServers")
    if not isinstance(servers, dict):
        return config
    updated = dict(config)
    new_servers: dict[str, Any] = {}
    for name, entry in servers.items():
        if not isinstance(entry, dict):
            new_servers[name] = entry
            continue
        item = dict(entry)
        joined = " ".join([str(item.get("command", "")), *[str(arg) for arg in item.get("args", [])]])
        if "rcoder-mcp" in joined or "rcoder_mcp" in joined:
            item["command"] = "node"
            item["args"] = ["launcher/rcoder-mcp.mjs"]
        new_servers[name] = item
    updated["mcpServers"] = new_servers
    return updated
