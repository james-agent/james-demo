"""Persistence helpers for q2_accounts."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ext.q2.models.account import Q2Account


class AccountRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_tag(self, account_tag: str) -> Q2Account | None:
        return self.session.scalar(select(Q2Account).where(Q2Account.account_tag == account_tag))

    def list_for_customer_row(self, q2_customer_row_id: str) -> list[Q2Account]:
        return list(
            self.session.scalars(
                select(Q2Account).where(Q2Account.q2_customer_row_id == q2_customer_row_id)
            ).all()
        )

    def save(self, row: Q2Account) -> Q2Account:
        self.session.add(row)
        self.session.flush()
        return row
