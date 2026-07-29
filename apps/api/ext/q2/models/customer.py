"""Local customer base + Helix customer mapping."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ext.q2.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


class Q2Customer(Base):
    __tablename__ = "q2_customers"
    __table_args__ = (
        # Unique when set; NULL mappings remain allowed (partial unique index).
        Index(
            "uq_q2_customers_q2_customer_id",
            "q2_customer_id",
            unique=True,
            sqlite_where=text("q2_customer_id IS NOT NULL"),
            postgresql_where=text("q2_customer_id IS NOT NULL"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    local_customer_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    q2_customer_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="pending")
    kyc_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )

    accounts = relationship("Q2Account", back_populates="customer", cascade="all, delete-orphan")
