"""Pydantic models for CRM customer mock API."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

CustomerStatus = Literal["Lead", "Prospect", "Active", "Inactive"]
WarmStatus = Literal["Hot", "Warm"]


class CustomerComment(BaseModel):
    id: str
    text: str
    author: str
    createdAt: datetime


class CustomerSummary(BaseModel):
    id: str
    name: str
    email: str
    company: str
    country: str
    state: str
    status: CustomerStatus
    warmStatus: WarmStatus
    inclusionDate: datetime
    lastCommunicationDate: datetime | None
    phone: str
    segment: str
    accountOwner: str
    leadSource: str


class CustomerDetail(CustomerSummary):
    comments: list[CustomerComment] = Field(default_factory=list)


class CustomerListResponse(BaseModel):
    items: list[CustomerSummary]
    page: int
    pageSize: int
    totalItems: int
    totalPages: int
