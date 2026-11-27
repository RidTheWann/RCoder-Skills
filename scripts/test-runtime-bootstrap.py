#!/usr/bin/env python3
"""Offline tests for automatic Runtime activation from the local RCoder MCP process."""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "rcoder" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import runtime_bootstrap  # noqa: E402


def main():
    with tempfile.TemporaryDirectory() as temp:
        project = Path(temp).resolve()

        disabled = Mock()
        previous = os.environ.get("RCODER_RUNTIME_DISABLE")
        os.environ["RCODER_RUNTIME_DISABLE"] = "1"
        try:
            assert not runtime_bootstrap.start_runtime_companion(
                project, runtime_binary="/tmp/rcoder-runtime", popen=disabled
            )
            disabled.assert_not_called()
        finally:
            if previous is None:
                os.environ.pop("RCODER_RUNTIME_DISABLE", None)
            else:
                os.environ["RCODER_RUNTIME_DISABLE"] = previous

        missing = Mock()
        with patch.dict(os.environ, {"RCODER_RUNTIME_PATH": ""}), \
             patch.object(runtime_bootstrap.shutil, "which", return_value=None):
            assert not runtime_bootstrap.start_runtime_companion(
                project, runtime_binary="", popen=missing
            )
        missing.assert_not_called()

        unix_launch = Mock()
        assert runtime_bootstrap.start_runtime_companion(
            project, runtime_binary="/opt/rcoder-runtime", parent_pid=1234,
            platform="linux", popen=unix_launch
        )
        command = unix_launch.call_args.args[0]
        options = unix_launch.call_args.kwargs
        assert command == [
            "/opt/rcoder-runtime", "attach", "--project", str(project),
            "--parent-pid", "1234"
        ]
        assert options["stdin"] == runtime_bootstrap.subprocess.DEVNULL
        assert options["stdout"] == runtime_bootstrap.subprocess.DEVNULL
        assert options["stderr"] == runtime_bootstrap.subprocess.DEVNULL
        assert options["start_new_session"] is True
        assert options["close_fds"] is True

        windows_launch = Mock()
        assert runtime_bootstrap.start_runtime_companion(
            project, runtime_binary="C:/tools/rcoder-runtime.exe", parent_pid=77,
            platform="win32", popen=windows_launch
        )
        windows_options = windows_launch.call_args.kwargs
        assert windows_options["creationflags"] == 0x00000008 | 0x08000000
        assert "start_new_session" not in windows_options

        broken_launch = Mock(side_effect=OSError("cannot start"))
        assert not runtime_bootstrap.start_runtime_companion(
            project, runtime_binary="/bad/rcoder-runtime", popen=broken_launch
        )

    print("RCoder Runtime bootstrap tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
