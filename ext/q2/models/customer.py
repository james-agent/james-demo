"""Pydantic models for Q2 Helix customer lifecycle."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


TaxIdType = Literal["SSN", "EIN", "ITIN"]
Gender = Literal["M", "F", "U"]
ResidencyStatusType = Literal["USCitizen", "ResidentAlien", "NonResidentAlien"]
AddressType = Literal["Mailing", "Home", "Work"]
PhoneType = Literal["Mobile", "Home", "Work"]


class CustomerAddress(BaseModel):
    model_config = ConfigDict(extra="allow")

    addressLine1: str = Field(..., max_length=100)
    city: str = Field(..., max_length=64)
    state: str = Field(..., max_length=2)
    postalCode: str = Field(..., max_length=10)
    countryCode: str = Field(default="USA", max_length=3)
    addressType: AddressType = "Home"
    addressLine2: str | None = Field(default=None, max_length=100)


class CustomerPhone(BaseModel):
    model_config = ConfigDict(extra="allow")

    phoneNumber: str = Field(..., max_length=16)
    phoneType: PhoneType = "Mobile"


class CustomerOnboardRequest(BaseModel):
    """Create and verify a customer via ``/customer/onboard``."""

    model_config = ConfigDict(extra="allow")

    firstName: str = Field(..., max_length=64)
    lastName: str = Field(..., max_length=128)
    tag: str = Field(..., max_length=50)
    birthDate: str | None = None
    taxId: str | None = None
    taxIdType: TaxIdType | None = None
    emailAddress: str | None = None
    middleName: str | None = Field(default=None, max_length=64)
    culture: str = "en-US"
    gender: Gender | None = None
    residencyStatusType: ResidencyStatusType | None = None
    isDocumentsAccepted: bool = True
    isBusiness: bool = False
    addresses: list[CustomerAddress] = Field(default_factory=list)
    phones: list[CustomerPhone] = Field(default_factory=list)


class CustomerUpdateRequest(BaseModel):
    """Updatable customer profile fields."""

    model_config = ConfigDict(extra="allow")

    firstName: str | None = Field(default=None, max_length=64)
    lastName: str | None = Field(default=None, max_length=128)
    middleName: str | None = Field(default=None, max_length=64)
    emailAddress: str | None = None
    culture: str | None = None
    gender: Gender | None = None
    addresses: list[CustomerAddress] | None = None
    phones: list[CustomerPhone] | None = None


class CustomerBeneficiary(BaseModel):
    model_config = ConfigDict(extra="allow")

    firstName: str = Field(..., max_length=64)
    lastName: str = Field(..., max_length=128)
    birthDate: str | None = None
    taxId: str | None = None
    relationshipType: str | None = None
    percentage: float | None = None


class CustomerLockRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=256)


class Q2Customer(BaseModel):
    """Helix customer object with common lifecycle properties."""

    model_config = ConfigDict(extra="allow")

    customerId: int | None = None
    tag: str | None = None
    status: str | None = None
    kycStatus: str | None = None
    fraudStatus: str | None = None
    ofacStatus: str | None = None
    isBusiness: bool | None = None
    isLocked: bool | None = None
    firstName: str | None = None
    lastName: str | None = None
    middleName: str | None = None
    emailAddress: str | None = None
    taxIdMasked: str | None = None
    raw: dict[str, Any] | None = None
