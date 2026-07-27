"""Request models for Q2 Helix account lifecycle and stop pays."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AccountCreateRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    customerId: int = Field(ge=1)
    productId: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=50)
    tag: str | None = Field(default=None, max_length=50)
    category: str | None = None
    subcategory: str | None = None
    isclosable: bool | None = None
    requestingCustomerId: int | None = None


class AccountCloseRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    customerId: int = Field(ge=1)
    accountId: int = Field(ge=1)
    closeToAccountId: int | None = None
    transactionTag: str | None = None


class AccountLockRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    customerId: int = Field(ge=1)
    accountId: int = Field(ge=1)
    lockTypeCode: Literal["CST", "SYS"] = "CST"
    lockReasonTypeCode: str = "ADM"


class StopPayCreateRequest(BaseModel):
    """Create check or ACH stop pay (routes to Helix stopPay endpoints)."""

    model_config = ConfigDict(extra="allow")

    customerId: int = Field(ge=1)
    accountId: int = Field(ge=1)
    paymentType: Literal["Check", "ACH"] = "Check"
    checkNumberMinimum: int | None = None
    checkNumberMaximum: int | None = None
    amountMinimum: float | None = None
    amountMaximum: float | None = None
    expireDate: str | None = None
    payeeName: str | None = None
    comment: str | None = None
    stopPayType: Literal["OneTime", "Permanent"] | None = None
    companyName: str | None = None
    companyId: str | None = None


class StopPayExpireRequest(BaseModel):
    customerId: int = Field(ge=1)
    accountId: int = Field(ge=1)
    stopPayId: int = Field(ge=1)
