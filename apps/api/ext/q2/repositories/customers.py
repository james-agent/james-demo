"""Persistence helpers for q2_customers."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ext.q2.models.customer import Q2Customer


class CustomerRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_all(self) -> list[Q2Customer]:
        return list(self.session.scalars(select(Q2Customer).order_by(Q2Customer.local_customer_key)).all())

    def get_by_local_key(self, local_customer_key: str) -> Q2Customer | None:
        return self.session.scalar(
            select(Q2Customer).where(Q2Customer.local_customer_key == local_customer_key)
        )

    def get_by_id(self, customer_row_id: str) -> Q2Customer | None:
        return self.session.get(Q2Customer, customer_row_id)

    def upsert_local(
        self,
        *,
        local_customer_key: str,
        full_name: str,
        email: str | None,
        phone: str | None,
    ) -> Q2Customer:
        row = self.get_by_local_key(local_customer_key)
        if row is None:
            row = Q2Customer(
                local_customer_key=local_customer_key,
                full_name=full_name,
                email=email,
                phone=phone,
                status="pending",
            )
            self.session.add(row)
        else:
            row.full_name = full_name
            row.email = email
            row.phone = phone
        self.session.flush()
        return row

    def save(self, row: Q2Customer) -> Q2Customer:
        self.session.add(row)
        self.session.flush()
        return row
