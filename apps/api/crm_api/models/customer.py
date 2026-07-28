"""Local customer ORM model with durable Q2 Helix linkage."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    Index,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from crm_api.db import Base

SYNC_STATUSES = (
    "pending",
    "customer_linked",
    "account_linked",
    "skipped_incomplete",
    "failed",
)


class Customer(Base):
    """Local customer master — source of truth for Helix provisioning."""

    __tablename__ = "customers"
    __table_args__ = (
        CheckConstraint(
            "q2_sync_status IN ('pending','customer_linked','account_linked',"
            "'skipped_incomplete','failed')",
            name="ck_customers_q2_sync_status",
        ),
        Index("uq_customers_email", "email", unique=True),
        Index(
            "uq_customers_q2_customer_tag",
            "q2_customer_tag",
            unique=True,
            sqlite_where=text("q2_customer_tag IS NOT NULL"),
            postgresql_where=text("q2_customer_tag IS NOT NULL"),
        ),
        Index(
            "uq_customers_q2_customer_id",
            "q2_customer_id",
            unique=True,
            sqlite_where=text("q2_customer_id IS NOT NULL"),
            postgresql_where=text("q2_customer_id IS NOT NULL"),
        ),
        Index("idx_customers_q2_sync_status", "q2_sync_status"),
        {"sqlite_autoincrement": False},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    external_ref: Mapped[str | None] = mapped_column(String(64), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(64), nullable=False)
    last_name: Mapped[str] = mapped_column(String(128), nullable=False)
    middle_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    tax_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    tax_id_type: Mapped[str | None] = mapped_column(String(16), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(16), nullable=True)
    address_line1: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(64), nullable=True)
    state: Mapped[str | None] = mapped_column(String(2), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(3), nullable=True, default="USA")

    q2_customer_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    q2_account_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    q2_customer_tag: Mapped[str | None] = mapped_column(String(50), nullable=True)
    q2_account_tag: Mapped[str | None] = mapped_column(String(50), nullable=True)
    q2_sync_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    q2_last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    q2_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def customer_tag(self) -> str:
        return str(self.id)

    def account_tag(self) -> str:
        return f"{self.id}:primary"

    def is_kyc_complete(self) -> bool:
        """Helix onboard requires identity + tax + mailing address fields."""
        required = [
            self.first_name,
            self.last_name,
            self.email,
            self.birth_date,
            self.tax_id,
            self.tax_id_type,
            self.address_line1,
            self.city,
            self.state,
            self.postal_code,
        ]
        return all(value not in (None, "") for value in required)
