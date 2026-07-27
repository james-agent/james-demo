"""Q2 Helix customer management HTTP routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from james.ext.q2.models.customer import (
    CustomerArchiveRequest,
    CustomerBeneficiaryCreateRequest,
    CustomerLockRequest,
    CustomerOnboardRequest,
    CustomerUpdateRequest,
)
from james.ext.q2.routes.http import raise_q2_http
from james.ext.q2.services.customer import CustomerService

router = APIRouter(prefix="/api/v1/q2/customers", tags=["q2-customers"])


class CustomerResponse(BaseModel):
    result: str = "OK"
    customer: dict[str, Any] = Field(default_factory=dict)


class BeneficiaryListResponse(BaseModel):
    result: str = "OK"
    beneficiaries: list[Any] = Field(default_factory=list)


@router.post("/onboard", response_model=CustomerResponse)
def onboard_customer(body: CustomerOnboardRequest) -> CustomerResponse:
    try:
        with CustomerService() as service:
            customer = service.onboard(body)
        return CustomerResponse(customer=customer if isinstance(customer, dict) else {"data": customer})
    except Exception as exc:
        raise_q2_http(exc)
        raise  # pragma: no cover


@router.get("/by-tag/{tag}", response_model=CustomerResponse)
def get_customer_by_tag(tag: str) -> CustomerResponse:
    try:
        with CustomerService() as service:
            customer = service.get_by_tag(tag)
        return CustomerResponse(customer=customer if isinstance(customer, dict) else {"data": customer})
    except Exception as exc:
        raise_q2_http(exc)
        raise  # pragma: no cover


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int) -> CustomerResponse:
    try:
        with CustomerService() as service:
            customer = service.get(customer_id)
        return CustomerResponse(customer=customer if isinstance(customer, dict) else {"data": customer})
    except Exception as exc:
        raise_q2_http(exc)
        raise  # pragma: no cover


@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(customer_id: int, body: CustomerUpdateRequest) -> CustomerResponse:
    try:
        with CustomerService() as service:
            customer = service.update(customer_id, body)
        return CustomerResponse(customer=customer if isinstance(customer, dict) else {"data": customer})
    except Exception as exc:
        raise_q2_http(exc)
        raise  # pragma: no cover


@router.post("/{customer_id}/archive", response_model=CustomerResponse)
def archive_customer(customer_id: int, body: CustomerArchiveRequest | None = None) -> CustomerResponse:
    reason = (body.archiveReason if body else "Other") or "Other"
    try:
        with CustomerService() as service:
            customer = service.archive(customer_id, reason)
        return CustomerResponse(customer=customer if isinstance(customer, dict) else {"data": customer})
    except Exception as exc:
        raise_q2_http(exc)
        raise  # pragma: no cover


@router.post("/{customer_id}/lock", response_model=CustomerResponse)
def lock_customer(customer_id: int, body: CustomerLockRequest) -> CustomerResponse:
    try:
        with CustomerService() as service:
            customer = service.lock(customer_id, body.reason)
        return CustomerResponse(customer=customer if isinstance(customer, dict) else {"data": customer})
    except Exception as exc:
        raise_q2_http(exc)
        raise  # pragma: no cover


@router.post("/{customer_id}/unlock", response_model=CustomerResponse)
def unlock_customer(customer_id: int) -> CustomerResponse:
    try:
        with CustomerService() as service:
            customer = service.unlock(customer_id)
        return CustomerResponse(customer=customer if isinstance(customer, dict) else {"data": customer})
    except Exception as exc:
        raise_q2_http(exc)
        raise  # pragma: no cover


@router.get("/{customer_id}/beneficiaries", response_model=BeneficiaryListResponse)
def list_beneficiaries(customer_id: int) -> BeneficiaryListResponse:
    try:
        with CustomerService() as service:
            data = service.list_beneficiaries(customer_id)
        if isinstance(data, list):
            return BeneficiaryListResponse(beneficiaries=data)
        if isinstance(data, dict):
            items = data.get("beneficiaries") or data.get("results") or []
            if isinstance(items, list):
                return BeneficiaryListResponse(beneficiaries=items)
            return BeneficiaryListResponse(beneficiaries=[data])
        return BeneficiaryListResponse(beneficiaries=[])
    except Exception as exc:
        raise_q2_http(exc)
        raise  # pragma: no cover


@router.post("/{customer_id}/beneficiaries", response_model=CustomerResponse)
def add_beneficiary(customer_id: int, body: CustomerBeneficiaryCreateRequest) -> CustomerResponse:
    payload = body.model_dump(exclude_none=True)
    payload.pop("customerId", None)
    try:
        with CustomerService() as service:
            result = service.add_beneficiary(customer_id, payload)
        return CustomerResponse(customer=result if isinstance(result, dict) else {"data": result})
    except Exception as exc:
        raise_q2_http(exc)
        raise  # pragma: no cover
