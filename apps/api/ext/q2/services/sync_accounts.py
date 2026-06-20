"""Bulk account provisioning orchestrator for synced Q2 customers."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from crm_api.models.q2_account_sync import Q2AccountSync
from crm_api.models.q2_customer_sync import Q2CustomerSync
from ext.q2.config import Q2ConfigError, get_q2_config
from ext.q2.exceptions import Q2ApiError, Q2DuplicateTagError
from ext.q2.models.account import AccountSyncStatusResponse, AccountSyncTriggerResponse
from ext.q2.services.account import Q2AccountService

logger = logging.getLogger(__name__)


def account_tag(customer_id: UUID) -> str:
    return f"{customer_id}-primary"


def default_account_name(customer_sync: Q2CustomerSync) -> str:
    return f"Primary Account ({customer_sync.tag[:8]})"


def _get_or_create_account_row(
    session: Session,
    customer_sync: Q2CustomerSync,
    *,
    product_id: str,
) -> Q2AccountSync:
    row = session.scalar(
        select(Q2AccountSync).where(
            Q2AccountSync.customer_id == customer_sync.customer_id,
            Q2AccountSync.product_id == product_id,
        )
    )
    if row is None:
        row = Q2AccountSync(
            customer_id=customer_sync.customer_id,
            q2_customer_id=customer_sync.q2_customer_id or "",
            product_id=product_id,
            account_tag=account_tag(customer_sync.customer_id),
            account_name=default_account_name(customer_sync),
            sync_status="pending",
        )
        session.add(row)
        session.flush()
    return row


def _mark_synced(row: Q2AccountSync, q2_account_id: str | None) -> None:
    row.sync_status = "synced"
    row.q2_account_id = q2_account_id
    row.last_error = None
    row.last_synced_at = datetime.now(UTC)


def _mark_failed(row: Q2AccountSync, error: str) -> None:
    row.sync_status = "failed"
    row.last_error = error[:2000]


class AccountSyncService:
    def __init__(self, q2_service: Q2AccountService | None = None) -> None:
        self.q2_service = q2_service or Q2AccountService()

    def _resolve_product_id(self, product_id: str | None) -> str:
        config = get_q2_config()
        resolved = (product_id or config.default_product_id).strip()
        if not resolved:
            raise Q2ConfigError(
                "Missing required Q2 configuration: Q2_HELIX_DEFAULT_PRODUCT_ID"
            )
        return resolved

    def provision_one(
        self,
        session: Session,
        customer_sync: Q2CustomerSync,
        *,
        product_id: str | None = None,
    ) -> str:
        if customer_sync.sync_status != "synced" or not customer_sync.q2_customer_id:
            return "skipped"

        resolved_product = self._resolve_product_id(product_id)
        row = _get_or_create_account_row(
            session, customer_sync, product_id=resolved_product
        )
        if row.sync_status == "synced":
            return "skipped"

        tag = row.account_tag
        try:
            existing = self.q2_service.safe_get_by_tag(tag)
            if existing and existing.account_id:
                _mark_synced(row, existing.account_id)
                session.commit()
                return "provisioned"

            result = self.q2_service.create(
                customer_id=customer_sync.q2_customer_id,
                product_id=resolved_product,
                name=row.account_name or default_account_name(customer_sync),
                tag=tag,
            )
            _mark_synced(row, result.account_id)
            session.commit()
            return "provisioned"
        except Q2DuplicateTagError:
            existing = self.q2_service.get_by_tag(tag)
            _mark_synced(row, existing.account_id)
            session.commit()
            return "provisioned"
        except Q2ApiError as exc:
            _mark_failed(row, str(exc))
            session.commit()
            logger.warning(
                "Q2 account provision failed for customer %s: %s",
                customer_sync.customer_id,
                exc,
            )
            return "failed"
        except Q2ConfigError as exc:
            _mark_failed(row, str(exc))
            session.commit()
            return "failed"

    def run_sync(
        self, session: Session, *, product_id: str | None = None
    ) -> AccountSyncTriggerResponse:
        self._resolve_product_id(product_id)
        eligible = session.scalars(
            select(Q2CustomerSync).where(Q2CustomerSync.sync_status == "synced")
        ).all()

        provisioned = failed = skipped = 0
        for customer_sync in eligible:
            outcome = self.provision_one(session, customer_sync, product_id=product_id)
            if outcome == "provisioned":
                provisioned += 1
            elif outcome == "failed":
                failed += 1
            else:
                skipped += 1

        return AccountSyncTriggerResponse(
            processed=len(eligible),
            provisioned=provisioned,
            failed=failed,
            skipped=skipped,
        )

    def get_status(self, session: Session) -> AccountSyncStatusResponse:
        synced_customers = session.scalars(
            select(Q2CustomerSync).where(Q2CustomerSync.sync_status == "synced")
        ).all()
        eligible_ids = {row.customer_id for row in synced_customers}

        counts = dict(
            session.execute(
                select(Q2AccountSync.sync_status, func.count()).group_by(
                    Q2AccountSync.sync_status
                )
            ).all()
        )
        provisioned = counts.get("synced", 0)
        failed = counts.get("failed", 0)
        skipped = counts.get("skipped", 0)
        pending = counts.get("pending", 0)

        provisioned_customer_ids = {
            row.customer_id
            for row in session.scalars(
                select(Q2AccountSync).where(Q2AccountSync.sync_status == "synced")
            ).all()
        }
        unprovisioned = len(eligible_ids - provisioned_customer_ids)
        eligible = unprovisioned + pending

        return AccountSyncStatusResponse(
            eligible=eligible,
            provisioned=provisioned,
            failed=failed,
            skipped=skipped,
            total=len(eligible_ids),
        )
