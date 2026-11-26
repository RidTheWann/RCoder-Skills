#!/usr/bin/env python3
"""CLI wrapper for the importable cross-platform parity verifier."""
import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).with_name("verify_parity.py")), run_name="__main__")
