#!/usr/bin/env python3
"""Regression test: interactive installer menus must not repeat option numbers.

Drives the real PowerShell launcher (needs pwsh) and the Node terminal manager (needs a POSIX
pty) through a full install, then checks every consecutive block of numbered lines. A block
that repeats or skips a number (for example RSaver/RScan listed as 1-2 right before the
"Both / RSaver only / RScan only / Neither" choices) fails the test. Also checks that the MCP
step is offered and that the result is written. Skips a driver whose runtime is unavailable.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NUMBERED = re.compile(r"^\s*(\d+)\.\s+\S")


def numbered_blocks(text):
    blocks, current = [], []
    for line in text.replace("\r", "").splitlines():
        match = NUMBERED.match(line)
        if match:
            current.append(int(match.group(1)))
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    return blocks


def check_blocks(label, text):
    blocks = numbered_blocks(text)
    assert blocks, f"{label}: no numbered menus found"
    for block in blocks:
        assert len(block) == len(set(block)), f"{label}: duplicate option numbers {block}"
        expected = list(range(1, len(block) + 1))
        if block[-1] == 0:
            expected = list(range(1, len(block))) + [0]
        # the main menu skips nothing but may end with 0; the action list may include 4 after 3
        assert block == expected, f"{label}: option numbers are not sequential {block}"
    joined = "\n".join(map(str, blocks))
    assert any(block == [1, 2, 3, 4] for block in blocks), f"{label}: feature menu missing\n{joined}"
    assert "MCP server" in text, f"{label}: MCP step was not offered"


def run_powershell(temp):
    pwsh = shutil.which("pwsh")
    if not pwsh:
        print("SKIP PowerShell launcher menus (pwsh not installed)")
        return
    project = temp / "ps-project"
    home = temp / "ps-home"
    project.mkdir()
    home.mkdir()
    answers = f"1\n3\n1\n1\n2\n{project}\n0\n"  # install, Cursor, project, both tools, auto MCP
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home))
    done = subprocess.run([pwsh, "-NoLogo", "-NoProfile", "-File", str(ROOT / "launcher" / "RCoder.ps1")],
                          input=answers, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=180, env=env, check=False)
    assert done.returncode == 0, done.stdout + done.stderr
    check_blocks("PowerShell launcher", done.stdout)
    assert (project / ".cursor" / "mcp.json").is_file(), done.stdout
    assert (project / ".cursor" / "skills" / "rcoder" / "scripts" / "rcoder_mcp_setup.py").is_file()
    print("PASS PowerShell launcher menus")


def run_node(temp):
    try:
        import pty
        import select
    except ImportError:
        print("SKIP Node menus (no pty on this platform)")
        return
    if not shutil.which("node"):
        print("SKIP Node menus (node not installed)")
        return
    project = temp / "node-project"
    home = temp / "node-home"
    project.mkdir()
    home.mkdir()
    pid, fd = pty.fork()
    if pid == 0:
        os.execvp("node", ["node", str(ROOT / "scripts" / "rcoder.mjs"), "--interactive",
                           "--home-dir", str(home)])
    output = b""

    def drain(seconds):
        nonlocal output
        end = time.time() + seconds
        while time.time() < end:
            ready, _, _ = select.select([fd], [], [], 0.1)
            if ready:
                try:
                    output += os.read(fd, 65536)
                except OSError:
                    return

    for answer in ("1", "3", "1", "1", "2", str(project), "0"):
        drain(0.8)
        os.write(fd, (answer + "\n").encode())
    drain(2.0)
    try:
        os.waitpid(pid, 0)
    except ChildProcessError:
        pass
    text = re.sub(rb"\x1b\[[0-9;?]*[A-Za-z]", b"", output).decode("utf-8", "replace")
    check_blocks("Node manager", text)
    assert (project / ".cursor" / "mcp.json").is_file(), text
    print("PASS Node terminal manager menus")


def main():
    with tempfile.TemporaryDirectory(prefix="rcoder-menus-") as raw:
        temp = Path(raw)
        run_powershell(temp)
        if os.name != "nt":
            run_node(temp)
        else:
            print("SKIP Node menus (pty tests run on POSIX CI)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
