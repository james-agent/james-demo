"""Q2 Helix account models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AccountCreateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    customerId: int
    productId: int
    name: str
    tag: str


class AccountUpdateLimitRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    limitType: str | None = None
    amount: float | None = None
    raw: dict[str, Any] = Field(default_factory=dict)

    def to_helix_payload(self, account_id: int) -> dict[str, Any]:
        payload = {"accountId": account_id}
        if self.limitType is not None:
            payload["limitType"] = self.limitType
        if self.amount is not None:
            payload["amount"] = self.amount
        payload.update(self.raw)
        return payload


class StopPayRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    checkNumber: str | None = None
    amount: float | None = None
    payee: str | None = None
    amountMin: float | None = None
    amountMax: float | None = None


class Q2Account(BaseModel):
    model_config = ConfigDict(extra="ignore")

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
    raw: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_helix(cls, data: Any) -> Q2Account:
        payload = data if isinstance(data, dict) else {}
        return cls(
            accountId=_as_int(payload.get("accountId")),
            customerId=_as_int(payload.get("customerId")),
            productId=_as_int(payload.get("productId")),
            accountBalance=_as_float(payload.get("accountBalance")),
            availableBalance=_as_float(payload.get("availableBalance")),
            pendingBalance=_as_float(payload.get("pendingBalance")),
            status=payload.get("status"),
            type=payload.get("type"),
            tag=payload.get("tag"),
            routingNumber=payload.get("routingNumber"),
            accountNumber=_mask_account_number(payload.get("accountNumber")),
            isLocked=payload.get("isLocked"),
            name=payload.get("name"),
            raw=_sanitize_account_payload(payload),
        )


def _as_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _mask_account_number(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    if text.startswith("*"):
        return text
    if len(text) <= 4:
        return "****"
    return f"****{text[-4:]}"


def _sanitize_account_payload(payload: dict[str, Any]) -> dict[str, Any]:
    sanitized = dict(payload)
    if "accountNumber" in sanitized:
        sanitized["accountNumber"] = _mask_account_number(sanitized.get("accountNumber"))
    return sanitized
