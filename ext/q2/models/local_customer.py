"""ORM models for the local customer base and Helix account mappings."""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from ext.q2.db import Base


class CustomerStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class ProvisionStatus(str, enum.Enum):
    PENDING = "pending"
    CUSTOMER_CREATED = "customer_created"
    ACCOUNT_CREATED = "account_created"
    FAILED = "failed"


class LocalCustomer(Base):
    """Local customer row provisioned into Q2 Helix."""

    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("tag", name="uq_customers_tag"),
        CheckConstraint(
            "provision_status IN ('pending','customer_created','account_created','failed')",
            name="ck_customers_provision_status",
        ),
        CheckConstraint(
            "status IN ('active','inactive','archived')",
            name="ck_customers_status",
        ),
        Index("idx_customers_q2_customer_id", "q2_customer_id"),
        Index("idx_customers_provision_status", "provision_status"),
        {"sqlite_autoincrement": False},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tag: Mapped[str] = mapped_column(String(50), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=CustomerStatus.ACTIVE.value)
    q2_customer_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    provision_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ProvisionStatus.PENDING.value,
    )
    last_provision_error: Mapped[str | None] = mapped_column(Text, nullable=True)
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

    q2_accounts: Mapped[list[LocalCustomerQ2Account]] = relationship(
        "LocalCustomerQ2Account",
        back_populates="customer",
        cascade="all, delete-orphan",
    )


class LocalCustomerQ2Account(Base):
    """Helix account linked to a local customer."""

    __tablename__ = "customer_q2_accounts"
    __table_args__ = (
        UniqueConstraint("account_tag", name="uq_customer_q2_accounts_account_tag"),
        UniqueConstraint("q2_account_id", name="uq_customer_q2_accounts_q2_account_id"),
        Index("idx_customer_q2_accounts_customer_id", "customer_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("customers.id", name="fk_customer_q2_accounts_customer_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    q2_account_id: Mapped[str] = mapped_column(String(64), nullable=False)
    product_id: Mapped[str] = mapped_column(String(64), nullable=False)
    account_tag: Mapped[str] = mapped_column(String(50), nullable=False)
    account_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
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

    customer: Mapped[LocalCustomer] = relationship("LocalCustomer", back_populates="q2_accounts")
