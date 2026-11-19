#!/usr/bin/env python3
"""Repository-root wrapper for the canonical RSaver CLI bundled with the skill."""
import runpy
from pathlib import Path

CANONICAL = Path(__file__).resolve().parent.parent / "skills" / "rcoder" / "scripts" / "rsaver.py"


def main() -> None:
    runpy.run_path(str(CANONICAL), run_name="__main__")


if __name__ == "__main__":
    main()
