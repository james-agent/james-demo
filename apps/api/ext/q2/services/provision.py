"""Idempotent local-base → Helix customer+account provisioning."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from crm_api.customers.mock_data import MOCK_CUSTOMERS
from ext.q2.client import HelixClient
from ext.q2.config import Q2Config, load_q2_config
from ext.q2.errors import Q2ConflictError, Q2Error, Q2NotFoundError
from ext.q2.models.account import Q2Account
from ext.q2.models.customer import Q2Customer
from ext.q2.models.provision_run import Q2ProvisionRun
from ext.q2.repositories.accounts import AccountRepository
from ext.q2.repositories.customers import CustomerRepository
from ext.q2.repositories.provision_runs import ProvisionRunRepository
from ext.q2.services.account import AccountService
from ext.q2.services.customer import CustomerService


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _split_name(full_name: str) -> tuple[str, str]:
    parts = [p for p in (full_name or "").strip().split() if p]
    if not parts:
        return "Unknown", "Customer"
    if len(parts) == 1:
        return parts[0], "Customer"
    return parts[0], " ".join(parts[1:])


def _extract_data(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data")
    return data if isinstance(data, dict) else {}


class ProvisionService:
    def __init__(self, session: Session, client: HelixClient | None = None, config: Q2Config | None = None) -> None:
        self.session = session
        self.config = config or load_q2_config()
        self.client = client or HelixClient(self.config)
        self.customers = CustomerRepository(session)
        self.accounts = AccountRepository(session)
        self.runs = ProvisionRunRepository(session)
        self.customer_api = CustomerService(self.client)
        self.account_api = AccountService(self.client)

    def sync_local_base_from_crm_mocks(self) -> int:
        """Seed/refresh q2_customers from the CRM mock customer base."""
        count = 0
        for customer in MOCK_CUSTOMERS:
            self.customers.upsert_local(
                local_customer_key=customer.id,
                full_name=customer.name,
                email=customer.email,
                phone=customer.phone,
            )
            count += 1
        self.session.flush()
        return count

    def _build_onboard_payload(self, row: Q2Customer) -> dict[str, Any]:
        first_name, last_name = _split_name(row.full_name)
        if not self.config.allow_placeholder_pii and not self.config.mock_mode:
            raise Q2Error(
                f"Customer {row.local_customer_key} is missing Helix KYC fields "
                "(taxId/birthDate/address). Enrich the row or set Q2_ALLOW_PLACEHOLDER_PII=true.",
                code="VALIDATION_ERROR",
            )
        # Deterministic sandbox placeholders derived from local key (never real PII).
        digits = "".join(ch for ch in row.local_customer_key if ch.isdigit()) or "123456789"
        tax_id = (digits * 3)[:9]
        phone_digits = "".join(ch for ch in (row.phone or "") if ch.isdigit()) or "4155550100"
        return {
            "firstName": first_name[:64],
            "lastName": last_name[:128],
            "birthDate": "1990-01-01T00:00:00.000+00:00",
            "taxId": tax_id,
            "taxIdType": "SSN",
            "emailAddress": row.email or f"{row.local_customer_key}@example.invalid",
            "culture": "en-US",
            "gender": "U",
            "residencyStatusType": "USCitizen",
            "isDocumentsAccepted": True,
            "tag": row.local_customer_key[:50],
            "addresses": [
                {
                    "addressLine1": "1 Market St",
                    "city": "San Francisco",
                    "state": "CA",
                    "postalCode": "94105",
                    "countryCode": "USA",
                    "addressType": "Home",
                }
            ],
            "phones": [{"phoneNumber": phone_digits[:16], "phoneType": "Mobile"}],
        }

    def _resolve_or_create_customer(self, row: Q2Customer) -> tuple[Q2Customer, bool]:
        """Return (row, skipped)."""
        if row.q2_customer_id:
            return row, True

        tag = row.local_customer_key
        try:
            existing = self.customer_api.get_by_tag(tag)
            data = _extract_data(existing)
            customer_id = data.get("customerId")
            if customer_id is not None:
                row.q2_customer_id = str(customer_id)
                row.status = str(data.get("status") or "Active")
                row.kyc_status = str(data.get("kycStatus") or row.kyc_status)
                row.last_error = None
                self.customers.save(row)
                return row, True
        except Q2NotFoundError:
            pass

        try:
            created = self.customer_api.onboard(self._build_onboard_payload(row))
        except Q2ConflictError:
            existing = self.customer_api.get_by_tag(tag)
            created = existing

        data = _extract_data(created)
        customer_id = data.get("customerId")
        if customer_id is None:
            raise Q2Error("Helix customer onboard did not return customerId", code="API_BUSINESS_ERROR")
        row.q2_customer_id = str(customer_id)
        row.status = str(data.get("status") or "Active")
        row.kyc_status = str(data.get("kycStatus") or "Verified")
        row.last_error = None
        self.customers.save(row)
        return row, False

    def _resolve_or_create_account(self, row: Q2Customer) -> tuple[Q2Account, bool]:
        if not row.q2_customer_id:
            raise Q2Error("Cannot create account without q2_customer_id", code="VALIDATION_ERROR")

        account_tag = f"acct-{row.local_customer_key}"[:128]
        existing_row = self.accounts.get_by_tag(account_tag)
        if existing_row and existing_row.q2_account_id:
            return existing_row, True

        try:
            remote = self.account_api.get_by_tag(account_tag)
            data = _extract_data(remote)
            account_id = data.get("accountId")
            if account_id is not None:
                account = existing_row or Q2Account(
                    q2_customer_row_id=row.id,
                    q2_customer_id=row.q2_customer_id,
                    product_id=str(data.get("productId") or self.config.product_id),
                    account_tag=account_tag,
                )
                account.q2_account_id = str(account_id)
                account.q2_customer_id = row.q2_customer_id
                account.status = str(data.get("status") or "Open")
                account.last_error = None
                self.accounts.save(account)
                return account, True
        except Q2NotFoundError:
            pass

        payload = {
            "customerId": int(row.q2_customer_id) if str(row.q2_customer_id).isdigit() else row.q2_customer_id,
            "productId": int(self.config.product_id) if str(self.config.product_id).isdigit() else self.config.product_id,
            "name": f"{row.full_name} Checking"[:64],
            "tag": account_tag,
        }
        try:
            created = self.account_api.create(payload)
        except Q2ConflictError:
            created = self.account_api.get_by_tag(account_tag)

        data = _extract_data(created)
        account_id = data.get("accountId")
        if account_id is None:
            raise Q2Error("Helix account create did not return accountId", code="API_BUSINESS_ERROR")

        account = existing_row or Q2Account(
            q2_customer_row_id=row.id,
            q2_customer_id=row.q2_customer_id,
            product_id=str(payload["productId"]),
            account_tag=account_tag,
        )
        account.q2_account_id = str(account_id)
        account.q2_customer_id = row.q2_customer_id
        account.product_id = str(payload["productId"])
        account.status = str(data.get("status") or "Open")
        account.last_error = None
        self.accounts.save(account)
        return account, False

    def provision_customer(self, row: Q2Customer) -> str:
        """Provision one customer. Returns outcome: succeeded|skipped|failed."""
        try:
            _, customer_skipped = self._resolve_or_create_customer(row)
            _, account_skipped = self._resolve_or_create_account(row)
            if customer_skipped and account_skipped:
                return "skipped"
            return "succeeded"
        except Q2Error as exc:
            row.last_error = exc.message
            row.status = "failed"
            self.customers.save(row)
            return "failed"
        except Exception as exc:  # noqa: BLE001 — capture unexpected Helix/SDK failures per row
            row.last_error = str(exc)[:500]
            row.status = "failed"
            self.customers.save(row)
            return "failed"

    def run_provision(self, *, local_customer_keys: list[str] | None = None, sync_from_crm: bool = True) -> Q2ProvisionRun:
        if sync_from_crm:
            self.sync_local_base_from_crm_mocks()

        run = Q2ProvisionRun(status="running", started_at=_utcnow())
        self.runs.create(run)

        rows = self.customers.list_all()
        if local_customer_keys:
            wanted = set(local_customer_keys)
            rows = [r for r in rows if r.local_customer_key in wanted]

        run.total_customers = len(rows)
        errors: list[str] = []

        for row in rows:
            outcome = self.provision_customer(row)
            if outcome == "succeeded":
                run.succeeded_count += 1
            elif outcome == "skipped":
                run.skipped_count += 1
            else:
                run.failed_count += 1
                if row.last_error:
                    errors.append(f"{row.local_customer_key}: {row.last_error}")

        if run.failed_count and run.succeeded_count == 0 and run.skipped_count == 0:
            run.status = "failed"
        elif run.failed_count:
            run.status = "partial"
        else:
            run.status = "succeeded"

        run.error_summary = "\n".join(errors[:50]) if errors else None
        run.finished_at = _utcnow()
        self.runs.save(run)
        self.session.flush()
        return run
