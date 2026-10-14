#!/usr/bin/env python3
"""Compatibility shim — run `python3 qa_check.py` from the site root (_src/halfbandnew2026/)."""
import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).resolve().parents[1] / "qa_check.py"), run_name="__main__")
