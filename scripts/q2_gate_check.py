#!/usr/bin/env python3
"""Repo-root wrapper for apps/api/scripts/q2_gate_check.py."""

from __future__ import annotations

import runpy
from pathlib import Path

TARGET = Path(__file__).resolve().parents[1] / "apps" / "api" / "scripts" / "q2_gate_check.py"
runpy.run_path(str(TARGET), run_name="__main__")
