"""Q2 Helix customer API routes — middleware-only Helix access."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from fastapi import APIRouter, Depends

from ext.q2.client import HelixAPIError
from ext.q2.models.customer import (
    CustomerBeneficiary,
    CustomerLockRequest,
    CustomerOnboardRequest,
    CustomerUpdateRequest,
)
from ext.q2.routes._http import as_json_response, helix_http_error
from ext.q2.services.customer import CustomerService

router = APIRouter(prefix="/api/v1/q2/customers", tags=["q2-customers"])


def get_customer_service() -> Iterator[CustomerService]:
    service = CustomerService()
    try:
        yield service
    finally:
        service.close()


@router.post("/onboard")
def onboard_customer(
    body: CustomerOnboardRequest,
    service: CustomerService = Depends(get_customer_service),
) -> Any:
    try:
        return as_json_response(service.onboard(body))
    except HelixAPIError as exc:
        raise helix_http_error(exc) from exc


@router.get("/by-tag/{tag}")
def get_customer_by_tag(
    tag: str,
    service: CustomerService = Depends(get_customer_service),
) -> Any:
    try:
        return as_json_response(service.get_by_tag(tag))
    except HelixAPIError as exc:
        raise helix_http_error(exc) from exc


@router.get("/{customer_id}")
def get_customer(
    customer_id: int,
    service: CustomerService = Depends(get_customer_service),
) -> Any:
    try:
        return as_json_response(service.get(customer_id))
    except HelixAPIError as exc:
        raise helix_http_error(exc) from exc


@router.put("/{customer_id}")
def update_customer(
    customer_id: int,
    body: CustomerUpdateRequest,
    service: CustomerService = Depends(get_customer_service),
) -> Any:
    try:
        return as_json_response(service.update(customer_id, body))
    except HelixAPIError as exc:
        raise helix_http_error(exc) from exc


@router.post("/{customer_id}/archive")
def archive_customer(
    customer_id: int,
    service: CustomerService = Depends(get_customer_service),
) -> Any:
    try:
        return as_json_response(service.archive(customer_id))
    except HelixAPIError as exc:
        raise helix_http_error(exc) from exc


@router.post("/{customer_id}/lock")
def lock_customer(
    customer_id: int,
    body: CustomerLockRequest,
    service: CustomerService = Depends(get_customer_service),
) -> Any:
    try:
        return as_json_response(service.lock(customer_id, body.reason))
    except HelixAPIError as exc:
        raise helix_http_error(exc) from exc


@router.post("/{customer_id}/unlock")
def unlock_customer(
    customer_id: int,
    service: CustomerService = Depends(get_customer_service),
) -> Any:
    try:
        return as_json_response(service.unlock(customer_id))
    except HelixAPIError as exc:
        raise helix_http_error(exc) from exc


@router.get("/{customer_id}/beneficiaries")
def list_beneficiaries(
    customer_id: int,
    service: CustomerService = Depends(get_customer_service),
) -> Any:
    try:
        return as_json_response(service.list_beneficiaries(customer_id))
    except HelixAPIError as exc:
        raise helix_http_error(exc) from exc


@router.post("/{customer_id}/beneficiaries")
def add_beneficiary(
    customer_id: int,
    body: CustomerBeneficiary,
    service: CustomerService = Depends(get_customer_service),
) -> Any:
    try:
        return as_json_response(service.add_beneficiary(customer_id, body))
    except HelixAPIError as exc:
        raise helix_http_error(exc) from exc
