"""Pydantic models for Q2 Helix account lifecycle."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AccountCreateRequest(BaseModel):
    """Create account via ``/account/create``."""

    model_config = ConfigDict(extra="allow")

    customerId: int
    productId: int
    name: str = Field(..., min_length=1, max_length=128)
    tag: str = Field(..., max_length=50)


class AccountUpdateLimitRequest(BaseModel):
    """Limit configuration for ``/account/updateLimit``."""

    model_config = ConfigDict(extra="allow")

    limitType: str | None = None
    amount: float | None = None
    velocity: str | None = None


class StopPayRequest(BaseModel):
    """Create stop payment via ``/stopPay/create``."""

    model_config = ConfigDict(extra="allow")

    checkNumber: str | None = None
    amount: float | None = None
    amountFrom: float | None = None
    amountTo: float | None = None
    payee: str | None = None


class Q2Account(BaseModel):
    """Helix account object with balance and status fields."""

    model_config = ConfigDict(extra="allow")

    accountId: int | None = None
    customerId: int | None = None
    productId: int | None = None
    accountBalance: float | None = None
    availableBalance: float | None = None
    pendingBalance: float | None = None
    status: str | None = None
    type: str | None = None
    tag: str | None = None
    routingNumber: str | None = None
    accountNumber: str | None = None
    isLocked: bool | None = None
    name: str | None = None
    raw: dict[str, Any] | None = None
