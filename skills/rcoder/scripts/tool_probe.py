#!/usr/bin/env python3
"""Dependency-free tool discovery, verification, and bounded fallback execution.

A skill file is not an installed executable. This helper verifies that a tool
exists before use, executes it with a hard timeout and bounded output capture,
checks output validity and version, and falls back only to explicitly listed
alternatives. It never retries the same command with the same arguments: a
retry requires a changed condition supplied by the caller, so infinite retry
loops cannot occur.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys

DEFAULT_TIMEOUT = 20.0
MAX_OUTPUT = 65536


def resolve(candidates: list[str]) -> str | None:
    """Return the first candidate executable resolvable on PATH."""
    for candidate in candidates:
        if not candidate:
            continue
        found = shutil.which(candidate)
        if found:
            return found
    return None


def _text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    return value


def _bounded(value, limit: int) -> tuple[str, bool]:
    text = _text(value)
    if len(text) <= limit:
        return text, False
    return text[:limit], True


def run(command: list[str], timeout: float = DEFAULT_TIMEOUT,
        max_output: int = MAX_OUTPUT) -> dict:
    """Execute one command once. No implicit retry. Returns a structured verdict."""
    verdict = {
        "invoked": False, "command": list(command), "exit_code": None,
        "stdout": "", "stderr": "", "timed_out": False, "error": None, "pid": None,
        "truncated_stdout": False, "truncated_stderr": False,
    }
    if not command or not shutil.which(command[0]):
        verdict["error"] = "executable not found"
        return verdict
    limit = max(1, int(max_output))
    kwargs = {"stdout": subprocess.PIPE, "stderr": subprocess.PIPE}
    if os.name == "posix":
        kwargs["start_new_session"] = True
    try:
        proc = subprocess.Popen(command, text=True, **kwargs)
        verdict["pid"] = proc.pid
    except (OSError, ValueError) as error:
        verdict["error"] = f"execution failed: {error}"
        return verdict
    try:
        out, err = proc.communicate(timeout=timeout)
        verdict.update({"invoked": True, "exit_code": proc.returncode})
    except subprocess.TimeoutExpired as error:
        if os.name == "posix":
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                proc.kill()
        else:
            proc.kill()
        try:
            out, err = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            out, err = error.stdout, error.stderr
        verdict.update({"invoked": True, "timed_out": True, "error": "timeout"})
    except (OSError, ValueError) as error:
        verdict["error"] = f"execution failed: {error}"
        return verdict
    out, truncated_out = _bounded(out, limit)
    err, truncated_err = _bounded(err, limit)
    verdict.update({
        "stdout": out, "stderr": err,
        "truncated_stdout": truncated_out, "truncated_stderr": truncated_err,
    })
    return verdict


def valid_output(verdict: dict, expect_json: bool) -> bool:
    if not verdict["invoked"] or verdict["timed_out"] or verdict["exit_code"] != 0:
        return False
    if not expect_json:
        return True
    try:
        json.loads(verdict["stdout"])
        return True
    except (json.JSONDecodeError, TypeError):
        return False


def version_of(verdict: dict) -> str | None:
    if not valid_output(verdict, False):
        return None
    for line in (_text(verdict.get("stdout")) + "\n" + _text(verdict.get("stderr"))).splitlines():
        line = line.strip()
        if line:
            return line[:200]
    return None


def version_probe(candidates: list[str], flags: list[str] | None = None,
                  timeout: float = DEFAULT_TIMEOUT,
                  max_output: int = MAX_OUTPUT) -> dict:
    """Try each candidate once with version flags; return the first parsed version."""
    flags = list(flags or ["--version"])
    attempts = []
    for candidate in candidates:
        found = shutil.which(candidate)
        if not found:
            attempts.append({"candidate": candidate, "reason": "not installed",
                             "invoked": False, "version": None})
            continue
        verdict = run([found, *flags], timeout, max_output)
        version = version_of(verdict)
        attempts.append({"candidate": found, "invoked": verdict["invoked"],
                         "exit_code": verdict["exit_code"], "timed_out": verdict["timed_out"],
                         "error": verdict["error"], "version": version})
        if version is not None:
            return {"ok": True, "tool_used": found, "version": version,
                    "candidates": list(candidates), "attempts": attempts, "result": verdict}
    return {"ok": False, "tool_used": None, "version": None,
            "candidates": list(candidates), "attempts": attempts, "result": None}


def chain(candidates: list[str], args: list[str], timeout: float = DEFAULT_TIMEOUT,
          expect_json: bool = False, max_output: int = MAX_OUTPUT) -> dict:
    """Try each candidate at most once; return the first usable result."""
    attempts = []
    for candidate in candidates:
        command = [candidate, *args]
        found = shutil.which(candidate)
        if not found:
            attempts.append({"candidate": candidate, "reason": "not installed", "invoked": False})
            continue
        verdict = run(command, timeout, max_output)
        attempts.append({"candidate": found, **{k: verdict[k] for k in ("invoked", "exit_code", "timed_out", "error")}})
        if valid_output(verdict, expect_json):
            return {
                "ok": True, "tool_used": found, "candidates": list(candidates),
                "attempts": attempts, "result": verdict,
            }
    return {
        "ok": False, "tool_used": None, "candidates": list(candidates),
        "attempts": attempts, "result": None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("resolve", "run", "chain", "version"))
    parser.add_argument("--candidate", action="append", default=[], help="Executable name (repeatable, ordered)")
    parser.add_argument("--arg", action="append", default=[], help="Argument passed to the command (repeatable)")
    parser.add_argument("--version-flag", action="append", default=None, help="Version flag (repeatable, default --version)")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("--max-output", type=int, default=MAX_OUTPUT, help="Maximum captured stdout/stderr bytes")
    parser.add_argument("--expect-json", action="store_true")
    parser.add_argument("--strict", action="store_true", help="Exit 1 when the verdict is not usable")
    args = parser.parse_args()

    if not args.candidate:
        print("ERROR: at least one --candidate is required", file=sys.stderr)
        return 2
    if args.action == "resolve":
        output = {"tool": resolve(args.candidate)}
        ok = output["tool"] is not None
    elif args.action == "run":
        output = run([args.candidate[0], *args.arg], args.timeout, args.max_output)
        ok = valid_output(output, args.expect_json)
    elif args.action == "version":
        output = version_probe(args.candidate, args.version_flag, args.timeout, args.max_output)
        ok = output["ok"]
    else:
        output = chain(args.candidate, args.arg, args.timeout, args.expect_json, args.max_output)
        ok = output["ok"]
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 1 if args.strict and not ok else 0


if __name__ == "__main__":
    raise SystemExit(main())
