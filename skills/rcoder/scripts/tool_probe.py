#!/usr/bin/env python3
"""Dependency-free tool discovery, verification, and bounded fallback execution.

A skill file is not an installed executable. This helper verifies that a tool
exists before use, executes it with a hard timeout, checks output validity, and
falls back only to explicitly listed alternatives. It never retries the same
command with the same arguments: a retry requires a changed condition supplied
by the caller, so infinite retry loops cannot occur.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys

DEFAULT_TIMEOUT = 20.0


def resolve(candidates: list[str]) -> str | None:
    """Return the first candidate executable resolvable on PATH."""
    for candidate in candidates:
        if not candidate:
            continue
        found = shutil.which(candidate)
        if found:
            return found
    return None


def run(command: list[str], timeout: float = DEFAULT_TIMEOUT) -> dict:
    """Execute one command once. No implicit retry. Returns a structured verdict."""
    verdict = {
        "invoked": False, "command": list(command), "exit_code": None,
        "stdout": "", "stderr": "", "timed_out": False, "error": None,
    }
    if not command or not shutil.which(command[0]):
        verdict["error"] = "executable not found"
        return verdict
    try:
        proc = subprocess.run(
            command, capture_output=True, text=True,
            timeout=timeout, check=False,
        )
    except subprocess.TimeoutExpired as error:
        verdict.update({
            "invoked": True, "timed_out": True,
            "stdout": (error.stdout or "") if isinstance(error.stdout, str) else "",
            "stderr": (error.stderr or "") if isinstance(error.stderr, str) else "",
            "error": "timeout",
        })
        return verdict
    except (OSError, ValueError) as error:
        verdict["error"] = f"execution failed: {error}"
        return verdict
    verdict.update({
        "invoked": True, "exit_code": proc.returncode,
        "stdout": proc.stdout, "stderr": proc.stderr,
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


def chain(candidates: list[str], args: list[str], timeout: float = DEFAULT_TIMEOUT,
          expect_json: bool = False) -> dict:
    """Try each candidate at most once; return the first usable result."""
    attempts = []
    for candidate in candidates:
        command = [candidate, *args]
        found = shutil.which(candidate)
        if not found:
            attempts.append({"candidate": candidate, "reason": "not installed", "invoked": False})
            continue
        verdict = run(command, timeout)
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
    parser.add_argument("action", choices=("resolve", "run", "chain"))
    parser.add_argument("--candidate", action="append", default=[], help="Executable name (repeatable, ordered)")
    parser.add_argument("--arg", action="append", default=[], help="Argument passed to the command (repeatable)")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("--expect-json", action="store_true")
    args = parser.parse_args()

    if not args.candidate:
        print("ERROR: at least one --candidate is required", file=sys.stderr)
        return 2
    if args.action == "resolve":
        output = {"tool": resolve(args.candidate)}
    elif args.action == "run":
        output = run([args.candidate[0], *args.arg], args.timeout)
    else:
        output = chain(args.candidate, args.arg, args.timeout, args.expect_json)
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0 if (args.action != "chain" or output["ok"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
