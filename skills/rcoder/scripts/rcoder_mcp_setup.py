#!/usr/bin/env python3
"""Show, apply, and verify the RCoder MCP server configuration for an agent host.

Used by the PowerShell, Node, and POSIX installers so every route behaves the same.
Dependency-free (standard library only). It never opens network connections.

Safety rules for `apply`:
  * only the `rcoder` entry is added; every other key in the file is preserved
  * an existing config that is not strict JSON (for example JSONC with comments) is never
    rewritten; the snippet is printed for manual merge instead
  * an existing, different `rcoder` entry is never overwritten
  * the file is backed up before it changes, written atomically, and refused if the path
    leaves the selected base directory or crosses a symbolic link
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SERVER_NAME = "rcoder"
SERVER_SCRIPT = "rcoder_mcp_modern.py"

# kind: how the host stores servers.  project/user: config path relative to the base dir
# (None = no file route; the snippet is shown instead).
HOSTS = {
    "claude-code": {"kind": "mcpServers", "project": ".mcp.json", "user": None, "cli": True},
    "cursor": {"kind": "mcpServers", "project": ".cursor/mcp.json", "user": ".cursor/mcp.json"},
    "gemini-cli": {"kind": "mcpServers", "project": ".gemini/settings.json",
                   "user": ".gemini/settings.json"},
    "copilot": {"kind": "vscode", "project": ".vscode/mcp.json", "user": None},
    "opencode": {"kind": "opencode", "project": "opencode.json",
                 "user": ".config/opencode/opencode.json"},
    "codex": {"kind": "toml", "project": None, "user": ".codex/config.toml"},
}
GENERIC = {"kind": "mcpServers", "project": None, "user": None}


def host_info(host: str) -> dict:
    return HOSTS.get(host, GENERIC)


def default_command() -> tuple[str, list[str]]:
    """Interpreter command a host can use to start the server."""
    if os.name == "nt":
        if shutil.which("python"):
            return "python", []
        if shutil.which("py"):
            return "py", ["-3"]
        return "python", []
    if shutil.which("python3"):
        return "python3", []
    return "python", []


def server_args(server: Path, base: Path, scope: str, pre: list[str]) -> list[str]:
    """Project scope uses a relative script path (safe to commit); user scope is absolute."""
    script = server.resolve()
    if scope == "project":
        try:
            script_text = script.relative_to(base.resolve()).as_posix()
        except ValueError:
            script_text = str(script)
    else:
        script_text = str(script)
    return [*pre, script_text, "--root", "."]


def entry_for(info: dict, command: str, args: list[str]) -> dict:
    kind = info["kind"]
    if kind == "opencode":
        return {"type": "local", "command": [command, *args], "enabled": True}
    entry = {"command": command, "args": args}
    if kind == "vscode":
        entry = {"type": "stdio", **entry}
    return entry


def container_key(info: dict) -> str:
    return {"vscode": "servers", "opencode": "mcp"}.get(info["kind"], "mcpServers")


def snippet(host: str, scope: str, command: str, args: list[str]) -> str:
    info = host_info(host)
    if host == "claude-code":
        quoted = " ".join(f'"{part}"' if " " in part else part for part in [command, *args])
        return f"claude mcp add {SERVER_NAME} --scope {scope} -- {quoted}"
    if info["kind"] == "toml":
        rendered = ", ".join(json.dumps(part) for part in args)
        return (f"[mcp_servers.{SERVER_NAME}]\ncommand = {json.dumps(command)}\n"
                f"args = [{rendered}]")
    document = {container_key(info): {SERVER_NAME: entry_for(info, command, args)}}
    if info["kind"] == "opencode":
        document = {"$schema": "https://opencode.ai/config.json", **document}
    return json.dumps(document, indent=2)


def config_path(host: str, scope: str, base: Path) -> Path | None:
    relative = host_info(host).get(scope)
    return (base / relative) if relative else None


def assert_inside(base: Path, path: Path) -> None:
    base_real = Path(os.path.abspath(base))
    target = Path(os.path.abspath(path))
    try:
        relative = target.relative_to(base_real)
    except ValueError:
        raise RuntimeError(f"refusing to write outside the selected directory: {path}")
    current = base_real
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise RuntimeError(f"refusing to follow a symbolic link: {current}")


def write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(prefix=".rcoder-mcp-", dir=str(path.parent))
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
        os.replace(temp_name, path)
    except BaseException:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
        raise


def backup(path: Path) -> Path:
    stamp = time.strftime("%Y%m%dT%H%M%S", time.gmtime())
    saved = path.with_name(f"{path.name}.rcoder-backup-{stamp}")
    counter = 0
    while saved.exists():
        counter += 1
        saved = path.with_name(f"{path.name}.rcoder-backup-{stamp}-{counter}")
    shutil.copy2(path, saved)
    return saved


def apply_json(host: str, path: Path, base: Path, entry: dict) -> tuple[str, str]:
    info = host_info(host)
    key = container_key(info)
    assert_inside(base, path)
    data: dict = {}
    existed = path.is_file()
    if existed:
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except (ValueError, OSError) as error:
            return "manual", f"{path} is not strict JSON ({error}); it was left untouched"
        if not isinstance(data, dict):
            return "manual", f"{path} does not contain a JSON object; it was left untouched"
    servers = data.get(key)
    if servers is None:
        servers = {}
    if not isinstance(servers, dict):
        return "manual", f'"{key}" in {path} is not an object; it was left untouched'
    current = servers.get(SERVER_NAME)
    if current is not None:
        if current == entry:
            return "already", f"already configured in {path}"
        return "conflict", (f'{path} already has a different "{SERVER_NAME}" entry; '
                            "it was left untouched")
    if info["kind"] == "opencode" and not existed:
        data = {"$schema": "https://opencode.ai/config.json"}
    servers = copy.deepcopy(servers)
    servers[SERVER_NAME] = entry
    data[key] = servers
    saved = backup(path) if existed else None
    write_atomic(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    note = f"added to {path}"
    if saved:
        note += f" (backup: {saved.name})"
    return "applied", note


def apply_toml(path: Path, base: Path, command: str, args: list[str]) -> tuple[str, str]:
    assert_inside(base, path)
    existing = path.read_text(encoding="utf-8-sig") if path.is_file() else ""
    if f"[mcp_servers.{SERVER_NAME}]" in existing:
        return "already", f"a [mcp_servers.{SERVER_NAME}] table already exists in {path}"
    block = snippet("codex", "user", command, args)
    saved = backup(path) if path.is_file() else None
    separator = "" if not existing or existing.endswith("\n\n") else (
        "\n" if existing.endswith("\n") else "\n\n")
    write_atomic(path, existing + separator + block + "\n")
    note = f"added to {path}"
    if saved:
        note += f" (backup: {saved.name})"
    return "applied", note


def apply_claude_cli(scope: str, command: str, args: list[str]) -> tuple[str, str]:
    claude = shutil.which("claude")
    if not claude:
        return "manual", "the `claude` command was not found on PATH"
    done = subprocess.run([claude, "mcp", "add", SERVER_NAME, "--scope", scope, "--",
                           command, *args], capture_output=True, text=True, timeout=60,
                          check=False)
    output = (done.stdout + done.stderr).strip()
    if done.returncode == 0:
        return "applied", "registered with `claude mcp add`"
    if "already exists" in output.lower():
        return "already", "already registered with Claude Code"
    return "manual", f"`claude mcp add` failed: {output[:200]}"


def verify_server(server: Path, root: Path) -> tuple[bool, str]:
    """Start the server, run initialize + tools/list, and count the tools."""
    requests = [
        {"jsonrpc": "2.0", "id": 0, "method": "initialize",
         "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                    "clientInfo": {"name": "rcoder-setup", "version": "0"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
    ]
    try:
        done = subprocess.run(
            [sys.executable, str(server), "--root", str(root)],
            input="\n".join(json.dumps(item) for item in requests) + "\n",
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        return False, f"server did not start: {error}"
    replies = {}
    for line in done.stdout.splitlines():
        try:
            item = json.loads(line)
        except ValueError:
            continue
        if isinstance(item, dict) and "id" in item:
            replies[item["id"]] = item
    tools = replies.get(1, {}).get("result", {}).get("tools")
    if replies.get(0, {}).get("result") is None or not isinstance(tools, list):
        return False, f"unexpected server output (exit {done.returncode}): {done.stderr[:200]}"
    return True, f"server answers MCP requests ({len(tools)} tools available)"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("action", choices=["show", "apply", "verify", "hosts"])
    parser.add_argument("--host", default="generic",
                        help="target id such as claude-code, codex, cursor, gemini-cli, copilot, "
                             "opencode (anything else prints the generic mcpServers JSON)")
    parser.add_argument("--scope", choices=["project", "user"], default="project")
    parser.add_argument("--base", default=".", help="project directory (project scope) or home")
    parser.add_argument("--server", default=str(Path(__file__).resolve().with_name(SERVER_SCRIPT)),
                        help="path of the installed rcoder_mcp_modern.py")
    parser.add_argument("--command", default="auto",
                        help="interpreter the host runs (default: auto-detect)")
    parser.add_argument("--dry-run", action="store_true", help="apply: report only")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.action == "hosts":
        for name in sorted(HOSTS):
            info = HOSTS[name]
            routes = [scope for scope in ("project", "user")
                      if info.get(scope) or (info.get("cli") and scope == "user")]
            print(f"{name}: auto-setup for {', '.join(routes) or 'none (snippet only)'}")
        return 0

    base = Path(args.base).resolve()
    server = Path(args.server)
    if not server.is_file():
        print(f"ERROR: MCP server not found: {server}", file=sys.stderr)
        return 2
    if args.action == "verify":
        ok, message = verify_server(server, base)
        print(("OK: " if ok else "FAILED: ") + message)
        return 0 if ok else 1

    if args.command == "auto":
        command, pre = default_command()
    else:
        command, pre = args.command, []
    arguments = server_args(server, base, args.scope, pre)
    info = host_info(args.host)

    if args.action == "show":
        print(f"MCP server config for {args.host} ({args.scope} scope):")
        print(snippet(args.host, args.scope, command, arguments))
        path = config_path(args.host, args.scope, base)
        if path:
            print(f"-> paste it into: {path}")
        elif args.host in HOSTS and not info.get(args.scope) and not info.get("cli"):
            print("-> this host has no per-file route for this scope; use its MCP settings page")
        return 0

    # apply
    path = config_path(args.host, args.scope, base)
    try:
        if args.dry_run:
            where = path if path else "the host CLI/settings"
            print(f"DRY RUN: would add the {SERVER_NAME} MCP server to {where}")
            return 0
        if info.get("cli") and args.scope == "user":
            status, note = apply_claude_cli(args.scope, command, arguments)
        elif path is None:
            status, note = "manual", "no automatic route for this host/scope"
        elif info["kind"] == "toml":
            status, note = apply_toml(path, base, command, arguments)
        else:
            status, note = apply_json(args.host, path, base,
                                      entry_for(info, command, arguments))
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        status, note = "manual", str(error)

    print(f"[{status}] {args.host}: {note}")
    if status in {"applied", "already"}:
        ok, message = verify_server(server, base)
        print(("OK: " if ok else "WARNING: ") + message)
        return 0 if ok else 1
    print("Paste this manually instead:")
    print(snippet(args.host, args.scope, command, arguments))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
