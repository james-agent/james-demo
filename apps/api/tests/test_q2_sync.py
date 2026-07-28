"""Tests for local customer persistence and Q2 sync orchestration."""

from __future__ import annotations

from datetime import date
from typing import Any
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from crm_api.ext.q2.client import Q2HelixError
from crm_api.ext.q2.config import clear_q2_config_cache
from crm_api.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def _q2_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("Q2_HELIX_API_URL", "https://sandbox-api.helix.q2.com")
    monkeypatch.setenv("Q2_HELIX_API_KEY", "test-key")
    monkeypatch.setenv("Q2_HELIX_API_SECRET", "test-secret")
    monkeypatch.setenv("Q2_HELIX_PROGRAM_ID", "100")
    monkeypatch.setenv("Q2_ENVIRONMENT", "sandbox")
    monkeypatch.setenv("Q2_DEFAULT_PRODUCT_ID", "7")
    clear_q2_config_cache()
    yield
    clear_q2_config_cache()


def _complete_customer_payload(**overrides: Any) -> dict[str, Any]:
    data = {
        "email": f"user-{uuid4().hex[:8]}@example.com",
        "first_name": "Ada",
        "last_name": "Lovelace",
        "birth_date": "1815-12-10",
        "tax_id": "123456789",
        "tax_id_type": "SSN",
        "phone_number": "5551234567",
        "address_line1": "1 Analytical Engine Way",
        "city": "London",
        "state": "NY",
        "postal_code": "10001",
        "country_code": "USA",
    }
    data.update(overrides)
    return data


def test_create_local_customer_hides_tax_id() -> None:
    response = client.post("/api/v1/customers", json=_complete_customer_payload())
    assert response.status_code == 201
    body = response.json()
    assert body["q2_sync_status"] == "pending"
    assert body["has_tax_id"] is True
    assert "tax_id" not in body
    assert "123456789" not in str(body)


def test_sync_skips_incomplete_kyc_without_aborting_batch() -> None:
    incomplete = client.post(
        "/api/v1/customers",
        json={"email": f"inc-{uuid4().hex[:8]}@example.com", "first_name": "Inc", "last_name": "Omplete"},
    )
    assert incomplete.status_code == 201
    complete = client.post("/api/v1/customers", json=_complete_customer_payload())
    assert complete.status_code == 201
    complete_id = complete.json()["id"]

    with patch("crm_api.ext.q2.routes.sync.Q2HelixClient") as client_cls:
        instance = AsyncMock()
        instance.__aenter__.return_value = instance
        instance.__aexit__.return_value = None

        async def _post(path: str, payload: dict[str, Any] | None = None) -> Any:
            if path == "customer/getByTag":
                raise Q2HelixError("missing", status_code=404)
            if path == "customer/onboard":
                return {
                    "customerId": 42,
                    "tag": payload["tag"] if payload else complete_id,
                    "taxId": "123456789",
                }
            if path == "account/getByTag":
                raise Q2HelixError("missing", status_code=404)
            if path == "account/create":
                return {
                    "accountId": 99,
                    "customerId": 42,
                    "productId": 7,
                    "tag": payload["tag"] if payload else f"{complete_id}:primary",
                    "accountNumber": "1234567890",
                }
            raise AssertionError(f"unexpected path {path}")

        instance.post = AsyncMock(side_effect=_post)
        client_cls.return_value = instance

        response = client.post("/api/v1/q2/sync/customers")

    assert response.status_code == 200
    body = response.json()
    assert body["processed"] == 2
    outcomes = {row["local_customer_id"]: row for row in body["results"]}
    assert outcomes[incomplete.json()["id"]]["outcome"] == "skipped_incomplete"
    assert outcomes[incomplete.json()["id"]]["q2_sync_status"] == "skipped_incomplete"
    assert outcomes[complete_id]["q2_sync_status"] == "account_linked"
    assert outcomes[complete_id]["q2_account_id"] == 99


def test_sync_is_idempotent_via_get_by_tag() -> None:
    created = client.post("/api/v1/customers", json=_complete_customer_payload())
    assert created.status_code == 201
    local_id = created.json()["id"]

    with patch("crm_api.ext.q2.routes.sync.Q2HelixClient") as client_cls:
        instance = AsyncMock()
        instance.__aenter__.return_value = instance
        instance.__aexit__.return_value = None

        async def _post(path: str, payload: dict[str, Any] | None = None) -> Any:
            if path == "customer/getByTag":
                return {"customerId": 42, "tag": local_id}
            if path == "account/getByTag":
                return {
                    "accountId": 99,
                    "customerId": 42,
                    "productId": 7,
                    "tag": f"{local_id}:primary",
                    "accountNumber": "****7890",
                }
            raise AssertionError(f"unexpected create path {path}")

        instance.post = AsyncMock(side_effect=_post)
        client_cls.return_value = instance

        response = client.post(f"/api/v1/q2/sync/customers/{local_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["outcome"] == "linked_existing"
    assert body["q2_sync_status"] == "account_linked"
    assert body["q2_customer_id"] == 42
    assert body["q2_account_id"] == 99


def test_birth_date_round_trip() -> None:
    response = client.post(
        "/api/v1/customers",
        json=_complete_customer_payload(birth_date=date(1990, 1, 2).isoformat()),
    )
    assert response.status_code == 201
    assert response.json()["birth_date"] == "1990-01-02"
