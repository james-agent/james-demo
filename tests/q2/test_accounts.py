"""Unit tests for Q2 Helix account management."""

from __future__ import annotations

import httpx
import pytest
from fastapi.testclient import TestClient

from james.ext.q2.client import HelixClient
from james.ext.q2.config import Q2Config, reset_q2_config
from james.ext.q2.services.account import AccountService
from james.hub.app import app


@pytest.fixture(autouse=True)
def _clear_config_cache() -> None:
    reset_q2_config()
    yield
    reset_q2_config()


def _cfg() -> Q2Config:
    return Q2Config(
        Q2_HELIX_API_URL="https://sandbox-api.helix.q2.com",
        Q2_HELIX_API_KEY="key",
        Q2_HELIX_API_SECRET="secret",
        Q2_HELIX_PROGRAM_ID="prog-1",
        Q2_ENVIRONMENT="sandbox",
    )


def test_account_create_list_lock_stop_pay() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path.endswith("/account/create"):
            return httpx.Response(
                200,
                json={
                    "status": 0,
                    "data": {
                        "accountId": 100,
                        "customerId": 42,
                        "name": "Checking",
                        "status": "Open",
                        "availableBalance": 0,
                        "accountNumber": "1234567890",
                        "productId": 9,
                        "isLocked": False,
                    },
                },
            )
        if "/account/list/" in request.url.path:
            return httpx.Response(
                200,
                json={
                    "status": 0,
                    "data": [
                        {
                            "accountId": 100,
                            "customerId": 42,
                            "name": "Checking",
                            "status": "Open",
                            "availableBalance": 12.5,
                            "accountNumber": "1234567890",
                        }
                    ],
                },
            )
        if request.url.path.endswith("/account/lock"):
            return httpx.Response(
                200,
                json={
                    "status": 0,
                    "data": {
                        "accountId": 100,
                        "customerId": 42,
                        "isLocked": True,
                        "lockTypeCode": "CST",
                        "status": "Open",
                    },
                },
            )
        if "createCheckStopPay" in request.url.path:
            return httpx.Response(
                200,
                json={"status": 0, "data": {"stopPayId": 55, "paymentType": "Check"}},
            )
        if "/account/stopPay/list/" in request.url.path:
            return httpx.Response(
                200,
                json={"status": 0, "data": [{"stopPayId": 55, "paymentType": "Check"}]},
            )
        if request.url.path.endswith("/account/stopPay/expire"):
            return httpx.Response(
                200,
                json={"status": 0, "data": {"stopPayId": 55, "status": "Expired"}},
            )
        return httpx.Response(404, json={"status": 1, "message": "not found"})

    with HelixClient(_cfg(), client=httpx.Client(transport=httpx.MockTransport(handler))) as helix:
        service = AccountService(helix)
        created = service.create(
            {"customerId": 42, "productId": 9, "name": "Checking", "tag": "acct-1"}
        )
        listed = service.list(42)
        locked = service.lock(
            {
                "customerId": 42,
                "accountId": 100,
                "lockTypeCode": "CST",
                "lockReasonTypeCode": "ADM",
            }
        )
        stop = service.create_stop_pay(
            {
                "customerId": 42,
                "accountId": 100,
                "paymentType": "Check",
                "checkNumberMinimum": 1,
                "checkNumberMaximum": 1,
                "amountMinimum": 1.0,
                "amountMaximum": 100.0,
            }
        )
        stops = service.list_stop_pays(42, 100)
        cancelled = service.cancel_stop_pay(42, 100, 55)

    assert created["accountId"] == 100
    assert "****" in created["accountNumber"]
    assert listed[0]["availableBalance"] == 12.5
    assert locked["isLocked"] is True
    assert stop["stopPayId"] == 55
    assert isinstance(stops, list) and stops[0]["stopPayId"] == 55
    assert cancelled["stopPayId"] == 55
    assert any("createCheckStopPay" in p for p in calls)


def test_account_routes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("Q2_HELIX_API_KEY", "key")
    monkeypatch.setenv("Q2_HELIX_API_SECRET", "secret")
    monkeypatch.setenv("Q2_ENVIRONMENT", "sandbox")
    reset_q2_config()

    def handler(request: httpx.Request) -> httpx.Response:
        if "/account/list/" in request.url.path:
            return httpx.Response(
                200,
                json={
                    "status": 0,
                    "data": [
                        {
                            "accountId": 1,
                            "customerId": 42,
                            "status": "Open",
                            "availableBalance": 5,
                            "type": "Checking",
                        }
                    ],
                },
            )
        return httpx.Response(
            200,
            json={
                "status": 0,
                "data": {
                    "accountId": 1,
                    "customerId": 42,
                    "status": "Open",
                    "availableBalance": 5,
                    "type": "Checking",
                },
            },
        )

    original = HelixClient.__init__

    def patched(self, config=None, *, client=None):  # type: ignore[no-untyped-def]
        original(
            self,
            config or _cfg(),
            client=client or httpx.Client(transport=httpx.MockTransport(handler)),
        )

    monkeypatch.setattr(HelixClient, "__init__", patched)
    client = TestClient(app)
    listed = client.get("/api/v1/q2/accounts/by-customer/42")
    assert listed.status_code == 200
    assert listed.json()["accounts"][0]["accountId"] == 1
    detail = client.get("/api/v1/q2/accounts/42/1")
    assert detail.status_code == 200
    assert detail.json()["account"]["availableBalance"] == 5
