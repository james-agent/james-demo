"""Idempotent local-customer → Helix customer + account sync."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from crm_api.ext.q2.client import Q2HelixClient, Q2HelixError
from crm_api.ext.q2.config import Q2Config, get_q2_config
from crm_api.ext.q2.models.account import AccountCreateRequest
from crm_api.ext.q2.models.customer import CustomerOnboardRequest, Q2Address, Q2Phone
from crm_api.ext.q2.services.account import AccountService
from crm_api.ext.q2.services.customer import CustomerService
from crm_api.models.customer import Customer

logger = logging.getLogger(__name__)


class SyncOutcome(str, Enum):
    CREATED = "created"
    LINKED_EXISTING = "linked_existing"
    SKIPPED_INCOMPLETE = "skipped_incomplete"
    FAILED = "failed"
    ALREADY_LINKED = "already_linked"


class SyncRowResult(BaseModel):
    local_customer_id: str
    outcome: SyncOutcome
    q2_sync_status: str
    q2_customer_id: int | None = None
    q2_account_id: int | None = None
    detail: str | None = None


class SyncBatchResult(BaseModel):
    processed: int
    results: list[SyncRowResult] = Field(default_factory=list)


class CustomerAccountSyncService:
    """Ensure each local customer has a Helix customer and primary account."""

    def __init__(
        self,
        session: AsyncSession | Session,
        client: Q2HelixClient | None = None,
        config: Q2Config | None = None,
    ) -> None:
        self.session = session
        self.config = config or get_q2_config()
        self.client = client or Q2HelixClient(self.config)
        self.customers = CustomerService(self.client)
        self.accounts = AccountService(self.client)

    async def sync_all(self) -> SyncBatchResult:
        customers = list(await self._list_customers())
        results: list[SyncRowResult] = []
        for customer in customers:
            results.append(await self.sync_one(customer))
        return SyncBatchResult(processed=len(results), results=results)

    async def sync_by_id(self, local_customer_id: UUID) -> SyncRowResult:
        customer = await self._get_customer(local_customer_id)
        if customer is None:
            return SyncRowResult(
                local_customer_id=str(local_customer_id),
                outcome=SyncOutcome.FAILED,
                q2_sync_status="failed",
                detail="Local customer not found",
            )
        return await self.sync_one(customer)

    async def sync_one(self, customer: Customer) -> SyncRowResult:
        if customer.q2_sync_status == "account_linked" and customer.q2_account_id:
            return SyncRowResult(
                local_customer_id=str(customer.id),
                outcome=SyncOutcome.ALREADY_LINKED,
                q2_sync_status=customer.q2_sync_status,
                q2_customer_id=customer.q2_customer_id,
                q2_account_id=customer.q2_account_id,
                detail="Already linked",
            )

        if not customer.is_kyc_complete():
            return await self._mark(
                customer,
                status="skipped_incomplete",
                outcome=SyncOutcome.SKIPPED_INCOMPLETE,
                error="Incomplete KYC fields for Helix onboard",
            )

        product_id = self.config.product_id
        if product_id is None:
            return await self._mark(
                customer,
                status="failed",
                outcome=SyncOutcome.FAILED,
                error="Q2_DEFAULT_PRODUCT_ID is not configured",
            )

        try:
            customer_outcome = await self._ensure_helix_customer(customer)
            account_outcome = await self._ensure_helix_account(customer, product_id)
            outcome = (
                SyncOutcome.CREATED
                if SyncOutcome.CREATED in (customer_outcome, account_outcome)
                else SyncOutcome.LINKED_EXISTING
            )
            return await self._mark(
                customer,
                status="account_linked",
                outcome=outcome,
                error=None,
            )
        except Q2HelixError as exc:
            logger.warning(
                "Q2 sync failed for local_customer_id=%s status=%s",
                customer.id,
                exc.status_code,
            )
            return await self._mark(
                customer,
                status="failed",
                outcome=SyncOutcome.FAILED,
                error=_safe_error(exc.message),
            )
        except Exception as exc:  # noqa: BLE001 — persist failure, continue batch
            logger.exception("Unexpected Q2 sync error for local_customer_id=%s", customer.id)
            return await self._mark(
                customer,
                status="failed",
                outcome=SyncOutcome.FAILED,
                error=_safe_error(str(exc)),
            )

    async def _ensure_helix_customer(self, customer: Customer) -> SyncOutcome:
        tag = customer.customer_tag()
        customer.q2_customer_tag = tag
        try:
            existing = await self.customers.get_by_tag(tag)
            if existing.customerId is not None:
                customer.q2_customer_id = existing.customerId
                customer.q2_sync_status = "customer_linked"
                return SyncOutcome.LINKED_EXISTING
        except Q2HelixError as exc:
            if exc.status_code not in {404, 400}:
                raise

        try:
            onboarded = await self.customers.onboard(_to_onboard_request(customer, tag))
            created = True
        except Q2HelixError as exc:
            if exc.status_code != 409:
                raise
            onboarded = await self.customers.get_by_tag(tag)
            created = False

        if onboarded.customerId is None:
            raise Q2HelixError("Helix onboard returned no customerId", status_code=502)
        customer.q2_customer_id = onboarded.customerId
        customer.q2_sync_status = "customer_linked"
        return SyncOutcome.CREATED if created else SyncOutcome.LINKED_EXISTING

    async def _ensure_helix_account(self, customer: Customer, product_id: int) -> SyncOutcome:
        if customer.q2_customer_id is None:
            raise Q2HelixError("Cannot create account without Helix customerId", status_code=502)

        tag = customer.account_tag()
        customer.q2_account_tag = tag
        try:
            existing = await self.accounts.get_by_tag(tag)
            if existing.accountId is not None:
                customer.q2_account_id = existing.accountId
                return SyncOutcome.LINKED_EXISTING
        except Q2HelixError as exc:
            if exc.status_code not in {404, 400}:
                raise

        try:
            created_account = await self.accounts.create(
                AccountCreateRequest(
                    customerId=int(customer.q2_customer_id),
                    productId=product_id,
                    name=f"{customer.first_name} {customer.last_name}".strip() or "Primary",
                    tag=tag,
                )
            )
            was_created = True
        except Q2HelixError as exc:
            if exc.status_code != 409:
                raise
            created_account = await self.accounts.get_by_tag(tag)
            was_created = False

        if created_account.accountId is None:
            raise Q2HelixError("Helix account create returned no accountId", status_code=502)
        customer.q2_account_id = created_account.accountId
        return SyncOutcome.CREATED if was_created else SyncOutcome.LINKED_EXISTING

    async def _mark(
        self,
        customer: Customer,
        *,
        status: str,
        outcome: SyncOutcome,
        error: str | None,
    ) -> SyncRowResult:
        customer.q2_sync_status = status
        customer.q2_last_error = error
        customer.q2_synced_at = datetime.now(timezone.utc)
        customer.updated_at = datetime.now(timezone.utc)
        self.session.add(customer)
        await self._flush()
        return SyncRowResult(
            local_customer_id=str(customer.id),
            outcome=outcome,
            q2_sync_status=status,
            q2_customer_id=customer.q2_customer_id,
            q2_account_id=customer.q2_account_id,
            detail=error,
        )

    async def _list_customers(self) -> list[Customer]:
        result = await self.session.execute(select(Customer).order_by(Customer.created_at))
        return list(result.scalars().all())

    async def _get_customer(self, local_customer_id: UUID) -> Customer | None:
        result = await self.session.execute(
            select(Customer).where(Customer.id == local_customer_id)
        )
        return result.scalar_one_or_none()

    async def _flush(self) -> None:
        flush = getattr(self.session, "flush", None)
        if flush is None:
            return
        maybe = flush()
        if hasattr(maybe, "__await__"):
            await maybe


def _to_onboard_request(customer: Customer, tag: str) -> CustomerOnboardRequest:
    addresses: list[Q2Address] = []
    if customer.address_line1 and customer.city and customer.state and customer.postal_code:
        addresses.append(
            Q2Address(
                addressLine1=customer.address_line1,
                city=customer.city,
                state=customer.state,
                postalCode=customer.postal_code,
                countryCode=customer.country_code or "USA",
            )
        )
    phones: list[Q2Phone] = []
    if customer.phone_number:
        phones.append(Q2Phone(phoneNumber=customer.phone_number))

    birth = customer.birth_date
    birth_iso = (
        f"{birth.isoformat()}T00:00:00.000+00:00" if birth is not None else ""
    )
    return CustomerOnboardRequest(
        firstName=customer.first_name,
        lastName=customer.last_name,
        middleName=customer.middle_name,
        birthDate=birth_iso,
        taxId=customer.tax_id or "",
        taxIdType=_tax_id_type(customer.tax_id_type),
        emailAddress=customer.email,
        tag=tag,
        addresses=addresses,
        phones=phones,
    )


def _tax_id_type(value: str | None) -> Any:
    if value in {"SSN", "EIN", "ITIN"}:
        return value
    return "SSN"


def _safe_error(message: str) -> str:
    """Operator-safe error text — never echo raw tax ids or account numbers."""
    text = (message or "Q2 sync failed").strip()
    lowered = text.lower()
    for needle in ("taxid", "tax_id", "ssn", "accountnumber", "account_number"):
        if needle in lowered.replace(" ", ""):
            return "Q2 Helix rejected the request (details omitted to protect PII)"
    return text[:500]
