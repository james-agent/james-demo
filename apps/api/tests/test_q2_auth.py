"""Unit tests for Q2 Helix config and client error classification."""

from __future__ import annotations

import sys
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ext.q2.client import HelixAPIError, HelixClient  # noqa: E402
from ext.q2.config import Q2Config, get_q2_config  # noqa: E402


@pytest.fixture(autouse=True)
def _clear_config_cache():
    get_q2_config.cache_clear()
    yield
    get_q2_config.cache_clear()


def test_get_q2_config_reports_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "Q2_HELIX_API_URL",
        "Q2_HELIX_API_KEY",
        "Q2_HELIX_API_SECRET",
        "Q2_HELIX_PROGRAM_ID",
        "Q2_ENVIRONMENT",
        "Q2_API_KEY",
        "Q2_API_SECRET",
        "Q2_BASE_URL",
        "Q2_PROGRAM_ID",
    ):
        monkeypatch.delenv(key, raising=False)

    cfg = get_q2_config(env_file="/nonexistent/.env")
    assert cfg.api_url == "https://sandbox-api.helix.q2.com"
    assert cfg.environment == "sandbox"
    assert not cfg.is_complete
    missing = cfg.missing_fields()
    assert "Q2_HELIX_API_KEY" in missing
    assert "Q2_HELIX_API_SECRET" in missing
    assert "Q2_HELIX_PROGRAM_ID" in missing
    assert cfg.status_map()["Q2_HELIX_API_KEY"] == "MISSING"


def test_combined_api_key_splits_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("Q2_HELIX_API_KEY", "mykey:mysecret")
    monkeypatch.setenv("Q2_HELIX_PROGRAM_ID", "prog-1")
    monkeypatch.delenv("Q2_HELIX_API_SECRET", raising=False)
    monkeypatch.setenv("Q2_ENVIRONMENT", "sandbox")

    cfg = get_q2_config(env_file="/nonexistent/.env")
    assert cfg.api_key == "mykey"
    assert cfg.api_secret == "mysecret"
    assert cfg.is_complete


def test_helix_client_401_is_config_error(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = Q2Config(
        api_url="https://sandbox-api.helix.q2.com",
        api_key="k",
        api_secret="s",
        program_id="p",
        environment="sandbox",
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "unauthorized"})

    transport = httpx.MockTransport(handler)
    client = HelixClient(cfg)
    client._client.close()
    client._client = httpx.Client(
        base_url=cfg.api_url,
        auth=(cfg.api_key, cfg.api_secret),
        transport=transport,
    )

    with pytest.raises(HelixAPIError) as exc_info:
        client.test_connectivity()
    assert exc_info.value.status_code == 401
    assert exc_info.value.classification == "CONFIG_ERROR"
    client.close()


def test_discover_products_from_payload() -> None:
    cfg = Q2Config(
        api_url="https://sandbox-api.helix.q2.com",
        api_key="k",
        api_secret="s",
        program_id="p",
        environment="sandbox",
    )
    client = HelixClient(cfg)
    products = client.discover_products(
        {"data": {"products": [{"productId": "checking"}, {"productId": "savings"}]}}
    )
    assert [p["productId"] for p in products] == ["checking", "savings"]
    client.close()
