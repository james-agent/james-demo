"""Q2 Helix account management routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from crm_api.ext.q2.client import Q2HelixClient, Q2HelixError
from crm_api.ext.q2.models.account import (
    AccountCreateRequest,
    AccountUpdateLimitRequest,
    Q2Account,
    StopPayRequest,
)
from crm_api.ext.q2.routes.deps import raise_q2_http_error
from crm_api.ext.q2.services.account import AccountService

router = APIRouter(prefix="/api/v1/q2/accounts", tags=["q2-accounts"])


@router.post("/create", response_model=Q2Account)
async def create_account(body: AccountCreateRequest) -> Q2Account:
    try:
        async with Q2HelixClient() as client:
            return await AccountService(client).create(body)
    except Q2HelixError as exc:
        raise_q2_http_error(exc)


@router.get("/customer/{customer_id}", response_model=list[Q2Account])
async def list_customer_accounts(customer_id: int) -> list[Q2Account]:
    try:
        async with Q2HelixClient() as client:
            return await AccountService(client).list_by_customer(customer_id)
    except Q2HelixError as exc:
        raise_q2_http_error(exc)


@router.get("/by-tag/{tag}", response_model=Q2Account)
async def get_account_by_tag(tag: str) -> Q2Account:
    try:
        async with Q2HelixClient() as client:
            return await AccountService(client).get_by_tag(tag)
    except Q2HelixError as exc:
        raise_q2_http_error(exc)


@router.get("/{account_id}", response_model=Q2Account)
async def get_account(account_id: int) -> Q2Account:
    try:
        async with Q2HelixClient() as client:
            return await AccountService(client).get(account_id)
    except Q2HelixError as exc:
        raise_q2_http_error(exc)


@router.post("/{account_id}/close", response_model=Q2Account)
async def close_account(account_id: int) -> Q2Account:
    try:
        async with Q2HelixClient() as client:
            return await AccountService(client).close(account_id)
    except Q2HelixError as exc:
        raise_q2_http_error(exc)


@router.post("/{account_id}/lock", response_model=Q2Account)
async def lock_account(account_id: int) -> Q2Account:
    try:
        async with Q2HelixClient() as client:
            return await AccountService(client).lock(account_id)
    except Q2HelixError as exc:
        raise_q2_http_error(exc)


@router.post("/{account_id}/unlock", response_model=Q2Account)
async def unlock_account(account_id: int) -> Q2Account:
    try:
        async with Q2HelixClient() as client:
            return await AccountService(client).unlock(account_id)
    except Q2HelixError as exc:
        raise_q2_http_error(exc)


@router.post("/{account_id}/limits")
async def update_account_limit(account_id: int, body: AccountUpdateLimitRequest) -> Any:
    try:
        async with Q2HelixClient() as client:
            return await AccountService(client).update_limit(account_id, body)
    except Q2HelixError as exc:
        raise_q2_http_error(exc)


@router.post("/{account_id}/stop-pay")
async def create_stop_pay(account_id: int, body: StopPayRequest) -> Any:
    try:
        async with Q2HelixClient() as client:
            return await AccountService(client).create_stop_pay(account_id, body)
    except Q2HelixError as exc:
        raise_q2_http_error(exc)


@router.get("/{account_id}/stop-pay")
async def list_stop_pay(account_id: int) -> list[Any]:
    try:
        async with Q2HelixClient() as client:
            return await AccountService(client).list_stop_pay(account_id)
    except Q2HelixError as exc:
        raise_q2_http_error(exc)


@router.delete("/{account_id}/stop-pay/{stop_pay_id}")
async def cancel_stop_pay(account_id: int, stop_pay_id: int) -> Any:
    _ = account_id  # path symmetry with Helix account-scoped URLs
    try:
        async with Q2HelixClient() as client:
            return await AccountService(client).cancel_stop_pay(stop_pay_id)
    except Q2HelixError as exc:
        raise_q2_http_error(exc)
