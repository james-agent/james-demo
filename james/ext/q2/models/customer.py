"""Request/response models for Q2 Helix customer lifecycle."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CustomerAddress(BaseModel):
    model_config = ConfigDict(extra="allow")

    addressLine1: str
    addressType: str = "Residence"
    city: str
    state: str
    postalCode: str
    country: str = "US"
    addressLine2: str | None = None


class CustomerPhone(BaseModel):
    model_config = ConfigDict(extra="allow")

    number: str
    phoneType: str = "Mobile"


class CustomerOnboardRequest(BaseModel):
    """Onboard payload — Helix /customer/onboard (KYC/IDV)."""

    model_config = ConfigDict(extra="allow")

    firstName: str = Field(min_length=1, max_length=64)
    lastName: str = Field(min_length=1, max_length=128)
    birthDate: str
    emailAddress: str
    taxId: str
    taxIdType: str = "SSN"
    addresses: list[CustomerAddress]
    phones: list[CustomerPhone]
    isSubjectToBackupWithholding: bool = False
    isOptedInToBankCommunication: bool = True
    isDocumentsAccepted: bool = True
    tag: str | None = Field(default=None, max_length=50)
    middleName: str | None = None
    isBusiness: bool | None = None
    businessName: str | None = None


class CustomerUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    customerId: int | None = None
    firstName: str | None = None
    lastName: str | None = None
    middleName: str | None = None
    emailAddress: str | None = None
    preferredName: str | None = None
    addresses: list[CustomerAddress] | None = None
    phones: list[CustomerPhone] | None = None
    customField1: str | None = None
    customField2: str | None = None
    customField3: str | None = None
    customField4: str | None = None
    customField5: str | None = None


class CustomerArchiveRequest(BaseModel):
    archiveReason: str = "Other"


class CustomerLockRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=200)


class CustomerBeneficiaryCreateRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    customerId: int
    firstName: str
    lastName: str
    birthDate: str | None = None
    taxId: str | None = None
    relationshipType: str | None = None
    percentage: float | None = None
    extra: dict[str, Any] | None = None
