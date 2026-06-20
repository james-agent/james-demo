#!/usr/bin/env python3
"""Repo-root wrapper for Q2 Helix gate check."""

from __future__ import annotations

import runpy
from pathlib import Path

TARGET = Path(__file__).resolve().parent.parent / "apps" / "api" / "scripts" / "q2_gate_check.py"

if __name__ == "__main__":
    runpy.run_path(str(TARGET), run_name="__main__")
