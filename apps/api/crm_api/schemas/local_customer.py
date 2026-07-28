"""Schemas for persisted local customers (Q2 sync source of truth)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LocalCustomerCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    email: str = Field(min_length=3, max_length=255)
    first_name: str = Field(min_length=1, max_length=64)
    last_name: str = Field(min_length=1, max_length=128)
    middle_name: str | None = Field(default=None, max_length=64)
    external_ref: str | None = Field(default=None, max_length=64)
    birth_date: date | None = None
    tax_id: str | None = Field(default=None, max_length=32)
    tax_id_type: Literal["SSN", "EIN", "ITIN"] | None = None
    phone_number: str | None = Field(default=None, max_length=16)
    address_line1: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=64)
    state: str | None = Field(default=None, min_length=2, max_length=2)
    postal_code: str | None = Field(default=None, max_length=10)
    country_code: str | None = Field(default="USA", min_length=3, max_length=3)


class LocalCustomerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    external_ref: str | None = None
    email: str
    first_name: str
    last_name: str
    middle_name: str | None = None
    birth_date: date | None = None
    tax_id_type: str | None = None
    phone_number: str | None = None
    address_line1: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country_code: str | None = None
    q2_customer_id: int | None = None
    q2_account_id: int | None = None
    q2_customer_tag: str | None = None
    q2_account_tag: str | None = None
    q2_sync_status: str
    q2_last_error: str | None = None
    q2_synced_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    # Never expose raw tax_id in API responses
    has_tax_id: bool = False


def to_read_model(customer: object) -> LocalCustomerRead:
    data = LocalCustomerRead.model_validate(customer)
    tax_id = getattr(customer, "tax_id", None)
    return data.model_copy(update={"has_tax_id": bool(tax_id)})
