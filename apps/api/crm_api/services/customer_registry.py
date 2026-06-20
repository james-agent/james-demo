"""Local customer registry backed by PostgreSQL."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from crm_api.customers.mock_data import MOCK_CUSTOMERS
from crm_api.models.customer import Customer


def _split_name(full_name: str) -> tuple[str, str]:
    parts = full_name.strip().split(None, 1)
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]


def import_mock_customers(session: Session) -> int:
    """Seed local customers table from CRM mock data if empty."""
    existing = session.scalar(select(Customer.id).limit(1))
    if existing is not None:
        return 0

    created = 0
    for mock in MOCK_CUSTOMERS:
        first_name, last_name = _split_name(mock.name)
        customer = Customer(
            external_ref=mock.id,
            first_name=first_name,
            last_name=last_name or first_name,
            email=mock.email,
            phone=mock.phone,
            address_state=mock.state if mock.state != "—" else None,
            is_active=mock.status != "Inactive",
        )
        session.add(customer)
        created += 1
    session.commit()
    return created


def list_active_customers(session: Session) -> list[Customer]:
    stmt = select(Customer).where(Customer.is_active.is_(True)).order_by(Customer.created_at)
    return list(session.scalars(stmt).all())


def get_customer_by_id(session: Session, customer_id: uuid.UUID) -> Customer | None:
    return session.get(Customer, customer_id)


def get_customer_by_external_ref(session: Session, external_ref: str) -> Customer | None:
    stmt = select(Customer).where(Customer.external_ref == external_ref)
    return session.scalar(stmt)
