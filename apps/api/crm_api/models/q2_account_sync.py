"""Q2 account sync state model."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from crm_api.db import Base


class Q2AccountSync(Base):
    __tablename__ = "q2_account_sync"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    q2_customer_id: Mapped[str] = mapped_column(String(64), nullable=False)
    q2_account_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    product_id: Mapped[str] = mapped_column(String(64), nullable=False)
    account_tag: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    account_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sync_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending", index=True
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
