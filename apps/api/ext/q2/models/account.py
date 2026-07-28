"""Helix account mapping per local customer."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ext.q2.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


class Q2Account(Base):
    __tablename__ = "q2_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    q2_customer_row_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("q2_customers.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    q2_customer_id: Mapped[str] = mapped_column(String(64), nullable=False)
    q2_account_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    product_id: Mapped[str] = mapped_column(String(64), nullable=False)
    account_tag: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="pending")
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )

    customer = relationship("Q2Customer", back_populates="accounts")
