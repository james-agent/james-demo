"""Tests for Q2 customer sync orchestrator."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from crm_api.db import Base
from crm_api.models.customer import Customer
from crm_api.models.q2_customer_sync import Q2CustomerSync
from ext.q2.exceptions import Q2ApiError
from ext.q2.models.customer import Q2CustomerResponse
from ext.q2.services.customer import Q2CustomerService
from ext.q2.services.sync_customers import CustomerSyncService, customer_tag


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


def _add_customer(session: Session) -> Customer:
    customer = Customer(
        first_name="Alice",
        last_name="Morgan",
        email="alice@example.com",
        is_active=True,
    )
    session.add(customer)
    session.commit()
    session.refresh(customer)
    return customer


def test_skip_when_already_synced(session: Session) -> None:
    customer = _add_customer(session)
    tag = customer_tag(customer.id)
    session.add(
        Q2CustomerSync(
            customer_id=customer.id,
            tag=tag,
            q2_customer_id="q2-123",
            sync_status="synced",
        )
    )
    session.commit()

    mock_q2 = MagicMock(spec=Q2CustomerService)
    service = CustomerSyncService(mock_q2)
    outcome = service.sync_one(session, customer, mode="full")
    assert outcome == "skipped"
    mock_q2.onboard.assert_not_called()


def test_onboard_success_path(session: Session) -> None:
    customer = _add_customer(session)
    tag = customer_tag(customer.id)
    mock_q2 = MagicMock(spec=Q2CustomerService)
    mock_q2.safe_get_by_tag.return_value = None
    mock_q2.onboard.return_value = Q2CustomerResponse(
        customer_id="q2-new",
        tag=tag,
        kyc_status="Verified",
    )

    service = CustomerSyncService(mock_q2)
    outcome = service.sync_one(session, customer, mode="full")
    assert outcome == "synced"
    row = session.query(Q2CustomerSync).filter_by(customer_id=customer.id).one()
    assert row.sync_status == "synced"
    assert row.q2_customer_id == "q2-new"
    mock_q2.onboard.assert_called_once()


def test_duplicate_tag_treated_as_synced(session: Session) -> None:
    customer = _add_customer(session)
    tag = customer_tag(customer.id)
    mock_q2 = MagicMock(spec=Q2CustomerService)
    mock_q2.safe_get_by_tag.return_value = None
    from ext.q2.exceptions import Q2DuplicateTagError

    mock_q2.onboard.side_effect = Q2DuplicateTagError("duplicate", status_code=409)
    mock_q2.get_by_tag.return_value = Q2CustomerResponse(
        customer_id="q2-existing", tag=tag
    )

    service = CustomerSyncService(mock_q2)
    outcome = service.sync_one(session, customer, mode="full")
    assert outcome == "synced"
    row = session.query(Q2CustomerSync).filter_by(customer_id=customer.id).one()
    assert row.q2_customer_id == "q2-existing"


def test_failure_records_sync_status_failed(session: Session) -> None:
    customer = _add_customer(session)
    mock_q2 = MagicMock(spec=Q2CustomerService)
    mock_q2.safe_get_by_tag.return_value = None
    mock_q2.onboard.side_effect = Q2ApiError("upstream error", status_code=500)

    service = CustomerSyncService(mock_q2)
    outcome = service.sync_one(session, customer, mode="full")
    assert outcome == "failed"
    row = session.query(Q2CustomerSync).filter_by(customer_id=customer.id).one()
    assert row.sync_status == "failed"
    assert row.last_error is not None


def test_idempotent_full_sync_skips_second_onboard(session: Session) -> None:
    customer = _add_customer(session)
    tag = customer_tag(customer.id)
    mock_q2 = MagicMock(spec=Q2CustomerService)
    mock_q2.safe_get_by_tag.return_value = None
    mock_q2.onboard.return_value = Q2CustomerResponse(customer_id="q2-1", tag=tag)

    service = CustomerSyncService(mock_q2)
    service.sync_one(session, customer, mode="full")
    mock_q2.reset_mock()
    mock_q2.safe_get_by_tag.return_value = Q2CustomerResponse(
        customer_id="q2-1", tag=tag
    )

    outcome = service.sync_one(session, customer, mode="full")
    assert outcome == "skipped"
    mock_q2.onboard.assert_not_called()
