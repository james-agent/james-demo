"""Repository for local customers and Helix account mappings."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ext.q2.models.local_customer import (
    CustomerStatus,
    LocalCustomer,
    LocalCustomerQ2Account,
    ProvisionStatus,
)


class LocalCustomerLoader(Protocol):
    """Strategy interface for loading local customers (DB now; replaceable later)."""

    def list_active(self) -> list[LocalCustomer]: ...

    def get_by_id(self, local_id: uuid.UUID) -> LocalCustomer | None: ...


SEED_CUSTOMERS: tuple[dict, ...] = (
    {
        "tag": "local-ada-001",
        "full_name": "Ada Lovelace",
        "email": "ada.lovelace@example.com",
        "phone": "5125550101",
        "date_of_birth": date(1815, 12, 10),
    },
    {
        "tag": "local-alan-002",
        "full_name": "Alan Turing",
        "email": "alan.turing@example.com",
        "phone": "5125550102",
        "date_of_birth": date(1912, 6, 23),
    },
    {
        "tag": "local-grace-003",
        "full_name": "Grace Hopper",
        "email": "grace.hopper@example.com",
        "phone": "5125550103",
        "date_of_birth": date(1906, 12, 9),
    },
)


class LocalCustomerRepository:
    """DB-backed local customer loader/persister."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def list_active(self) -> list[LocalCustomer]:
        stmt = (
            select(LocalCustomer)
            .where(LocalCustomer.status == CustomerStatus.ACTIVE.value)
            .options(selectinload(LocalCustomer.q2_accounts))
            .order_by(LocalCustomer.created_at.asc())
        )
        return list(self.session.scalars(stmt).all())

    def get_by_id(self, local_id: uuid.UUID) -> LocalCustomer | None:
        stmt = (
            select(LocalCustomer)
            .where(LocalCustomer.id == local_id)
            .options(selectinload(LocalCustomer.q2_accounts))
        )
        return self.session.scalars(stmt).first()

    def get_by_tag(self, tag: str) -> LocalCustomer | None:
        stmt = select(LocalCustomer).where(LocalCustomer.tag == tag)
        return self.session.scalars(stmt).first()

    def mark_customer_created(self, customer: LocalCustomer, q2_customer_id: str) -> None:
        customer.q2_customer_id = str(q2_customer_id)
        customer.provision_status = ProvisionStatus.CUSTOMER_CREATED.value
        customer.last_provision_error = None
        customer.updated_at = datetime.now(timezone.utc)
        self.session.add(customer)

    def mark_account_created(
        self,
        customer: LocalCustomer,
        *,
        q2_account_id: str,
        product_id: str,
        account_tag: str,
        account_name: str,
        status: str,
    ) -> LocalCustomerQ2Account:
        existing = next(
            (row for row in customer.q2_accounts if row.q2_account_id == str(q2_account_id)),
            None,
        )
        if existing is None:
            existing = next(
                (row for row in customer.q2_accounts if row.account_tag == account_tag),
                None,
            )
        if existing is None:
            existing = LocalCustomerQ2Account(
                id=uuid.uuid4(),
                customer_id=customer.id,
                q2_account_id=str(q2_account_id),
                product_id=str(product_id),
                account_tag=account_tag,
                account_name=account_name,
                status=status,
            )
            customer.q2_accounts.append(existing)
            self.session.add(existing)
        else:
            existing.q2_account_id = str(q2_account_id)
            existing.product_id = str(product_id)
            existing.account_tag = account_tag
            existing.account_name = account_name
            existing.status = status
            existing.updated_at = datetime.now(timezone.utc)

        customer.provision_status = ProvisionStatus.ACCOUNT_CREATED.value
        customer.last_provision_error = None
        customer.updated_at = datetime.now(timezone.utc)
        self.session.add(customer)
        return existing

    def mark_failed(self, customer: LocalCustomer, error: str) -> None:
        customer.provision_status = ProvisionStatus.FAILED.value
        customer.last_provision_error = error[:4000]
        customer.updated_at = datetime.now(timezone.utc)
        self.session.add(customer)

    def ensure_seed_customers(self) -> int:
        """Insert the minimal local base when the table is empty. Returns inserted count."""
        existing = self.session.scalar(select(LocalCustomer.id).limit(1))
        if existing is not None:
            return 0
        created = 0
        for row in SEED_CUSTOMERS:
            if self.get_by_tag(row["tag"]) is not None:
                continue
            customer = LocalCustomer(
                id=uuid.uuid4(),
                tag=row["tag"],
                full_name=row["full_name"],
                email=row.get("email"),
                phone=row.get("phone"),
                date_of_birth=row.get("date_of_birth"),
                status=CustomerStatus.ACTIVE.value,
                provision_status=ProvisionStatus.PENDING.value,
            )
            self.session.add(customer)
            created += 1
        self.session.flush()
        return created
