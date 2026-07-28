"""Unit tests for local customer provisioning (idempotent sync)."""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ext.q2.client import HelixClient  # noqa: E402
from ext.q2.config import Q2Config  # noqa: E402
from ext.q2.db import Base, get_engine  # noqa: E402
from ext.q2.models.local_customer import ProvisionStatus  # noqa: E402
from ext.q2.repository.customers import LocalCustomerRepository  # noqa: E402
from ext.q2.services.account import AccountService  # noqa: E402
from ext.q2.services.customer import CustomerService  # noqa: E402
from ext.q2.services.provisioner import (  # noqa: E402
    CustomerAccountProvisioner,
    ProvisionOutcome,
)


@pytest.fixture()
def db_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Session:
    db_url = f"sqlite:///{tmp_path / 'prov.db'}"
    monkeypatch.setenv("Q2_DATABASE_URL", db_url)
    monkeypatch.setenv("Q2_HELIX_DEFAULT_PRODUCT_ID", "10")
    get_engine.cache_clear()
    engine = get_engine(db_url)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = SessionLocal()
    try:
        yield session
        session.commit()
    finally:
        session.close()
        engine.dispose()
        get_engine.cache_clear()


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


def test_provisioner_onboards_and_creates_account(db_session: Session) -> None:
    calls: list[str] = []
    seq = {"customer": 1000, "account": 2000}

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        body = json.loads(request.content.decode() or "{}")
        if request.url.path.endswith("/customer/getByTag"):
            return httpx.Response(404, json={"message": "not found"})
        if request.url.path.endswith("/customer/onboard"):
            seq["customer"] += 1
            return httpx.Response(
                200,
                json={
                    "data": {
                        "customerId": seq["customer"],
                        "tag": body.get("tag"),
                        "status": "Active",
                    }
                },
            )
        if request.url.path.endswith("/account/list"):
            return httpx.Response(200, json={"data": {"accounts": []}})
        if request.url.path.endswith("/account/create"):
            seq["account"] += 1
            return httpx.Response(
                200,
                json={
                    "data": {
                        "accountId": seq["account"],
                        "customerId": body.get("customerId"),
                        "productId": 10,
                        "status": "Open",
                        "tag": body.get("tag"),
                        "name": body.get("name"),
                        "accountNumber": "1234567890",
                    }
                },
            )
        return httpx.Response(500, json={"message": f"unexpected {request.url.path}"})

    helix = _client_with_handler(handler)
    repo = LocalCustomerRepository(db_session)
    repo.ensure_seed_customers()
    provisioner = CustomerAccountProvisioner(
        repo,
        customer_service=CustomerService(helix),
        account_service=AccountService(helix),
        product_id="10",
    )
    bulk = provisioner.sync_all()
    assert bulk.processed == 3
    assert bulk.failed == 0
    assert bulk.succeeded == 3
    assert "/customer/onboard" in calls
    assert "/account/create" in calls
    customers = repo.list_active()
    assert all(c.provision_status == ProvisionStatus.ACCOUNT_CREATED.value for c in customers)
    assert all(c.q2_customer_id for c in customers)
    assert all(c.q2_accounts for c in customers)
    assert {c.q2_accounts[0].q2_account_id for c in customers} == {"2001", "2002", "2003"}
    provisioner.close()


def test_provisioner_idempotent_skips_existing(db_session: Session) -> None:
    create_calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode() or "{}")
        tag = str(body.get("tag") or body.get("customerId") or "")
        if request.url.path.endswith("/customer/getByTag"):
            tag = str(body.get("tag"))
            cid = abs(hash(tag)) % 10000 + 1
            return httpx.Response(
                200,
                json={"data": {"customerId": cid, "tag": tag, "status": "Active"}},
            )
        if request.url.path.endswith("/account/list"):
            # list body uses customerId — map stably
            cid = int(body.get("customerId") or 0)
            return httpx.Response(
                200,
                json={
                    "data": {
                        "accounts": [
                            {
                                "accountId": 70000 + cid,
                                "productId": 10,
                                "status": "Open",
                                "tag": f"acct-{cid}",
                                "name": f"Account {cid}",
                            }
                        ]
                    }
                },
            )
        if request.url.path.endswith("/account/create"):
            create_calls["n"] += 1
            return httpx.Response(500, json={"message": "should not create"})
        if request.url.path.endswith("/customer/onboard"):
            return httpx.Response(500, json={"message": "should not onboard"})
        return httpx.Response(404, json={"message": "missing"})

    helix = _client_with_handler(handler)
    repo = LocalCustomerRepository(db_session)
    repo.ensure_seed_customers()
    provisioner = CustomerAccountProvisioner(
        repo,
        customer_service=CustomerService(helix),
        account_service=AccountService(helix),
        product_id="10",
    )
    first = provisioner.sync_all()
    second = provisioner.sync_all()
    assert first.failed == 0 and second.failed == 0
    assert create_calls["n"] == 0
    assert all(r.outcome == ProvisionOutcome.EXISTING for r in second.results)
    provisioner.close()


def test_bulk_isolates_row_failures(db_session: Session) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode() or "{}")
        if request.url.path.endswith("/customer/getByTag"):
            tag = body.get("tag")
            if tag == "local-alan-002":
                return httpx.Response(500, json={"message": "boom"})
            return httpx.Response(404, json={"message": "not found"})
        if request.url.path.endswith("/customer/onboard"):
            cid = abs(hash(body.get("tag"))) % 100000 + 1
            return httpx.Response(
                200,
                json={"data": {"customerId": cid, "tag": body.get("tag")}},
            )
        if request.url.path.endswith("/account/list"):
            return httpx.Response(200, json={"data": {"accounts": []}})
        if request.url.path.endswith("/account/create"):
            aid = abs(hash(body.get("tag"))) % 100000 + 50000
            return httpx.Response(
                200,
                json={
                    "data": {
                        "accountId": aid,
                        "productId": 10,
                        "status": "Open",
                        "tag": body.get("tag"),
                        "name": body.get("name"),
                    }
                },
            )
        return httpx.Response(404, json={"message": "x"})

    helix = _client_with_handler(handler)
    repo = LocalCustomerRepository(db_session)
    repo.ensure_seed_customers()
    provisioner = CustomerAccountProvisioner(
        repo,
        customer_service=CustomerService(helix),
        account_service=AccountService(helix),
        product_id="10",
    )
    bulk = provisioner.sync_all()
    assert bulk.processed == 3
    assert bulk.failed == 1
    assert bulk.succeeded == 2
    failed = [c for c in repo.list_active() if c.provision_status == ProvisionStatus.FAILED.value]
    assert len(failed) == 1
    assert failed[0].tag == "local-alan-002"
    assert failed[0].last_provision_error
    provisioner.close()


def test_provisioning_routes(db_session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("Q2_HELIX_DEFAULT_PRODUCT_ID", "10")
    seq = {"customer": 0, "account": 100}

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode() or "{}")
        if request.url.path.endswith("/customer/getByTag"):
            return httpx.Response(404, json={"message": "not found"})
        if request.url.path.endswith("/customer/onboard"):
            seq["customer"] += 1
            return httpx.Response(
                200, json={"data": {"customerId": seq["customer"], "tag": body.get("tag")}}
            )
        if request.url.path.endswith("/account/list"):
            return httpx.Response(200, json={"data": {"accounts": []}})
        if request.url.path.endswith("/account/create"):
            seq["account"] += 1
            return httpx.Response(
                200,
                json={
                    "data": {
                        "accountId": seq["account"],
                        "productId": 10,
                        "status": "Open",
                        "tag": body.get("tag"),
                        "name": body.get("name"),
                    }
                },
            )
        return httpx.Response(404, json={"message": "missing"})

    helix = _client_with_handler(handler)
    from crm_api.main import app
    from ext.q2.routes import provisioning as q2_provisioning

    def override_provisioner():
        repo = LocalCustomerRepository(db_session)
        provisioner = CustomerAccountProvisioner(
            repo,
            customer_service=CustomerService(helix),
            account_service=AccountService(helix),
            product_id="10",
        )
        try:
            yield provisioner
        finally:
            provisioner.close()

    app.dependency_overrides[q2_provisioning.get_provisioner] = override_provisioner
    client = TestClient(app)
    bulk = client.post("/api/v1/q2/provisioning/customers/sync")
    assert bulk.status_code == 200
    payload = bulk.json()
    assert payload["processed"] == 3
    assert payload["failed"] == 0

    local_id = payload["results"][0]["local_id"]
    single = client.post(f"/api/v1/q2/provisioning/customers/{local_id}/sync")
    assert single.status_code == 200
    assert single.json()["outcome"] in {"created", "existing"}

    missing = client.post(f"/api/v1/q2/provisioning/customers/{uuid.uuid4()}/sync")
    assert missing.status_code == 404
    app.dependency_overrides.clear()
