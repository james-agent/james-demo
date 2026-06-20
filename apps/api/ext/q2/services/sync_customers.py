"""Bulk sync orchestrator for local customers to Q2 Helix."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from crm_api.models.customer import Customer
from crm_api.models.q2_customer_sync import Q2CustomerSync
from crm_api.services.customer_registry import list_active_customers
from ext.q2.exceptions import Q2ApiError, Q2DuplicateTagError
from ext.q2.models.customer import SyncStatusResponse, SyncTriggerResponse
from ext.q2.services.customer import Q2CustomerService

logger = logging.getLogger(__name__)

SyncMode = Literal["full", "incremental"]


def customer_tag(customer_id: UUID) -> str:
    return str(customer_id)


def _get_or_create_sync_row(session: Session, customer: Customer) -> Q2CustomerSync:
    tag = customer_tag(customer.id)
    row = session.scalar(select(Q2CustomerSync).where(Q2CustomerSync.customer_id == customer.id))
    if row is None:
        row = Q2CustomerSync(customer_id=customer.id, tag=tag, sync_status="pending")
        session.add(row)
        session.flush()
    return row


def _mark_synced(row: Q2CustomerSync, q2_customer_id: str | None, kyc_status: str | None) -> None:
    row.sync_status = "synced"
    row.q2_customer_id = q2_customer_id
    row.kyc_status = kyc_status
    row.last_error = None
    row.last_synced_at = datetime.now(UTC)


def _mark_failed(row: Q2CustomerSync, error: str) -> None:
    row.sync_status = "failed"
    row.last_error = error[:2000]


def _should_process(row: Q2CustomerSync, mode: SyncMode) -> bool:
    if mode == "full":
        return row.sync_status != "synced"
    return row.sync_status in {"pending", "failed"}


class CustomerSyncService:
    def __init__(self, q2_service: Q2CustomerService | None = None) -> None:
        self.q2_service = q2_service or Q2CustomerService()

    def sync_one(self, session: Session, customer: Customer, *, mode: SyncMode = "full") -> str:
        row = _get_or_create_sync_row(session, customer)
        if not _should_process(row, mode):
            return "skipped"

        tag = row.tag
        try:
            existing = self.q2_service.safe_get_by_tag(tag)
            if existing and existing.customer_id:
                _mark_synced(row, existing.customer_id, existing.kyc_status)
                session.commit()
                return "synced"

            result = self.q2_service.onboard(customer, tag)
            _mark_synced(row, result.customer_id, result.kyc_status)
            session.commit()
            return "synced"
        except Q2DuplicateTagError:
            existing = self.q2_service.get_by_tag(tag)
            _mark_synced(row, existing.customer_id, existing.kyc_status)
            session.commit()
            return "synced"
        except Q2ApiError as exc:
            _mark_failed(row, str(exc))
            session.commit()
            logger.warning("Q2 sync failed for customer %s: %s", customer.id, exc)
            return "failed"

    def run_sync(self, session: Session, *, mode: SyncMode = "full") -> SyncTriggerResponse:
        customers = list_active_customers(session)
        synced = failed = skipped = 0
        for customer in customers:
            outcome = self.sync_one(session, customer, mode=mode)
            if outcome == "synced":
                synced += 1
            elif outcome == "failed":
                failed += 1
            else:
                skipped += 1
        return SyncTriggerResponse(
            mode=mode,
            processed=len(customers),
            synced=synced,
            failed=failed,
            skipped=skipped,
        )

    def get_status(self, session: Session) -> SyncStatusResponse:
        counts = dict(
            session.execute(
                select(Q2CustomerSync.sync_status, func.count())
                .group_by(Q2CustomerSync.sync_status)
            ).all()
        )
        active_total = len(list_active_customers(session))
        pending = counts.get("pending", 0)
        synced = counts.get("synced", 0)
        failed = counts.get("failed", 0)
        skipped = counts.get("skipped", 0)
        unmapped = max(active_total - (pending + synced + failed + skipped), 0)
        return SyncStatusResponse(
            pending=pending + unmapped,
            synced=synced,
            failed=failed,
            skipped=skipped,
            total=active_total,
        )
