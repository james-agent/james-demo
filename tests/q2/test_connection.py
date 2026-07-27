"""Unit tests for Q2 Helix connection structure."""

from __future__ import annotations

import json

import httpx
import pytest
from fastapi.testclient import TestClient

from james.ext.q2.client import HelixClient
from james.ext.q2.config import Q2Config, reset_q2_config
from james.ext.q2.errors import Q2APIError, Q2ConfigError
from james.hub.app import app


@pytest.fixture(autouse=True)
def _clear_config_cache() -> None:
    reset_q2_config()
    yield
    reset_q2_config()


def test_missing_credentials_raise_config_error() -> None:
    cfg = Q2Config(
        Q2_HELIX_API_KEY="",
        Q2_HELIX_API_SECRET="",
        Q2_ENVIRONMENT="sandbox",
    )
    with pytest.raises(Q2ConfigError):
        cfg.require_helix()
    assert "Q2_HELIX_API_KEY" in cfg.missing_helix_vars()
    assert "Q2_HELIX_API_SECRET" in cfg.missing_helix_vars()


def test_helix_client_basic_auth_and_program_get() -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        assert request.url.path.endswith("/program/get")
        assert request.headers.get("authorization", "").startswith("Basic ")
        body = {
            "status": 0,
            "message": "Success",
            "data": {
                "programId": "prog-1",
                "products": [{"productId": "p1", "name": "Checking"}],
            },
        }
        return httpx.Response(200, json=body)

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    cfg = Q2Config(
        Q2_HELIX_API_URL="https://sandbox-api.helix.q2.com",
        Q2_HELIX_API_KEY="key",
        Q2_HELIX_API_SECRET="secret",
        Q2_HELIX_PROGRAM_ID="prog-1",
        Q2_ENVIRONMENT="sandbox",
    )
    with HelixClient(cfg, client=http_client) as client:
        result = client.get_program()
    assert result["program"]["programId"] == "prog-1"
    assert len(calls) == 1


def test_helix_client_maps_401() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"status": 1, "message": "Unauthorized"})

    cfg = Q2Config(
        Q2_HELIX_API_URL="https://sandbox-api.helix.q2.com",
        Q2_HELIX_API_KEY="bad",
        Q2_HELIX_API_SECRET="bad",
        Q2_ENVIRONMENT="sandbox",
    )
    with HelixClient(cfg, client=httpx.Client(transport=httpx.MockTransport(handler))) as client:
        with pytest.raises(Q2APIError) as exc:
            client.get_program()
    assert exc.value.http_status == 401


def test_connection_status_hides_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("Q2_HELIX_API_KEY", "super-secret-key")
    monkeypatch.setenv("Q2_HELIX_API_SECRET", "super-secret-secret")
    monkeypatch.setenv("Q2_ENVIRONMENT", "sandbox")
    reset_q2_config()
    client = TestClient(app)
    response = client.get("/api/v1/q2/connection/status")
    assert response.status_code == 200
    payload = response.json()
    raw = json.dumps(payload)
    assert "super-secret" not in raw
    assert payload["helix_api_key_set"] is True
    assert payload["helix_api_secret_set"] is True
    assert payload["helix_configured"] is True


def test_connection_test_config_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("Q2_HELIX_API_KEY", raising=False)
    monkeypatch.delenv("Q2_HELIX_API_SECRET", raising=False)
    monkeypatch.setenv("Q2_HELIX_API_KEY", "")
    monkeypatch.setenv("Q2_HELIX_API_SECRET", "")
    reset_q2_config()
    client = TestClient(app)
    response = client.post("/api/v1/q2/connection/test")
    assert response.status_code == 400
    assert response.json()["detail"]["result"] == "CONFIG_ERROR"
