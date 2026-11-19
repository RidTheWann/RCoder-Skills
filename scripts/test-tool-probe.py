#!/usr/bin/env python3
"""Self-tests for tool discovery, timeouts, invalid output, and bounded fallback."""
import importlib.util
import json
import os
import stat
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODULE = ROOT / "skills" / "rcoder" / "scripts" / "tool_probe.py"


def load_module():
    spec = importlib.util.spec_from_file_location("tool_probe", MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_script(path: Path, body: str):
    path.write_text("#!/bin/sh\n" + body + "\n", encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


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

    with tempfile.TemporaryDirectory(prefix="rcoder-tool-probe-") as temporary:
        directory = Path(temporary)
        make_script(directory / "fake-a", "echo not-json")
        make_script(directory / "fake-b", "printf '{\"ok\": true}'")
        original_path = os.environ.get("PATH", "")
        try:
            os.environ["PATH"] = str(directory) + os.pathsep + original_path
            result = mod.chain(["fake-a", "fake-b"], [], expect_json=True)
            assert result["ok"] is True, result
            assert Path(result["tool_used"]).name == "fake-b", result
            assert len(result["attempts"]) == 2, result
            none = mod.chain(["definitely-not-a-real-tool-xyz"], [], expect_json=True)
            assert none["ok"] is False and len(none["attempts"]) == 1
        finally:
            os.environ["PATH"] = original_path

    print("PASS tool_probe: discovery, missing executable, non-zero exit, timeout, "
          "invalid args, corrupted output, bounded fallback")


if __name__ == "__main__":
    main()
