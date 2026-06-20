"""Tests for Q2 configuration loader."""

from __future__ import annotations

import pytest

from ext.q2.config import Q2Config, Q2ConfigError, get_q2_config


def test_q2_config_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("Q2_HELIX_API_KEY", raising=False)
    monkeypatch.delenv("Q2_HELIX_API_SECRET", raising=False)
    monkeypatch.delenv("Q2_HELIX_PROGRAM_ID", raising=False)
    get_q2_config.cache_clear()
    config = Q2Config()
    assert config.environment == "sandbox"
    assert "sandbox-api.helix.q2.com" in config.api_url


def test_q2_config_missing_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("Q2_HELIX_API_KEY", "")
    monkeypatch.setenv("Q2_HELIX_API_SECRET", "")
    monkeypatch.setenv("Q2_HELIX_PROGRAM_ID", "")
    config = Q2Config()
    missing = config.missing_fields()
    assert "Q2_HELIX_API_KEY" in missing
    assert "Q2_HELIX_API_SECRET" in missing
    assert "Q2_HELIX_PROGRAM_ID" in missing


def test_q2_config_require_configured_raises() -> None:
    config = Q2Config(
        Q2_HELIX_API_KEY="",
        Q2_HELIX_API_SECRET="",
        Q2_HELIX_PROGRAM_ID="",
    )
    with pytest.raises(Q2ConfigError):
        config.require_configured()
