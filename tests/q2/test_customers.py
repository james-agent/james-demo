"""Unit tests for Q2 Helix customer management."""

from __future__ import annotations

import httpx
import pytest
from fastapi.testclient import TestClient

from james.ext.q2.client import HelixClient
from james.ext.q2.config import Q2Config, reset_q2_config
from james.ext.q2.errors import Q2APIError
from james.ext.q2.pii import mask_pii
from james.ext.q2.services.customer import CustomerService
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


def test_mask_pii_tax_and_email() -> None:
    masked = mask_pii({"taxId": "123456789", "emailAddress": "dwight@example.com"})
    assert masked["taxId"].endswith("6789")
    assert masked["emailAddress"].startswith("d***@")
    assert "123456789" not in masked["taxId"]


def test_customer_onboard_and_get() -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.url.path.endswith("/customer/onboard"):
            return httpx.Response(
                200,
                json={
                    "status": 0,
                    "data": {
                        "customerId": 42,
                        "tag": "user-1",
                        "status": "Active",
                        "kycStatus": "Verified",
                        "taxId": "123456789",
                        "emailAddress": "a@b.com",
                        "isBusiness": False,
                    },
                },
            )
        if "/customer/get/" in request.url.path:
            return httpx.Response(
                200,
                json={
                    "status": 0,
                    "data": {
                        "customerId": 42,
                        "tag": "user-1",
                        "status": "Active",
                        "kycStatus": "Verified",
                        "taxId": "123456789",
                    },
                },
            )
        return httpx.Response(404, json={"status": 1, "message": "not found"})

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    with HelixClient(_cfg(), client=http_client) as helix:
        service = CustomerService(helix)
        created = service.onboard(
            {
                "firstName": "Dwight",
                "lastName": "Schrute",
                "birthDate": "1970-01-20T00:00:00.000+00:00",
                "emailAddress": "a@b.com",
                "taxId": "123456789",
                "addresses": [
                    {
                        "addressLine1": "1 Rural",
                        "addressType": "Residence",
                        "city": "Honesdale",
                        "state": "PA",
                        "postalCode": "18431",
                        "country": "US",
                    }
                ],
                "phones": [{"number": "7175550177", "phoneType": "Mobile"}],
                "tag": "user-1",
            }
        )
        got = service.get(42)

    assert created["customerId"] == 42
    assert created["kycStatus"] == "Verified"
    assert "****" in created["taxId"]
    assert got["customerId"] == 42
    assert any(c.url.path.endswith("/customer/onboard") for c in calls)


def test_duplicate_tag_maps_to_duplicate_code() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": 1, "message": "Duplicate tag already exists"})

    with HelixClient(_cfg(), client=httpx.Client(transport=httpx.MockTransport(handler))) as helix:
        service = CustomerService(helix)
        with pytest.raises(Q2APIError) as exc:
            service.onboard(
                {
                    "firstName": "A",
                    "lastName": "B",
                    "birthDate": "1970-01-01T00:00:00.000+00:00",
                    "emailAddress": "a@b.com",
                    "taxId": "111111111",
                    "addresses": [
                        {
                            "addressLine1": "1",
                            "addressType": "Residence",
                            "city": "X",
                            "state": "PA",
                            "postalCode": "1",
                            "country": "US",
                        }
                    ],
                    "phones": [{"number": "1111111111", "phoneType": "Mobile"}],
                    "tag": "dup",
                }
            )
    assert exc.value.code == "DUPLICATE"


def test_customer_routes_mask_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("Q2_HELIX_API_KEY", "key")
    monkeypatch.setenv("Q2_HELIX_API_SECRET", "secret")
    monkeypatch.setenv("Q2_ENVIRONMENT", "sandbox")
    reset_q2_config()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "status": 0,
                "data": {
                    "customerId": 7,
                    "tag": "t",
                    "taxId": "999887777",
                    "kycStatus": "Verified",
                    "status": "Active",
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
    response = client.get("/api/v1/q2/customers/7")
    assert response.status_code == 200
    body = response.json()
    assert body["customer"]["customerId"] == 7
    assert "999887777" not in str(body)
