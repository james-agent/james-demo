"""Unit tests for Q2 customer and account services/routes."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ext.q2.client import HelixClient  # noqa: E402
from ext.q2.config import Q2Config  # noqa: E402
from ext.q2.models.account import AccountCreateRequest  # noqa: E402
from ext.q2.models.customer import CustomerOnboardRequest  # noqa: E402
from ext.q2.services.account import AccountService  # noqa: E402
from ext.q2.services.customer import CustomerService  # noqa: E402
from ext.q2.services._helpers import mask_pii  # noqa: E402


def _cfg() -> Q2Config:
    return Q2Config(
        api_url="https://sandbox-api.helix.q2.com",
        api_key="k",
        api_secret="s",
        program_id="p",
        environment="sandbox",
    )


def _client_with_handler(handler) -> HelixClient:
    cfg = _cfg()
    client = HelixClient(cfg)
    client._client.close()
    client._client = httpx.Client(
        base_url=cfg.api_url,
        auth=(cfg.api_key, cfg.api_secret),
        transport=httpx.MockTransport(handler),
    )
    return client


def test_mask_pii_hides_tax_and_account_numbers() -> None:
    masked = mask_pii({"taxId": "123456789", "accountNumber": "9988776655", "name": "Ada"})
    assert masked["taxId"] == "****6789"
    assert masked["accountNumber"] == "****6655"
    assert masked["name"] == "Ada"


def test_customer_onboard_posts_relative_path() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["body"] = request.read()
        return httpx.Response(
            200,
            json={
                "status": 0,
                "data": {
                    "customerId": 42,
                    "tag": "u-1",
                    "status": "Active",
                    "kycStatus": "Verified",
                    "taxId": "123456789",
                },
            },
        )

    helix = _client_with_handler(handler)
    svc = CustomerService(helix)
    result = svc.onboard(
        CustomerOnboardRequest(firstName="Ada", lastName="Lovelace", tag="u-1", taxId="123456789")
    )
    assert seen["path"] == "/customer/onboard"
    assert result["customerId"] == 42
    assert result["taxId"] == "****6789"
    assert result["kycStatus"] == "Verified"
    svc.close()


def test_customer_duplicate_tag_maps_to_409() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(409, json={"message": "Duplicate tag"})

    helix = _client_with_handler(handler)
    from crm_api.main import app
    from ext.q2.routes import customers as q2_customers

    def override():
        svc = CustomerService(helix)
        try:
            yield svc
        finally:
            svc.close()

    app.dependency_overrides[q2_customers.get_customer_service] = override
    client = TestClient(app)
    response = client.post(
        "/api/v1/q2/customers/onboard",
        json={"firstName": "Ada", "lastName": "Lovelace", "tag": "dup"},
    )
    app.dependency_overrides.clear()
    assert response.status_code == 409
    assert "tag" in response.json()["detail"].lower()


def test_account_create_and_list() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path.endswith("/account/create"):
            return httpx.Response(
                200,
                json={
                    "data": {
                        "accountId": 99,
                        "customerId": 1,
                        "productId": 10,
                        "accountBalance": 0,
                        "availableBalance": 0,
                        "pendingBalance": 0,
                        "status": "Open",
                        "type": "Checking",
                        "tag": "acc-1",
                        "accountNumber": "1234567890",
                        "isLocked": False,
                        "name": "Primary",
                    }
                },
            )
        return httpx.Response(
            200,
            json={"data": {"accounts": [{"accountId": 99, "accountNumber": "1234567890"}]}},
        )

    helix = _client_with_handler(handler)
    svc = AccountService(helix)
    created = svc.create(
        AccountCreateRequest(customerId=1, productId=10, name="Primary", tag="acc-1")
    )
    listed = svc.list_by_customer(1)
    assert calls == ["/account/create", "/account/list"]
    assert created["accountId"] == 99
    assert created["accountNumber"] == "****7890"
    assert listed["accounts"][0]["accountNumber"] == "****7890"
    svc.close_client()


def test_account_stop_pay_routes() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/stopPay/create"):
            return httpx.Response(200, json={"data": {"stopPayId": 7}})
        if path.endswith("/stopPay/list"):
            return httpx.Response(200, json={"data": {"stopPays": [{"stopPayId": 7}]}})
        if path.endswith("/stopPay/cancel"):
            return httpx.Response(200, json={"data": {"cancelled": True}})
        return httpx.Response(404, json={"message": "missing"})

    helix = _client_with_handler(handler)
    from crm_api.main import app
    from ext.q2.routes import accounts as q2_accounts

    def override():
        svc = AccountService(helix)
        try:
            yield svc
        finally:
            svc.close_client()

    app.dependency_overrides[q2_accounts.get_account_service] = override
    client = TestClient(app)
    create = client.post("/api/v1/q2/accounts/1/stop-pay", json={"checkNumber": "1001", "amount": 10})
    listed = client.get("/api/v1/q2/accounts/1/stop-pay")
    cancel = client.delete("/api/v1/q2/accounts/1/stop-pay/7")
    app.dependency_overrides.clear()
    assert create.status_code == 200
    assert create.json()["stopPayId"] == 7
    assert listed.status_code == 200
    assert cancel.status_code == 200
    assert cancel.json()["cancelled"] is True
