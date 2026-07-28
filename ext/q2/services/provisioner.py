"""Idempotent orchestration: local customers → Helix customer + Open account."""

from __future__ import annotations

import logging
import os
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ext.q2.client import HelixAPIError, HelixClient, get_helix_client
from ext.q2.models.account import AccountCreateRequest
from ext.q2.models.customer import CustomerOnboardRequest, CustomerPhone
from ext.q2.models.local_customer import LocalCustomer
from ext.q2.repository.customers import LocalCustomerRepository
from ext.q2.services._helpers import mask_pii, safe_log_payload
from ext.q2.services._provision_helpers import (
    account_tag_for,
    extract_accounts,
    extract_customer_id,
    find_open_account,
    split_name,
)
from ext.q2.services.account import AccountService
from ext.q2.services.customer import CustomerService

logger = logging.getLogger(__name__)


class ProvisionOutcome(str, Enum):
    CREATED = "created"
    EXISTING = "existing"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class CustomerProvisionResult:
    local_id: str
    tag: str
    outcome: ProvisionOutcome
    q2_customer_id: str | None = None
    q2_account_id: str | None = None
    detail: str | None = None


@dataclass
class BulkProvisionResult:
    processed: int = 0
    succeeded: int = 0
    failed: int = 0
    results: list[CustomerProvisionResult] = field(default_factory=list)


def _default_product_id() -> str:
    value = os.environ.get("Q2_HELIX_DEFAULT_PRODUCT_ID", "").strip()
    if not value:
        raise ValueError(
            "Q2_HELIX_DEFAULT_PRODUCT_ID is required to create Helix accounts. "
            "Set it in .env (see .env.example)."
        )
    return value


def _account_name_template() -> str:
    return (
        os.environ.get("Q2_HELIX_ACCOUNT_NAME_TEMPLATE", "{full_name} Account").strip()
        or "{full_name} Account"
    )


class CustomerAccountProvisioner:
    """Per-customer pipeline: resolve/create Helix customer → list/create account → persist."""

    def __init__(
        self,
        repo: LocalCustomerRepository,
        *,
        customer_service: CustomerService | None = None,
        account_service: AccountService | None = None,
        client: HelixClient | None = None,
        product_id: str | None = None,
    ) -> None:
        self.repo = repo
        owns = client is None and customer_service is None and account_service is None
        self._client = client or (None if (customer_service or account_service) else get_helix_client())
        self.customers = customer_service or CustomerService(self._client)
        self.accounts = account_service or AccountService(self._client)
        self._owns_client = owns
        self.product_id = product_id

    def close(self) -> None:
        if self._owns_client and self._client is not None:
            self._client.close()

    def __enter__(self) -> CustomerAccountProvisioner:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def sync_all(self) -> BulkProvisionResult:
        self.repo.ensure_seed_customers()
        bulk = BulkProvisionResult()
        for customer in self.repo.list_active():
            result = self._sync_one(customer)
            bulk.results.append(result)
            bulk.processed += 1
            if result.outcome == ProvisionOutcome.FAILED:
                bulk.failed += 1
            else:
                bulk.succeeded += 1
        self.repo.session.flush()
        return bulk

    def sync_one(self, local_id: uuid.UUID) -> CustomerProvisionResult:
        self.repo.ensure_seed_customers()
        customer = self.repo.get_by_id(local_id)
        if customer is None:
            return CustomerProvisionResult(
                local_id=str(local_id),
                tag="",
                outcome=ProvisionOutcome.FAILED,
                detail="Local customer not found",
            )
        result = self._sync_one(customer)
        self.repo.session.flush()
        return result

    def _sync_one(self, customer: LocalCustomer) -> CustomerProvisionResult:
        safe_log_payload(
            "provision_start",
            {"local_id": str(customer.id), "tag": customer.tag, "full_name": customer.full_name},
        )
        try:
            product_id = self.product_id if self.product_id is not None else _default_product_id()
            q2_customer_id, customer_outcome = self._resolve_or_create_customer(customer)
            self.repo.mark_customer_created(customer, q2_customer_id)
            q2_account_id, account_outcome = self._resolve_or_create_account(
                customer,
                q2_customer_id=q2_customer_id,
                product_id=product_id,
            )
            outcome = (
                ProvisionOutcome.EXISTING
                if customer_outcome == ProvisionOutcome.EXISTING
                and account_outcome == ProvisionOutcome.EXISTING
                else ProvisionOutcome.CREATED
            )
            return CustomerProvisionResult(
                local_id=str(customer.id),
                tag=customer.tag,
                outcome=outcome,
                q2_customer_id=q2_customer_id,
                q2_account_id=q2_account_id,
                detail=f"customer={customer_outcome.value};account={account_outcome.value}",
            )
        except Exception as exc:  # noqa: BLE001 — bulk must isolate row failures
            message = str(exc)
            logger.warning(
                "provision_failed local_id=%s tag=%s error=%s",
                customer.id,
                customer.tag,
                message,
            )
            self.repo.mark_failed(customer, message)
            return CustomerProvisionResult(
                local_id=str(customer.id),
                tag=customer.tag,
                outcome=ProvisionOutcome.FAILED,
                q2_customer_id=customer.q2_customer_id,
                detail=message,
            )

    def _resolve_or_create_customer(self, customer: LocalCustomer) -> tuple[str, ProvisionOutcome]:
        if customer.q2_customer_id:
            return str(customer.q2_customer_id), ProvisionOutcome.EXISTING

        existing = self._try_get_by_tag(customer.tag)
        if existing is not None:
            cid = extract_customer_id(existing)
            if cid:
                return cid, ProvisionOutcome.EXISTING

        try:
            created = self.customers.onboard(self._build_onboard_request(customer))
        except HelixAPIError as exc:
            if exc.status_code == 409:
                existing = self._try_get_by_tag(customer.tag)
                if existing is not None:
                    cid = extract_customer_id(existing)
                    if cid:
                        return cid, ProvisionOutcome.EXISTING
            raise

        cid = extract_customer_id(created)
        if not cid:
            raise RuntimeError("Helix customer/onboard returned no customerId")
        return cid, ProvisionOutcome.CREATED

    def _try_get_by_tag(self, tag: str) -> dict[str, Any] | None:
        try:
            payload = self.customers.get_by_tag(tag)
            return payload if isinstance(payload, dict) else None
        except HelixAPIError as exc:
            if exc.status_code == 404:
                return None
            if exc.status_code == 400 and "not found" in str(exc).lower():
                return None
            raise

    def _build_onboard_request(self, customer: LocalCustomer) -> CustomerOnboardRequest:
        first, last = split_name(customer.full_name)
        phones: list[CustomerPhone] = []
        if customer.phone:
            phones.append(CustomerPhone(phoneNumber=customer.phone, phoneType="Mobile"))
        return CustomerOnboardRequest(
            firstName=first,
            lastName=last,
            tag=customer.tag,
            birthDate=customer.date_of_birth.isoformat() if customer.date_of_birth else None,
            emailAddress=customer.email,
            phones=phones,
            isDocumentsAccepted=True,
        )

    def _resolve_or_create_account(
        self,
        customer: LocalCustomer,
        *,
        q2_customer_id: str,
        product_id: str,
    ) -> tuple[str, ProvisionOutcome]:
        listed = self.accounts.list_by_customer(int(q2_customer_id))
        accounts = extract_accounts(listed)
        existing = find_open_account(accounts, product_id or None)
        account_tag = account_tag_for(customer)
        account_name = _account_name_template().format(
            full_name=customer.full_name,
            tag=customer.tag,
        )

        if existing is not None:
            account_id = str(existing.get("accountId") or existing.get("account_id") or "")
            if not account_id:
                raise RuntimeError("Helix account/list entry missing accountId")
            status = str(existing.get("status") or "Open")
            matched_product = str(
                existing.get("productId") or existing.get("product_id") or product_id
            )
            tag = str(existing.get("tag") or account_tag)[:50]
            name = str(existing.get("name") or account_name)[:255]
            self.repo.mark_account_created(
                customer,
                q2_account_id=account_id,
                product_id=matched_product,
                account_tag=tag,
                account_name=name,
                status=status,
            )
            return account_id, ProvisionOutcome.EXISTING

        local_mapped = next(
            (row for row in customer.q2_accounts if row.account_tag == account_tag),
            None,
        )
        if local_mapped is not None:
            return local_mapped.q2_account_id, ProvisionOutcome.EXISTING

        try:
            product_int = int(product_id)
        except ValueError as exc:
            raise ValueError(
                f"Q2_HELIX_DEFAULT_PRODUCT_ID must be an integer, got {product_id!r}"
            ) from exc

        created = self.accounts.create(
            AccountCreateRequest(
                customerId=int(q2_customer_id),
                productId=product_int,
                name=account_name[:128],
                tag=account_tag,
            )
        )
        safe_log_payload(
            "provision_account_created",
            mask_pii(created if isinstance(created, dict) else {}),
        )
        account_id = str(
            (created or {}).get("accountId") or (created or {}).get("account_id") or ""
        )
        if not account_id:
            raise RuntimeError("Helix account/create returned no accountId")
        status = str((created or {}).get("status") or "Open")
        self.repo.mark_account_created(
            customer,
            q2_account_id=account_id,
            product_id=str(product_id),
            account_tag=account_tag,
            account_name=account_name[:255],
            status=status,
        )
        return account_id, ProvisionOutcome.CREATED
