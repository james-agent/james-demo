"""Q2 Helix customer management routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from crm_api.ext.q2.client import Q2HelixClient, Q2HelixError
from crm_api.ext.q2.models.customer import (
    CustomerBeneficiary,
    CustomerLockRequest,
    CustomerOnboardRequest,
    CustomerUpdateRequest,
    Q2Customer,
)
from crm_api.ext.q2.routes.deps import raise_q2_http_error
from crm_api.ext.q2.services.customer import CustomerService

router = APIRouter(prefix="/api/v1/q2/customers", tags=["q2-customers"])


@router.post("/onboard", response_model=Q2Customer)
async def onboard_customer(body: CustomerOnboardRequest) -> Q2Customer:
    try:
        async with Q2HelixClient() as client:
            return await CustomerService(client).onboard(body)
    except Q2HelixError as exc:
        raise_q2_http_error(exc)


@router.get("/by-tag/{tag}", response_model=Q2Customer)
async def get_customer_by_tag(tag: str) -> Q2Customer:
    try:
        async with Q2HelixClient() as client:
            return await CustomerService(client).get_by_tag(tag)
    except Q2HelixError as exc:
        raise_q2_http_error(exc)


@router.get("/{customer_id}", response_model=Q2Customer)
async def get_customer(customer_id: int) -> Q2Customer:
    try:
        async with Q2HelixClient() as client:
            return await CustomerService(client).get(customer_id)
    except Q2HelixError as exc:
        raise_q2_http_error(exc)


@router.put("/{customer_id}", response_model=Q2Customer)
async def update_customer(customer_id: int, body: CustomerUpdateRequest) -> Q2Customer:
    try:
        async with Q2HelixClient() as client:
            return await CustomerService(client).update(customer_id, body)
    except Q2HelixError as exc:
        raise_q2_http_error(exc)


@router.post("/{customer_id}/archive", response_model=Q2Customer)
async def archive_customer(customer_id: int) -> Q2Customer:
    try:
        async with Q2HelixClient() as client:
            return await CustomerService(client).archive(customer_id)
    except Q2HelixError as exc:
        raise_q2_http_error(exc)


@router.post("/{customer_id}/lock", response_model=Q2Customer)
async def lock_customer(customer_id: int, body: CustomerLockRequest | None = None) -> Q2Customer:
    reason = (body.reason if body else None) or "fraud_review"
    try:
        async with Q2HelixClient() as client:
            return await CustomerService(client).lock(customer_id, reason)
    except Q2HelixError as exc:
        raise_q2_http_error(exc)


@router.post("/{customer_id}/unlock", response_model=Q2Customer)
async def unlock_customer(customer_id: int) -> Q2Customer:
    try:
        async with Q2HelixClient() as client:
            return await CustomerService(client).unlock(customer_id)
    except Q2HelixError as exc:
        raise_q2_http_error(exc)


@router.get("/{customer_id}/beneficiaries")
async def list_beneficiaries(customer_id: int) -> list[dict[str, Any]]:
    try:
        async with Q2HelixClient() as client:
            return await CustomerService(client).list_beneficiaries(customer_id)
    except Q2HelixError as exc:
        raise_q2_http_error(exc)


@router.post("/{customer_id}/beneficiaries")
async def add_beneficiary(customer_id: int, body: CustomerBeneficiary) -> Any:
    try:
        async with Q2HelixClient() as client:
            return await CustomerService(client).add_beneficiary(customer_id, body)
    except Q2HelixError as exc:
        raise_q2_http_error(exc)
