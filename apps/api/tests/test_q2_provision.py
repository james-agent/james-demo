"""Tests for Q2 Helix provisioning operator API."""

from __future__ import annotations

from fastapi.testclient import TestClient

from crm_api.main import app
from ext.q2.db import Base, get_engine, get_session_factory
from ext.q2.models.account import Q2Account
from ext.q2.models.customer import Q2Customer

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
