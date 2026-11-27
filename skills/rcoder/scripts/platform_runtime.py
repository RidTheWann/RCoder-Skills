#!/usr/bin/env python3
"""Cross-platform runtime resolver and POSIX path canonicalizer for RCoder."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
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


def portable_temp_root(namespace: str) -> Path:
    """Return a per-OS temporary namespace that honors TMPDIR/TEMP."""
    root = Path(tempfile.gettempdir()) / namespace
    root.mkdir(parents=True, exist_ok=True)
    return root


def resolve_node_command() -> list[str]:
    """Return a Node.js invocation string vector for the current OS."""
    for name in ("node", "node.exe"):
        found = shutil.which(name)
        if found:
            return [found]
    return ["node"]


def resolve_host_command(name: str = "opencode") -> list[str]:
    """Return an executable vector, wrapping Windows script launchers safely."""
    found = shutil.which(name)
    if not found:
        return []
    path = Path(found)
    if path.suffix.lower() in {".cmd", ".bat"}:
        return ["cmd.exe", "/c", str(path)]
    return [str(path)]


def isolated_host_environment(
    workspace: Path,
    *,
    mock_key: str,
    python_command: list[str] | None = None,
) -> dict[str, str]:
    """Build a sanitized host environment isolated to one fixture workspace.

    Provider credentials and ambient OpenCode session state are removed. The
    remaining keys follow the host's per-OS configuration conventions.
    """
    environment = dict(os.environ)
    for key in list(environment):
        upper = key.upper()
        if any(fragment in upper for fragment in ("OPENAI_API", "ANTHROPIC_API", "GOOGLE_API")):
            environment.pop(key, None)
        if upper.startswith("OPENCODE_") or upper in ("OPENCODE", "AI_AGENT"):
            environment.pop(key, None)
    python = python_command or resolve_python_command()
    environment.update({
        "MOCK_API_KEY": mock_key,
        "RCODER_OPENCODE_DEBUG": "1",
        "RCODER_PYTHON": python[0],
        "HOME": str(workspace),
    })
    if os.name == "nt":
        environment.update({
            "APPDATA": str(workspace / "appdata"),
            "LOCALAPPDATA": str(workspace / "localappdata"),
            "USERPROFILE": str(workspace),
            "TEMP": str(workspace / "tmp"),
            "TMP": str(workspace / "tmp"),
        })
    else:
        environment.update({
            "XDG_CONFIG_HOME": str(workspace / "xdg" / "config"),
            "XDG_DATA_HOME": str(workspace / "xdg" / "data"),
            "XDG_STATE_HOME": str(workspace / "xdg" / "state"),
            "PWD": str(workspace),
            "OLDPWD": str(workspace),
        })
    return environment


def link_or_copy(source: Path, destination: Path) -> None:
    """Prefer a symlink; fall back to a bounded copy where symlinks are unavailable."""
    try:
        destination.symlink_to(source, target_is_directory=source.is_dir())
        return
    except (OSError, NotImplementedError, AttributeError):
        pass
    if source.is_dir():
        shutil.copytree(source, destination, symlinks=True)
    else:
        shutil.copy2(source, destination)


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


def detect_runtime_environment(workspace_root: Path | None = None) -> dict[str, Any]:
    """Return normalized cross-platform runtime telemetry (Linux, Windows, macOS, Termux)."""
    import platform

    root = (workspace_root or Path.cwd()).resolve(strict=False)
    is_termux = bool(os.environ.get("TERMUX_VERSION")) or "com.termux" in str(
        os.environ.get("PREFIX", "")
    )
    system_name = platform.system().lower()
    runtime_id = "android-termux" if is_termux else system_name
    grun_bin = shutil.which("grun")
    node_bin = shutil.which("node")
    py_cmd = resolve_python_command()

    rcoder_dir = root / ".rcoder"
    lessons_count = 0
    lessons_file = rcoder_dir / "lessons.jsonl"
    if lessons_file.is_file():
        try:
            lessons_count = sum(
                1 for line in lessons_file.read_text(encoding="utf-8", errors="replace").splitlines()
                if line.strip()
            )
        except OSError:
            lessons_count = 0

    active_leases = 0
    leases_file = rcoder_dir / "leases.json"
    if leases_file.is_file():
        try:
            import json as _json
            import time as _time
            raw_leases = _json.loads(leases_file.read_text(encoding="utf-8"))
            if isinstance(raw_leases, dict):
                now = _time.time()
                active_leases = sum(
                    1 for meta in raw_leases.values()
                    if isinstance(meta, dict) and float(meta.get("expires_at", 0)) > now
                )
        except Exception:  # noqa: BLE001
            active_leases = 0

    stack_markers = [
        marker for marker in (
            "package.json", "pyproject.toml", "requirements.txt", "Cargo.toml", "go.mod",
            "plugin.json", "gemini-extension.json", ".claude-plugin/plugin.json",
            ".codex-plugin/plugin.json", ".opencode/plugins/rcoder.js",
        )
        if (root / marker).exists()
    ]

    return {
        "runtime": runtime_id,
        "os": system_name,
        "arch": platform.machine(),
        "python_version": platform.python_version(),
        "python_resolved": bool(py_cmd),
        "node_available": bool(node_bin),
        "is_termux": is_termux,
        "glibc_runner_available": bool(grun_bin),
        "stack_markers": stack_markers,
        "rcoder_state": {
            "initialized": rcoder_dir.is_dir(),
            "lessons_count": lessons_count,
            "active_leases": active_leases,
        },
    }
