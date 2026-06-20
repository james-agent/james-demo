"""Pydantic models for Q2 account API."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AccountCreateRequest(BaseModel):
    customer_id: UUID
    product_id: str | None = None
    name: str | None = None
    tag: str | None = None


class AccountUpdateLimitRequest(BaseModel):
    account_id: str
    limit_amount: float | None = None
    limit_type: str | None = None


class StopPayRequest(BaseModel):
    check_number: str | None = None
    amount: float | None = None
    payee: str | None = None


class Q2Account(BaseModel):
    account_id: str | None = None
    customer_id: str | None = None
    product_id: str | None = None
    account_balance: float | None = None
    available_balance: float | None = None
    pending_balance: float | None = None
    status: str | None = None
    type: str | None = None
    tag: str | None = None
    routing_number: str | None = None
    account_number: str | None = None
    is_locked: bool | None = None
    name: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class Q2AccountListResponse(BaseModel):
    accounts: list[Q2Account] = Field(default_factory=list)


class AccountSyncStatusResponse(BaseModel):
    eligible: int
    provisioned: int
    failed: int
    skipped: int
    total: int


class AccountSyncTriggerResponse(BaseModel):
    processed: int
    provisioned: int
    failed: int
    skipped: int


class Q2AccountSyncRecord(BaseModel):
    customer_id: UUID
    q2_customer_id: str
    q2_account_id: str | None
    product_id: str
    account_tag: str
    account_name: str | None
    sync_status: str
    last_error: str | None
    last_synced_at: datetime | None

    model_config = {"from_attributes": True}
