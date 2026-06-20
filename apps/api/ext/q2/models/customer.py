"""Pydantic models for Q2 customer API."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CustomerOnboardRequest(BaseModel):
    customer_id: UUID


class Q2CustomerResponse(BaseModel):
    customer_id: str | None = None
    tag: str | None = None
    kyc_status: str | None = None
    status: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class SyncStatusResponse(BaseModel):
    pending: int
    synced: int
    failed: int
    skipped: int
    total: int


class SyncTriggerResponse(BaseModel):
    mode: str
    processed: int
    synced: int
    failed: int
    skipped: int


class Q2CustomerSyncRecord(BaseModel):
    customer_id: UUID
    tag: str
    q2_customer_id: str | None
    kyc_status: str | None
    sync_status: str
    last_error: str | None
    last_synced_at: datetime | None

    model_config = {"from_attributes": True}
