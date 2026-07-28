"""Pydantic schemas for Q2 operator APIs."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    ok: bool
    environment: str
    configured: bool
    mock_mode: bool
    missing_keys: list[str] = Field(default_factory=list)
    connectivity: dict[str, Any] | None = None
    error: str | None = None
    code: str | None = None


class ProvisionRequest(BaseModel):
    local_customer_keys: list[str] | None = None
    sync_from_crm: bool = True


class ProvisionRunResponse(BaseModel):
    id: str
    status: str
    total_customers: int
    succeeded_count: int
    failed_count: int
    skipped_count: int
    error_summary: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime


class CustomerOnboardRequest(BaseModel):
    firstName: str
    lastName: str
    emailAddress: str | None = None
    tag: str
    birthDate: str | None = None
    taxId: str | None = None
    taxIdType: str | None = "SSN"
    extra: dict[str, Any] = Field(default_factory=dict)


class AccountCreateRequest(BaseModel):
    customerId: str | int
    productId: str | int
    name: str
    tag: str
