"""Q2 Helix account management HTTP routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from james.ext.q2.models.account import (
    AccountCloseRequest,
    AccountCreateRequest,
    AccountLockRequest,
    StopPayCreateRequest,
    StopPayExpireRequest,
)
from james.ext.q2.routes.http import raise_q2_http
from james.ext.q2.services.account import AccountService

router = APIRouter(prefix="/api/v1/q2/accounts", tags=["q2-accounts"])


class AccountResponse(BaseModel):
    result: str = "OK"
    account: dict[str, Any] = Field(default_factory=dict)


class AccountListResponse(BaseModel):
    result: str = "OK"
    accounts: list[Any] = Field(default_factory=list)


class StopPayResponse(BaseModel):
    result: str = "OK"
    stop_pay: dict[str, Any] = Field(default_factory=dict)


class StopPayListResponse(BaseModel):
    result: str = "OK"
    stop_pays: list[Any] = Field(default_factory=list)


@router.post("", response_model=AccountResponse)
def create_account(body: AccountCreateRequest) -> AccountResponse:
    try:
        with AccountService() as service:
            account = service.create(body)
        return AccountResponse(account=account if isinstance(account, dict) else {"data": account})
    except Exception as exc:
        raise_q2_http(exc)
        raise  # pragma: no cover


@router.get("/by-customer/{customer_id}", response_model=AccountListResponse)
def list_accounts(customer_id: int) -> AccountListResponse:
    try:
        with AccountService() as service:
            accounts = service.list(customer_id)
        return AccountListResponse(accounts=accounts)
    except Exception as exc:
        raise_q2_http(exc)
        raise  # pragma: no cover


@router.get("/{customer_id}/{account_id}", response_model=AccountResponse)
def get_account(customer_id: int, account_id: int) -> AccountResponse:
    try:
        with AccountService() as service:
            account = service.get(customer_id, account_id)
        return AccountResponse(account=account if isinstance(account, dict) else {"data": account})
    except Exception as exc:
        raise_q2_http(exc)
        raise  # pragma: no cover


@router.post("/close", response_model=AccountResponse)
def close_account(body: AccountCloseRequest) -> AccountResponse:
    try:
        with AccountService() as service:
            account = service.close(body)
        return AccountResponse(account=account if isinstance(account, dict) else {"data": account})
    except Exception as exc:
        raise_q2_http(exc)
        raise  # pragma: no cover


@router.post("/lock", response_model=AccountResponse)
def lock_account(body: AccountLockRequest) -> AccountResponse:
    try:
        with AccountService() as service:
            account = service.lock(body)
        return AccountResponse(account=account if isinstance(account, dict) else {"data": account})
    except Exception as exc:
        raise_q2_http(exc)
        raise  # pragma: no cover


@router.post("/{customer_id}/{account_id}/unlock", response_model=AccountResponse)
def unlock_account(customer_id: int, account_id: int) -> AccountResponse:
    try:
        with AccountService() as service:
            account = service.unlock(customer_id, account_id)
        return AccountResponse(account=account if isinstance(account, dict) else {"data": account})
    except Exception as exc:
        raise_q2_http(exc)
        raise  # pragma: no cover


@router.post("/stop-pays", response_model=StopPayResponse)
def create_stop_pay(body: StopPayCreateRequest) -> StopPayResponse:
    try:
        with AccountService() as service:
            stop_pay = service.create_stop_pay(body)
        return StopPayResponse(stop_pay=stop_pay if isinstance(stop_pay, dict) else {"data": stop_pay})
    except Exception as exc:
        raise_q2_http(exc)
        raise  # pragma: no cover


@router.get("/{customer_id}/{account_id}/stop-pays", response_model=StopPayListResponse)
def list_stop_pays(
    customer_id: int,
    account_id: int,
    begin_date: str | None = Query(default=None, alias="beginDate"),
    end_date: str | None = Query(default=None, alias="endDate"),
) -> StopPayListResponse:
    try:
        with AccountService() as service:
            data = service.list_stop_pays(
                customer_id,
                account_id,
                begin_date=begin_date,
                end_date=end_date,
            )
        if isinstance(data, list):
            return StopPayListResponse(stop_pays=data)
        if isinstance(data, dict):
            items = data.get("stopPays") or data.get("results") or []
            if isinstance(items, list):
                return StopPayListResponse(stop_pays=items)
            return StopPayListResponse(stop_pays=[data])
        return StopPayListResponse(stop_pays=[])
    except Exception as exc:
        raise_q2_http(exc)
        raise  # pragma: no cover


@router.post("/stop-pays/cancel", response_model=StopPayResponse)
def cancel_stop_pay(body: StopPayExpireRequest) -> StopPayResponse:
    try:
        with AccountService() as service:
            stop_pay = service.cancel_stop_pay(body.customerId, body.accountId, body.stopPayId)
        return StopPayResponse(stop_pay=stop_pay if isinstance(stop_pay, dict) else {"data": stop_pay})
    except Exception as exc:
        raise_q2_http(exc)
        raise  # pragma: no cover
