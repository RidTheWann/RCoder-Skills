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
import rcoder_mcp  # noqa: E402
import rcoder_mcp_http  # noqa: E402


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

        # The legacy server's actual startup path must invoke the companion before serving.
        with patch.object(rcoder_mcp.runtime_bootstrap, "start_runtime_companion") as start, \
             patch.object(rcoder_mcp, "serve", return_value=0):
            assert rcoder_mcp.main(["--root", str(project)]) == 0
            start.assert_called_once_with(project)

        # Printing configuration is an installer-preview operation, not an MCP session.
        with patch.object(rcoder_mcp.runtime_bootstrap, "start_runtime_companion") as start:
            assert rcoder_mcp.main(["--print-config", "generic"]) == 0
            start.assert_not_called()

        # The long-lived loopback HTTP process owns one session; per-request workers are disabled.
        fake_server = Mock()
        fake_server.server_port = 8765
        with patch.dict(os.environ, {"RCODER_MCP_TOKEN": "x" * 40}), \
             patch.object(rcoder_mcp_http, "Server", return_value=fake_server), \
             patch.object(rcoder_mcp_http.runtime_bootstrap, "start_runtime_companion") as start:
            assert rcoder_mcp_http.main(["--root", str(project), "--port", "0"]) == 0
            start.assert_called_once_with(project)
            fake_server.serve_forever.assert_called_once()
            fake_server.server_close.assert_called_once()

        broken_launch = Mock(side_effect=OSError("cannot start"))
        assert not runtime_bootstrap.start_runtime_companion(
            project, runtime_binary="/bad/rcoder-runtime", popen=broken_launch
        )

    print("RCoder Runtime bootstrap tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
