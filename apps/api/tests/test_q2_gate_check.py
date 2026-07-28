"""Unit tests for Q2 gate check classification."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "q2_gate_check.py"


def _load_gate_module():
    spec = importlib.util.spec_from_file_location("q2_gate_check", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.asyncio
async def test_gate_check_config_error_when_missing_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("Q2_HELIX_API_KEY", raising=False)
    monkeypatch.delenv("Q2_HELIX_API_SECRET", raising=False)
    monkeypatch.delenv("Q2_API_KEY", raising=False)
    monkeypatch.delenv("Q2_API_SECRET", raising=False)
    monkeypatch.setenv("Q2_HELIX_API_URL", "https://sandbox-api.helix.q2.com")
    monkeypatch.setenv("Q2_HELIX_PROGRAM_ID", "1")

    module = _load_gate_module()
    result = await module.run_check()
    assert result["status"] == "CONFIG_ERROR"
    assert "Q2_HELIX_API_KEY" in result["message"]
