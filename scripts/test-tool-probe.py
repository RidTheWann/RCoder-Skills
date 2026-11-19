#!/usr/bin/env python3
"""Self-tests for tool discovery, timeouts, bounded capture, version detection, and fallback."""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODULE = ROOT / "skills" / "rcoder" / "scripts" / "tool_probe.py"


def load_module():
    spec = importlib.util.spec_from_file_location("tool_probe", MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    mod = load_module()
    python = Path(sys.executable).name

    found = mod.resolve(["definitely-not-a-real-tool-xyz", python])
    assert found and Path(found).name == python, found
    assert mod.resolve(["definitely-not-a-real-tool-xyz"]) is None

    missing = mod.run(["definitely-not-a-real-tool-xyz", "--flag"])
    assert missing["invoked"] is False and missing["error"] == "executable not found"

    nonzero = mod.run([sys.executable, "-c", "import sys; sys.exit(3)"])
    assert nonzero["invoked"] is True and nonzero["exit_code"] == 3

    invalid_args = mod.run([sys.executable, "--not-a-valid-python-flag"])
    assert invalid_args["exit_code"] != 0

    timeout = mod.run([sys.executable, "-c", "import time; time.sleep(5)"], 0.3)
    assert timeout["timed_out"] is True and timeout["error"] == "timeout"

    bad = {"invoked": True, "timed_out": False, "exit_code": 0, "stdout": "{broken", "stderr": ""}
    good = {"invoked": True, "timed_out": False, "exit_code": 0, "stdout": '{"ok": true}', "stderr": ""}
    assert mod.valid_output(bad, True) is False
    assert mod.valid_output(good, True) is True
    assert mod.valid_output(bad, False) is True

    original_which = mod.shutil.which
    original_run = mod.run
    try:
        mod.shutil.which = lambda name: f"/probe/{name}" if name in {"fake-a", "fake-b", "fake-error"} else None

        def fake_run(command, timeout, max_output=65536):
            if Path(command[0]).name == "fake-error":
                return {"invoked": True, "exit_code": 7, "timed_out": False,
                        "error": "execution failed", "stdout": "", "stderr": ""}
            if Path(command[0]).name == "fake-a":
                return {"invoked": True, "exit_code": 0, "timed_out": False,
                        "error": None, "stdout": "not-json", "stderr": ""}
            return {"invoked": True, "exit_code": 0, "timed_out": False,
                    "error": None, "stdout": '{"ok": true}', "stderr": ""}

        mod.run = fake_run
        result = mod.chain(["fake-a", "fake-b"], [], expect_json=True)
        assert result["ok"] is True, result
        assert Path(result["tool_used"]).name == "fake-b", result
        assert len(result["attempts"]) == 2, result
        assert all(attempt["invoked"] for attempt in result["attempts"])

        none = mod.chain(["definitely-not-a-real-tool-xyz"], [], expect_json=True)
        assert none["ok"] is False and len(none["attempts"]) == 1

        failing = mod.chain(["fake-error", "fake-b"], [], expect_json=True)
        assert failing["ok"] is True and len(failing["attempts"]) == 2
    finally:
        mod.shutil.which = original_which
        mod.run = original_run

    bounded = mod.run(
        [sys.executable, "-c", "print('x' * 50000)"], 5, 128,
    )
    assert bounded["truncated_stdout"] is True and len(bounded["stdout"]) == 128, bounded

    partial = mod.run(
        [sys.executable, "-c", "import sys,time; print('partial'); sys.stdout.flush(); time.sleep(5)"], 0.3,
    )
    assert partial["timed_out"] is True and "partial" in partial["stdout"], partial
    if os.name == "posix":
        import signal
        try:
            os.killpg(partial["pid"], 0)
        except ProcessLookupError:
            pass
        else:
            os.killpg(partial["pid"], signal.SIGKILL)
            raise AssertionError("timed-out process group was not cleaned up")

    version_ok = mod.version_probe([sys.executable], ["--version"])
    assert version_ok["ok"] is True and "Python" in version_ok["version"], version_ok
    version_missing = mod.version_probe(["definitely-not-a-real-tool-xyz"])
    assert version_missing["ok"] is False and version_missing["version"] is None
    assert mod.version_of({"invoked": True, "timed_out": True, "exit_code": None,
                           "stdout": "", "stderr": ""}) is None

    def cli(*arguments):
        return subprocess.run(
            [sys.executable, str(MODULE), *arguments],
            text=True, capture_output=True, check=False, timeout=20,
        )

    assert cli().returncode == 2
    strict_missing = cli("run", "--candidate", "definitely-not-a-real-tool-xyz", "--strict")
    assert strict_missing.returncode == 1, strict_missing
    nonstrict_missing = cli("run", "--candidate", "definitely-not-a-real-tool-xyz")
    assert nonstrict_missing.returncode == 0
    strict_version = cli("version", "--candidate", sys.executable, "--version-flag=--version", "--strict")
    assert strict_version.returncode == 0, strict_version
    assert json.loads(strict_version.stdout)["ok"] is True

    print("PASS tool_probe: discovery, missing executable, non-zero exit, timeout, "
          "process-group cleanup, bounded capture, partial output, invalid args, "
          "corrupted output, version detection, CLI exit codes, and ordered fallback")


if __name__ == "__main__":
    main()
