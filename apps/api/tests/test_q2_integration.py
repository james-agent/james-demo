"""Tests for Q2 Helix customer and account integration routes."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from crm_api.ext.q2.client import Q2HelixError
from crm_api.ext.q2.config import Q2Config
from crm_api.main import app

client = TestClient(app)

CONFIGURED = Q2Config(
    api_url="https://sandbox-api.helix.q2.com",
    api_key="test-key",
    api_secret="test-secret",
    program_id="100",
    environment="sandbox",
)


def _customer_payload(**overrides: Any) -> dict[str, Any]:
    data = {
        "customerId": 42,
        "tag": "crm-user-1",
        "status": "Active",
        "kycStatus": "Verified",
        "isBusiness": False,
        "isLocked": False,
        "taxId": "123456789",
        "firstName": "Ada",
        "lastName": "Lovelace",
        "emailAddress": "ada@example.com",
    }
    data.update(overrides)
    return data


def _account_payload(**overrides: Any) -> dict[str, Any]:
    data = {
        "accountId": 99,
        "customerId": 42,
        "productId": 7,
        "accountBalance": 100.0,
        "availableBalance": 90.0,
        "pendingBalance": 10.0,
        "status": "Open",
        "type": "Checking",
        "tag": "acc-1",
        "routingNumber": "021000021",
        "accountNumber": "1234567890",
        "isLocked": False,
        "name": "Primary Checking",
    }
    data.update(overrides)
    return data


@pytest.fixture(autouse=True)
def _q2_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("Q2_HELIX_API_URL", CONFIGURED.api_url)
    monkeypatch.setenv("Q2_HELIX_API_KEY", CONFIGURED.api_key)
    monkeypatch.setenv("Q2_HELIX_API_SECRET", CONFIGURED.api_secret)
    monkeypatch.setenv("Q2_HELIX_PROGRAM_ID", CONFIGURED.program_id)
    monkeypatch.setenv("Q2_ENVIRONMENT", "sandbox")


def test_onboard_customer_masks_tax_id() -> None:
    with patch("crm_api.ext.q2.routes.customers.Q2HelixClient") as client_cls:
        instance = AsyncMock()
        instance.__aenter__.return_value = instance
        instance.__aexit__.return_value = None
        instance.post = AsyncMock(return_value=_customer_payload())
        client_cls.return_value = instance

        response = client.post(
            "/api/v1/q2/customers/onboard",
            json={
                "firstName": "Ada",
                "lastName": "Lovelace",
                "birthDate": "1815-12-10T00:00:00.000+00:00",
                "taxId": "123456789",
                "emailAddress": "ada@example.com",
                "tag": "crm-user-1",
                "addresses": [
                    {
                        "addressLine1": "1 Analytical Engine Way",
                        "city": "London",
                        "state": "NY",
                        "postalCode": "10001",
                        "countryCode": "USA",
                    }
                ],
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["customerId"] == 42
    assert body["taxIdMasked"] == "***-**-6789"
    assert "123456789" not in str(body)


def test_get_customer_not_found() -> None:
    with patch("crm_api.ext.q2.routes.customers.Q2HelixClient") as client_cls:
        instance = AsyncMock()
        instance.__aenter__.return_value = instance
        instance.__aexit__.return_value = None
        instance.post = AsyncMock(side_effect=Q2HelixError("missing", status_code=404))
        client_cls.return_value = instance

        response = client.get("/api/v1/q2/customers/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Q2 resource not found"


def test_create_account_masks_account_number() -> None:
    with patch("crm_api.ext.q2.routes.accounts.Q2HelixClient") as client_cls:
        instance = AsyncMock()
        instance.__aenter__.return_value = instance
        instance.__aexit__.return_value = None
        instance.post = AsyncMock(return_value=_account_payload())
        client_cls.return_value = instance

        response = client.post(
            "/api/v1/q2/accounts/create",
            json={
                "customerId": 42,
                "productId": 7,
                "name": "Primary Checking",
                "tag": "acc-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["accountId"] == 99
    assert body["accountNumber"] == "****7890"
    assert "1234567890" not in str(body)


def test_list_accounts_for_customer() -> None:
    with patch("crm_api.ext.q2.routes.accounts.Q2HelixClient") as client_cls:
        instance = AsyncMock()
        instance.__aenter__.return_value = instance
        instance.__aexit__.return_value = None
        instance.post = AsyncMock(return_value={"accounts": [_account_payload()]})
        client_cls.return_value = instance

        response = client.get("/api/v1/q2/accounts/customer/42")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["tag"] == "acc-1"


def test_duplicate_tag_returns_409() -> None:
    with patch("crm_api.ext.q2.routes.customers.Q2HelixClient") as client_cls:
        instance = AsyncMock()
        instance.__aenter__.return_value = instance
        instance.__aexit__.return_value = None
        instance.post = AsyncMock(side_effect=Q2HelixError("dup", status_code=409))
        client_cls.return_value = instance

        response = client.post(
            "/api/v1/q2/customers/onboard",
            json={
                "firstName": "Ada",
                "lastName": "Lovelace",
                "birthDate": "1815-12-10T00:00:00.000+00:00",
                "taxId": "123456789",
                "emailAddress": "ada@example.com",
                "tag": "crm-user-1",
            },
        )

    assert response.status_code == 409
    assert response.json()["detail"] == "Duplicate tag conflict"
