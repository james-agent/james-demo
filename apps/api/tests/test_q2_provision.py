"""Tests for Q2 Helix provisioning operator API."""

from __future__ import annotations

from fastapi.testclient import TestClient

from crm_api.main import app
from ext.q2.config import clear_q2_config_cache, load_q2_config
from ext.q2.db import Base, get_engine, get_session_factory
from ext.q2.errors import Q2Error
from ext.q2.models.account import Q2Account
from ext.q2.models.customer import Q2Customer
from ext.q2.services.customer import CustomerService

client = TestClient(app)


def _reset_tables() -> None:
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_q2_health_mock_mode() -> None:
    response = client.get("/api/v1/q2/health")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["mock_mode"] is True
    assert data["code"] is None
    # Security: never leak credentials in health payload.
    blob = response.text.lower()
    assert "test-secret" not in blob
    assert "api_secret" not in blob
    assert "password" not in blob


def test_q2_health_config_error(monkeypatch) -> None:
    monkeypatch.setenv("Q2_MOCK_MODE", "false")
    monkeypatch.setenv("Q2_HELIX_API_KEY", "")
    monkeypatch.setenv("Q2_HELIX_API_SECRET", "")
    monkeypatch.setenv("Q2_HELIX_PROGRAM_ID", "")
    clear_q2_config_cache()

    response = client.get("/api/v1/q2/health")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert data["code"] == "CONFIG_ERROR"
    assert "Q2_HELIX_API_KEY" in data["missing_keys"]
    assert "test-secret" not in response.text

    # Restore mock mode for subsequent tests.
    monkeypatch.setenv("Q2_MOCK_MODE", "true")
    monkeypatch.setenv("Q2_HELIX_API_KEY", "test-key")
    monkeypatch.setenv("Q2_HELIX_API_SECRET", "test-secret")
    monkeypatch.setenv("Q2_HELIX_PROGRAM_ID", "test-program")
    clear_q2_config_cache()
    assert load_q2_config().mock_mode is True


def test_provision_all_customers_idempotent() -> None:
    _reset_tables()

    first = client.post("/api/v1/q2/provision", json={"sync_from_crm": True})
    assert first.status_code == 200
    payload = first.json()
    assert payload["status"] == "succeeded"
    assert payload["total_customers"] >= 25
    assert payload["succeeded_count"] == payload["total_customers"]
    assert payload["failed_count"] == 0

    second = client.post("/api/v1/q2/provision", json={"sync_from_crm": True})
    assert second.status_code == 200
    again = second.json()
    assert again["status"] == "succeeded"
    assert again["skipped_count"] == again["total_customers"]
    assert again["succeeded_count"] == 0

    status = client.get(f"/api/v1/q2/provision/{again['id']}")
    assert status.status_code == 200
    assert status.json()["id"] == again["id"]

    session = get_session_factory()()
    try:
        customers = session.query(Q2Customer).all()
        accounts = session.query(Q2Account).all()
        assert len(customers) >= 25
        assert all(c.q2_customer_id for c in customers)
        assert len(accounts) >= 25
        assert all(a.q2_account_id for a in accounts)
    finally:
        session.close()


def test_provision_filtered_keys() -> None:
    _reset_tables()
    response = client.post(
        "/api/v1/q2/provision",
        json={"sync_from_crm": True, "local_customer_keys": ["cust-001", "cust-002"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_customers"] == 2
    assert data["succeeded_count"] == 2


def test_provision_partial_on_helix_failure(monkeypatch) -> None:
    """When Helix rejects one customer, run status is partial (not full success)."""
    _reset_tables()
    original = CustomerService.onboard

    def flaky_onboard(self, data):  # noqa: ANN001
        if data.get("tag") == "cust-001":
            raise Q2Error("Helix rejected customer onboard", code="API_BUSINESS_ERROR", http_status=400)
        return original(self, data)

    monkeypatch.setattr(CustomerService, "onboard", flaky_onboard)

    response = client.post(
        "/api/v1/q2/provision",
        json={"sync_from_crm": True, "local_customer_keys": ["cust-001", "cust-002"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "partial"
    assert data["failed_count"] == 1
    assert data["succeeded_count"] == 1
    assert data["error_summary"]
    assert "cust-001" in data["error_summary"]
    assert data["status"] != "succeeded"


def test_provision_failed_when_all_fail(monkeypatch) -> None:
    _reset_tables()

    def always_fail(self, data):  # noqa: ANN001, ARG001
        raise Q2Error("Invalid credentials", code="AUTH_ERROR", http_status=401)

    monkeypatch.setattr(CustomerService, "onboard", always_fail)

    response = client.post(
        "/api/v1/q2/provision",
        json={"sync_from_crm": True, "local_customer_keys": ["cust-001"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "failed"
    assert data["failed_count"] == 1
    assert data["succeeded_count"] == 0
    assert "Invalid credentials" in (data["error_summary"] or "")
