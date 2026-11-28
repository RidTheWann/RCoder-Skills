#!/usr/bin/env python3
"""Offline regressions for the bundled RFC/Runtime installer helper."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HELPER = ROOT / "skills" / "rcoder" / "scripts" / "rcoder_builtins.py"
ASSET = ROOT / "runtime" / "bin" / "rcoder-runtime-linux-arm64"


def host_key() -> str | None:
    import importlib.util
    spec = importlib.util.spec_from_file_location("rcoder_builtins_key", HELPER)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.platform_key()


def bundled_for_host() -> Path | None:
    import platform
    system = platform.system().lower()
    machine = platform.machine().lower()
    key = None
    if system == "linux" and machine in {"aarch64", "arm64"}:
        key = "linux-arm64"
    elif system == "linux" and machine in {"x86_64", "amd64"}:
        key = "linux-x64"
    elif system == "darwin" and machine == "arm64":
        key = "macos-arm64"
    elif system == "darwin" and machine in {"x86_64", "amd64"}:
        key = "macos-x64"
    elif system == "windows" and machine in {"amd64", "x86_64"}:
        key = "windows-x64"
    if not key:
        return None
    name = f"rcoder-runtime-{key}.exe" if system == "windows" else f"rcoder-runtime-{key}"
    candidate = ROOT / "runtime" / "bin" / name
    return candidate if candidate.is_file() else None


def run(*args: str, home: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home))
    return subprocess.run(
        [sys.executable, str(HELPER), *args], env=env,
        capture_output=True, text=True, timeout=120, check=False,
    )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="rcoder-builtins-") as raw:
        temp = Path(raw)
        home = temp / "home"
        project = temp / "project"
        home.mkdir()
        project.mkdir()

        # Dry run prints the plan and writes nothing.
        preview = run("setup", "--root", str(project), "--source", str(ROOT),
                      "--home", str(home), "--dry-run", home=home)
        assert preview.returncode == 0, preview.stderr
        assert "[RFC] would initialize" in preview.stdout, preview.stdout
        assert not (project / ".rcoder" / "context-fabric.sqlite3").exists()
        assert not (home / ".rcoder" / "bin").exists()

        # RFC store is initialized without any host toolchain.
        rfc_only = run("setup", "--root", str(project), "--source", str(ROOT),
                       "--home", str(home), "--no-runtime", home=home)
        assert rfc_only.returncode == 0, rfc_only.stderr
        assert (project / ".rcoder" / "context-fabric.sqlite3").is_file()
        assert "[Runtime]" not in rfc_only.stdout, rfc_only.stdout

        # The Runtime binary is installed from the project, with no cargo on PATH.
        release_args: list[str] = []
        host_asset = bundled_for_host()
        if host_asset is None:
            # CI runners have no prebuilt asset committed for their platform; verify
            # the release-asset download path with a local file:// catalog instead.
            import importlib.util
            import platform
            spec = importlib.util.spec_from_file_location("rcoder_builtins", HELPER)
            module = importlib.util.module_from_spec(spec)
            assert spec and spec.loader
            spec.loader.exec_module(module)
            key = module.platform_key()
            assert key, f"unsupported test platform: {platform.platform()}"
            release_dir = temp / "release"
            (release_dir / "runtime").mkdir(parents=True)
            name = f"rcoder-runtime-{key}.exe" if platform.system().lower() == "windows" else f"rcoder-runtime-{key}"
            shutil.copyfile(ASSET, release_dir / name)
            (release_dir / "SHA256SUMS").write_text(
                f"{__import__('hashlib').sha256(ASSET.read_bytes()).hexdigest()}  {name}\n", encoding="utf-8")
            release_args = ["--release-base", str(release_dir)]
        full = run("setup", "--root", str(project), "--source", str(ROOT),
                   "--home", str(home), *release_args, home=home)
        assert full.returncode == 0, full.stderr
        binary = home / ".rcoder" / "bin" / ("rcoder-runtime.exe" if os.name == "nt" else "rcoder-runtime")
        assert binary.is_file(), full.stdout + full.stderr
        assert os.access(binary, os.X_OK)
        if host_asset is not None:
            version = subprocess.run([str(binary), "--version"], capture_output=True,
                                     text=True, timeout=30, check=False)
            assert version.returncode == 0, version.stderr
            assert "rcoder-runtime" in version.stdout, version.stdout

        # A tampered checksum is refused before any binary is copied.
        bad_source = temp / "bad-source"
        (bad_source / "runtime" / "bin").mkdir(parents=True)
        bad_key = host_key() or "linux-arm64"
        bad_name = f"rcoder-runtime-{bad_key}.exe" if os.name == "nt" else f"rcoder-runtime-{bad_key}"
        shutil.copyfile(ASSET, bad_source / "runtime" / "bin" / bad_name)
        (bad_source / "runtime" / "bin" / "SHA256SUMS").write_text(
            "0000000000000000000000000000000000000000000000000000000000000000  " + bad_name + "\n",
            encoding="utf-8",
        )
        bad_home = temp / "bad-home"
        bad_home.mkdir()
        bad_base = bad_source / "runtime" / "bin"
        bad = run("setup", "--root", str(project), "--source", str(bad_source),
                  "--home", str(bad_home), "--no-rfc", "--release-base", str(bad_base), home=bad_home)
        assert bad.returncode == 0, bad.stderr
        assert "checksum mismatch" in bad.stderr, bad.stderr
        assert not (bad_home / ".rcoder" / "bin" / "rcoder-runtime").exists()

    print("PASS rcoder_builtins: RFC init, bundled Runtime install, dry run, and digest refusal")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
