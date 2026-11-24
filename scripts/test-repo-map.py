#!/usr/bin/env python3
"""Deterministic checks for repo_map.py: discovery, extraction, graph, ranking, budget."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "skills" / "rcoder" / "scripts" / "repo_map.py"


def run_map(cwd: Path, args: list[str]) -> dict:
    done = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, encoding="utf-8",
        cwd=str(cwd), timeout=30,
    )
    assert done.returncode == 0, f"repo_map failed rc={done.returncode}:\n{done.stderr}"
    return json.loads(done.stdout) if "--json" in args else {"raw": done.stdout}


def build_fixture() -> Path:
    base = Path(tempfile.mkdtemp(prefix="repomap-test-"))
    # Python service with an entry point
    (base / "main.py").write_text(
        "from service.loader import load\n"
        "from service.kernel import run\n"
        "\n"
        "def main():\n"
        "    load()\n"
        "    run()\n"
    )
    (base / "service").mkdir()
    (base / "service/__init__.py").write_text("")
    (base / "service/loader.py").write_text(
        "import json\n"
        "import os\n"
        "\n"
        "def load() -> dict:\n"
        "    \"\"\"Load the service config.\"\"\"\n"
        "    return {}\n"
    )
    (base / "service/kernel.py").write_text(
        "from service.loader import load\n"
        "\n"
        "class Kernel:\n"
        "    def run(self) -> None:\n"
        "        pass\n"
    )
    # TypeScript web entry
    (base / "src").mkdir()
    (base / "src/index.ts").write_text(
        "import { App } from './app'\n"
        "const app = new App()\n"
    )
    (base / "src/app.ts").write_text(
        "import { db } from './db'\n"
        "export class App {\n"
        "    constructor() { this.db = db }\n"
        "    render() {}\n"
        "}\n"
    )
    (base / "src/db.ts").write_text(
        "import { SELECT } from './sql'\n"
        "export const db: Database = { query(q: string) { SELECT(q) } }\n"
    )
    (base / "src/sql.ts").write_text(
        "export function SELECT(q: string): string {\n"
        "    return q\n"
        "}\n"
    )
    # Rust embedded entry
    (base / "src-rs").mkdir()
    (base / "src-rs" / "main.rs").write_text(
        "use firmware::hal::watchdog;\n"
        "\n"
        "fn main() {\n"
        "    watchdog::kick();\n"
        "}\n"
    )
    (base / "src-rs" / "firmware").mkdir()
    (base / "src-rs" / "firmware" / "mod.rs").write_text("")
    (base / "src-rs" / "firmware" / "hal.rs").write_text(
        "pub mod watchdog;\n"
        "pub fn init() -> bool {\n"
        "    true\n"
        "}\n"
    )
    (base / "src-rs" / "firmware" / "watchdog.rs").write_text(
        "pub fn kick() -> None {}\n"
    )
    # Vendor directory must be ignored
    (base / "vendor").mkdir()
    (base / "vendor" / "decoy.py").write_text("def trap(): return 42")
    return base


def main() -> int:
    base = build_fixture()
    try:
        r = run_map(base, ["--json", "--budget", "4096", "--max-files", "100"])
        data = r["map"]
        assert "main.py" in data, f"main.py missing:\n{data}"
        assert "service/kernel.py" in data, f"kernel.py missing:\n{data}"
        assert "src/index.ts" in data, f"index.ts missing:\n{data}"
        assert "vendor" not in data, f"vendor should be ignored:\n{data}"
        assert "src-rs/main.rs" in data, f"main.rs missing:\n{data}"
        # Entry point should rank high: it appears before decoys
        assert data.index("main.py") < data.index("src-rs/main.rs"), "main.py should rank high"

        # Verify symbol extraction
        assert "def main()" in data, "function signature missing"
        assert "class Kernel" in data, "class missing"
        assert "fn main()" in data, "rust fn missing"
        assert "load()" in data, "import edge missing"

        # Budget bounding: much smaller budget must truncate
        small = run_map(base, ["--json", "--budget", "128", "--max-files", "100"])
        assert len(small["map"]) < len(data), "smaller budget must produce shorter output"
        # Still deterministic
        again = run_map(base, ["--json", "--budget", "4096", "--max-files", "100"])
        assert again["map"] == data, "output must be deterministic"

        # Compact mode names-only
        compact = run_map(base, ["--json", "--budget", "4096", "--max-files", "100", "--format", "compact"])
        assert "def main()" not in compact["map"], "compact should not include signatures"

        # JSON structure
        assert "used_tokens" in r, "used_tokens missing in json"
        assert r["files_processed"] >= 5, f"expected >=5 files, got {r['files_processed']}"
        print("PASS repo_map deterministic checks")
        return 0
    finally:
        import shutil
        shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
