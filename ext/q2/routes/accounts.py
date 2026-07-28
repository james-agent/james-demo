"""Q2 Helix account API routes — middleware-only Helix access."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from fastapi import APIRouter, Depends

from ext.q2.client import HelixAPIError
from ext.q2.models.account import AccountCreateRequest, AccountUpdateLimitRequest, StopPayRequest
from ext.q2.routes._http import as_json_response, helix_http_error
from ext.q2.services.account import AccountService

router = APIRouter(prefix="/api/v1/q2/accounts", tags=["q2-accounts"])


def get_account_service() -> Iterator[AccountService]:
    service = AccountService()
    try:
        yield service
    finally:
        service.close_client()


@router.post("/create")
def create_account(
    body: AccountCreateRequest,
    service: AccountService = Depends(get_account_service),
) -> Any:
    try:
        return as_json_response(service.create(body))
    except HelixAPIError as exc:
        raise helix_http_error(exc) from exc


@router.get("/customer/{customer_id}")
def list_customer_accounts(
    customer_id: int,
    service: AccountService = Depends(get_account_service),
) -> Any:
    try:
        return as_json_response(service.list_by_customer(customer_id))
    except HelixAPIError as exc:
        raise helix_http_error(exc) from exc


@router.get("/by-tag/{tag}")
def get_account_by_tag(
    tag: str,
    service: AccountService = Depends(get_account_service),
) -> Any:
    try:
        return as_json_response(service.get_by_tag(tag))
    except HelixAPIError as exc:
        raise helix_http_error(exc) from exc


@router.get("/{account_id}")
def get_account(
    account_id: int,
    service: AccountService = Depends(get_account_service),
) -> Any:
    try:
        return as_json_response(service.get(account_id))
    except HelixAPIError as exc:
        raise helix_http_error(exc) from exc


@router.post("/{account_id}/close")
def close_account(
    account_id: int,
    service: AccountService = Depends(get_account_service),
) -> Any:
    try:
        return as_json_response(service.close(account_id))
    except HelixAPIError as exc:
        raise helix_http_error(exc) from exc


@router.post("/{account_id}/lock")
def lock_account(
    account_id: int,
    service: AccountService = Depends(get_account_service),
) -> Any:
    try:
        return as_json_response(service.lock(account_id))
    except HelixAPIError as exc:
        raise helix_http_error(exc) from exc


@router.post("/{account_id}/unlock")
def unlock_account(
    account_id: int,
    service: AccountService = Depends(get_account_service),
) -> Any:
    try:
        return as_json_response(service.unlock(account_id))
    except HelixAPIError as exc:
        raise helix_http_error(exc) from exc


@router.post("/{account_id}/limits")
def update_account_limit(
    account_id: int,
    body: AccountUpdateLimitRequest,
    service: AccountService = Depends(get_account_service),
) -> Any:
    try:
        return as_json_response(service.update_limit(account_id, body))
    except HelixAPIError as exc:
        raise helix_http_error(exc) from exc


@router.post("/{account_id}/stop-pay")
def create_stop_pay(
    account_id: int,
    body: StopPayRequest,
    service: AccountService = Depends(get_account_service),
) -> Any:
    try:
        return as_json_response(service.create_stop_pay(account_id, body))
    except HelixAPIError as exc:
        raise helix_http_error(exc) from exc


@router.get("/{account_id}/stop-pay")
def list_stop_pay(
    account_id: int,
    service: AccountService = Depends(get_account_service),
) -> Any:
    try:
        return as_json_response(service.list_stop_pay(account_id))
    except HelixAPIError as exc:
        raise helix_http_error(exc) from exc


@router.delete("/{account_id}/stop-pay/{stop_pay_id}")
def cancel_stop_pay(
    account_id: int,
    stop_pay_id: int,
    service: AccountService = Depends(get_account_service),
) -> Any:
    _ = account_id  # path symmetry with catalog; Helix cancel uses stopPayId
    try:
        return as_json_response(service.cancel_stop_pay(stop_pay_id))
    except HelixAPIError as exc:
        raise helix_http_error(exc) from exc
