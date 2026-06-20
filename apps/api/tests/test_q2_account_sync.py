"""Tests for Q2 account provisioning orchestrator."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from crm_api.db import Base
from crm_api.models.customer import Customer
from crm_api.models.q2_account_sync import Q2AccountSync
from crm_api.models.q2_customer_sync import Q2CustomerSync
from ext.q2.config import Q2ConfigError, get_q2_config
from ext.q2.exceptions import Q2ApiError, Q2DuplicateTagError
from ext.q2.models.account import Q2Account
from ext.q2.services.account import Q2AccountService
from ext.q2.services.sync_accounts import AccountSyncService, account_tag


@pytest.fixture
def session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine)
    db = factory()
    try:
        yield db
    finally:
        db.close()


def _add_synced_customer(session: Session) -> tuple[Customer, Q2CustomerSync]:
    customer = Customer(
        first_name="Bob",
        last_name="Smith",
        email="bob@example.com",
        is_active=True,
    )
    session.add(customer)
    session.commit()
    session.refresh(customer)
    customer_sync = Q2CustomerSync(
        customer_id=customer.id,
        tag=str(customer.id),
        q2_customer_id="q2-999",
        sync_status="synced",
    )
    session.add(customer_sync)
    session.commit()
    return customer, customer_sync


def test_skip_when_account_already_synced(session: Session, monkeypatch) -> None:
    customer, customer_sync = _add_synced_customer(session)
    tag = account_tag(customer.id)
    session.add(
        Q2AccountSync(
            customer_id=customer.id,
            q2_customer_id=customer_sync.q2_customer_id,
            q2_account_id="acc-1",
            product_id="100",
            account_tag=tag,
            sync_status="synced",
        )
    )
    session.commit()

    mock_q2 = MagicMock(spec=Q2AccountService)
    monkeypatch.setenv("Q2_HELIX_DEFAULT_PRODUCT_ID", "100")
    get_q2_config.cache_clear()
    service = AccountSyncService(mock_q2)
    outcome = service.provision_one(session, customer_sync)
    assert outcome == "skipped"
    mock_q2.create.assert_not_called()


def test_create_success_path(session: Session, monkeypatch) -> None:
    customer, customer_sync = _add_synced_customer(session)
    tag = account_tag(customer.id)
    mock_q2 = MagicMock(spec=Q2AccountService)
    mock_q2.safe_get_by_tag.return_value = None
    mock_q2.create.return_value = Q2Account(account_id="acc-new", tag=tag)

    monkeypatch.setenv("Q2_HELIX_DEFAULT_PRODUCT_ID", "100")
    get_q2_config.cache_clear()
    service = AccountSyncService(mock_q2)
    outcome = service.provision_one(session, customer_sync)
    assert outcome == "provisioned"
    row = session.query(Q2AccountSync).filter_by(customer_id=customer.id).one()
    assert row.sync_status == "synced"
    assert row.q2_account_id == "acc-new"
    mock_q2.create.assert_called_once()


def test_missing_product_id_config_error(session: Session, monkeypatch) -> None:
    _, customer_sync = _add_synced_customer(session)
    monkeypatch.delenv("Q2_HELIX_DEFAULT_PRODUCT_ID", raising=False)
    get_q2_config.cache_clear()

    mock_q2 = MagicMock(spec=Q2AccountService)
    service = AccountSyncService(mock_q2)
    with pytest.raises(Q2ConfigError):
        service.run_sync(session)
    mock_q2.create.assert_not_called()


def test_failed_create_sets_sync_status_failed(session: Session, monkeypatch) -> None:
    customer, customer_sync = _add_synced_customer(session)
    mock_q2 = MagicMock(spec=Q2AccountService)
    mock_q2.safe_get_by_tag.return_value = None
    mock_q2.create.side_effect = Q2ApiError("upstream error", status_code=500)

    monkeypatch.setenv("Q2_HELIX_DEFAULT_PRODUCT_ID", "100")
    get_q2_config.cache_clear()
    service = AccountSyncService(mock_q2)
    outcome = service.provision_one(session, customer_sync)
    assert outcome == "failed"
    row = session.query(Q2AccountSync).filter_by(customer_id=customer.id).one()
    assert row.sync_status == "failed"
    assert row.last_error is not None


def test_duplicate_tag_treated_as_provisioned(session: Session, monkeypatch) -> None:
    customer, customer_sync = _add_synced_customer(session)
    tag = account_tag(customer.id)
    mock_q2 = MagicMock(spec=Q2AccountService)
    mock_q2.safe_get_by_tag.return_value = None
    mock_q2.create.side_effect = Q2DuplicateTagError("duplicate", status_code=409)
    mock_q2.get_by_tag.return_value = Q2Account(account_id="acc-existing", tag=tag)

    monkeypatch.setenv("Q2_HELIX_DEFAULT_PRODUCT_ID", "100")
    get_q2_config.cache_clear()
    service = AccountSyncService(mock_q2)
    outcome = service.provision_one(session, customer_sync)
    assert outcome == "provisioned"
    row = session.query(Q2AccountSync).filter_by(customer_id=customer.id).one()
    assert row.q2_account_id == "acc-existing"


def test_eligible_only_from_synced_customers(session: Session, monkeypatch) -> None:
    customer = Customer(
        first_name="Carol",
        last_name="Lee",
        email="carol@example.com",
        is_active=True,
    )
    session.add(customer)
    session.commit()
    session.refresh(customer)
    session.add(
        Q2CustomerSync(
            customer_id=customer.id,
            tag=str(customer.id),
            sync_status="pending",
        )
    )
    session.commit()

    mock_q2 = MagicMock(spec=Q2AccountService)
    monkeypatch.setenv("Q2_HELIX_DEFAULT_PRODUCT_ID", "100")
    get_q2_config.cache_clear()
    service = AccountSyncService(mock_q2)
    result = service.run_sync(session)
    assert result.processed == 0
    mock_q2.create.assert_not_called()


def test_status_shows_zero_eligible_when_all_provisioned(
    session: Session, monkeypatch
) -> None:
    customer, customer_sync = _add_synced_customer(session)
    tag = account_tag(customer.id)
    session.add(
        Q2AccountSync(
            customer_id=customer.id,
            q2_customer_id=customer_sync.q2_customer_id,
            q2_account_id="acc-1",
            product_id="100",
            account_tag=tag,
            sync_status="synced",
        )
    )
    session.commit()

    monkeypatch.setenv("Q2_HELIX_DEFAULT_PRODUCT_ID", "100")
    get_q2_config.cache_clear()
    status = AccountSyncService(MagicMock(spec=Q2AccountService)).get_status(session)
    assert status.eligible == 0
    assert status.provisioned == 1
    assert status.total == 1


def test_idempotent_rerun_skips_second_create(session: Session, monkeypatch) -> None:
    customer, customer_sync = _add_synced_customer(session)
    tag = account_tag(customer.id)
    mock_q2 = MagicMock(spec=Q2AccountService)
    mock_q2.safe_get_by_tag.return_value = None
    mock_q2.create.return_value = Q2Account(account_id="acc-1", tag=tag)

    monkeypatch.setenv("Q2_HELIX_DEFAULT_PRODUCT_ID", "100")
    get_q2_config.cache_clear()
    service = AccountSyncService(mock_q2)
    service.provision_one(session, customer_sync)
    mock_q2.reset_mock()

    outcome = service.provision_one(session, customer_sync)
    assert outcome == "skipped"
    mock_q2.create.assert_not_called()
