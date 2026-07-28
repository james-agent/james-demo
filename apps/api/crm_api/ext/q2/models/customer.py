"""Q2 Helix customer models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class Q2Address(BaseModel):
    model_config = ConfigDict(extra="ignore")

    addressLine1: str
    city: str
    state: str = Field(min_length=2, max_length=2)
    postalCode: str
    countryCode: str = Field(default="USA", min_length=3, max_length=3)
    addressType: Literal["Mailing", "Home", "Work"] = "Home"
    addressLine2: str | None = None


class Q2Phone(BaseModel):
    model_config = ConfigDict(extra="ignore")

    phoneNumber: str
    phoneType: Literal["Mobile", "Home", "Work"] = "Mobile"


class CustomerOnboardRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    firstName: str
    lastName: str
    birthDate: str
    taxId: str
    emailAddress: str
    tag: str
    taxIdType: Literal["SSN", "EIN", "ITIN"] = "SSN"
    middleName: str | None = None
    culture: str = "en-US"
    gender: Literal["M", "F", "U"] | None = None
    residencyStatusType: Literal["USCitizen", "ResidentAlien", "NonResidentAlien"] | None = None
    isDocumentsAccepted: bool = True
    isBusiness: bool = False
    addresses: list[Q2Address] = Field(default_factory=list)
    phones: list[Q2Phone] = Field(default_factory=list)


class CustomerUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    firstName: str | None = None
    lastName: str | None = None
    middleName: str | None = None
    emailAddress: str | None = None
    culture: str | None = None
    addresses: list[Q2Address] | None = None
    phones: list[Q2Phone] | None = None


class CustomerLockRequest(BaseModel):
    reason: str = "fraud_review"


class CustomerBeneficiary(BaseModel):
    model_config = ConfigDict(extra="ignore")

    firstName: str
    lastName: str
    relationship: str | None = None
    percentage: float | None = None
    dateOfBirth: str | None = None
    taxId: str | None = None


class Q2Customer(BaseModel):
    model_config = ConfigDict(extra="ignore")

    customerId: int | None = None
    tag: str | None = None
    status: str | None = None
    kycStatus: str | None = None
    fraudStatus: str | None = None
    ofacStatus: str | None = None
    isBusiness: bool | None = None
    isLocked: bool | None = None
    taxIdMasked: str | None = None
    firstName: str | None = None
    lastName: str | None = None
    emailAddress: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_helix(cls, data: Any) -> Q2Customer:
        payload = data if isinstance(data, dict) else {}
        return cls(
            customerId=_as_int(payload.get("customerId")),
            tag=payload.get("tag"),
            status=payload.get("status"),
            kycStatus=payload.get("kycStatus"),
            fraudStatus=payload.get("fraudStatus"),
            ofacStatus=payload.get("ofacStatus"),
            isBusiness=payload.get("isBusiness"),
            isLocked=payload.get("isLocked"),
            taxIdMasked=payload.get("taxIdMasked") or _mask_tax_id(payload.get("taxId")),
            firstName=payload.get("firstName"),
            lastName=payload.get("lastName"),
            emailAddress=payload.get("emailAddress"),
            raw=_sanitize_customer_payload(payload),
        )


def _as_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _mask_tax_id(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    if len(text) < 4:
        return "****"
    return f"***-**-{text[-4:]}"


def _sanitize_customer_payload(payload: dict[str, Any]) -> dict[str, Any]:
    sanitized = dict(payload)
    if "taxId" in sanitized:
        sanitized["taxId"] = _mask_tax_id(sanitized.get("taxId"))
    return sanitized
