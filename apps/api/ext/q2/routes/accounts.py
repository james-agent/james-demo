"""Q2 account HTTP routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from crm_api.db import get_db_session
from crm_api.models.q2_account_sync import Q2AccountSync
from crm_api.models.q2_customer_sync import Q2CustomerSync
from ext.q2.config import Q2ConfigError
from ext.q2.exceptions import Q2ApiError
from ext.q2.models.account import (
    AccountCreateRequest,
    AccountSyncStatusResponse,
    AccountSyncTriggerResponse,
    Q2Account,
    Q2AccountListResponse,
    Q2AccountSyncRecord,
    StopPayRequest,
)
from ext.q2.services.account import Q2AccountService
from ext.q2.services.sync_accounts import AccountSyncService

router = APIRouter(prefix="/api/v1/q2", tags=["q2-accounts"])


def get_q2_account_service() -> Q2AccountService:
    return Q2AccountService()


def get_account_sync_service() -> AccountSyncService:
    return AccountSyncService()


@router.post("/accounts/create", response_model=Q2Account)
async def create_account(
    body: AccountCreateRequest,
    session: Session = Depends(get_db_session),
    q2_service: Q2AccountService = Depends(get_q2_account_service),
    sync_service: AccountSyncService = Depends(get_account_sync_service),
) -> Q2Account:
    customer_sync = session.scalar(
        select(Q2CustomerSync).where(Q2CustomerSync.customer_id == body.customer_id)
    )
    if customer_sync is None or customer_sync.sync_status != "synced":
        raise HTTPException(
            status_code=400,
            detail="Customer must be synced to Q2 before account creation",
        )
    if not customer_sync.q2_customer_id:
        raise HTTPException(status_code=400, detail="Missing Q2 customer id")

    try:
        outcome = sync_service.provision_one(
            session,
            customer_sync,
            product_id=body.product_id,
        )
    except Q2ConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if outcome == "failed":
        row = session.scalar(
            select(Q2AccountSync).where(Q2AccountSync.customer_id == body.customer_id)
        )
        raise HTTPException(
            status_code=502, detail=row.last_error if row else "Account create failed"
        )
    if outcome == "skipped":
        row = session.scalar(
            select(Q2AccountSync).where(
                Q2AccountSync.customer_id == body.customer_id,
                Q2AccountSync.sync_status == "synced",
            )
        )
        if row and row.q2_account_id:
            return q2_service.get(row.q2_account_id)
        raise HTTPException(status_code=409, detail="Account already provisioned")

    row = session.scalar(
        select(Q2AccountSync).where(Q2AccountSync.customer_id == body.customer_id)
    )
    if row and row.q2_account_id:
        return q2_service.get(row.q2_account_id)
    raise HTTPException(status_code=502, detail="Account created but id not recorded")


@router.get("/accounts/customer/{customer_id}", response_model=Q2AccountListResponse)
async def list_customer_accounts(
    customer_id: UUID,
    session: Session = Depends(get_db_session),
    q2_service: Q2AccountService = Depends(get_q2_account_service),
) -> Q2AccountListResponse:
    customer_sync = session.scalar(
        select(Q2CustomerSync).where(Q2CustomerSync.customer_id == customer_id)
    )
    if customer_sync is None or not customer_sync.q2_customer_id:
        raise HTTPException(status_code=404, detail="Synced Q2 customer not found")
    try:
        return q2_service.list_by_customer(customer_sync.q2_customer_id)
    except Q2ApiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/accounts/sync-records/{customer_id}", response_model=Q2AccountSyncRecord)
async def get_account_sync_record(
    customer_id: UUID,
    session: Session = Depends(get_db_session),
) -> Q2AccountSyncRecord:
    row = session.scalar(
        select(Q2AccountSync).where(Q2AccountSync.customer_id == customer_id)
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Account sync record not found")
    return Q2AccountSyncRecord.model_validate(row)


@router.get("/accounts/{account_id}", response_model=Q2Account)
async def get_account(
    account_id: str,
    q2_service: Q2AccountService = Depends(get_q2_account_service),
) -> Q2Account:
    try:
        return q2_service.get(account_id)
    except Q2ApiError as exc:
        status = exc.status_code or 502
        raise HTTPException(status_code=status, detail=str(exc)) from exc


@router.post("/accounts/{account_id}/close", response_model=Q2Account)
async def close_account(
    account_id: str,
    q2_service: Q2AccountService = Depends(get_q2_account_service),
) -> Q2Account:
    try:
        return q2_service.close(account_id)
    except Q2ApiError as exc:
        raise HTTPException(
            status_code=exc.status_code or 502, detail=str(exc)
        ) from exc


@router.post("/accounts/{account_id}/lock", response_model=Q2Account)
async def lock_account(
    account_id: str,
    q2_service: Q2AccountService = Depends(get_q2_account_service),
) -> Q2Account:
    try:
        return q2_service.lock(account_id)
    except Q2ApiError as exc:
        raise HTTPException(
            status_code=exc.status_code or 502, detail=str(exc)
        ) from exc


@router.post("/accounts/{account_id}/unlock", response_model=Q2Account)
async def unlock_account(
    account_id: str,
    q2_service: Q2AccountService = Depends(get_q2_account_service),
) -> Q2Account:
    try:
        return q2_service.unlock(account_id)
    except Q2ApiError as exc:
        raise HTTPException(
            status_code=exc.status_code or 502, detail=str(exc)
        ) from exc


@router.post("/accounts/{account_id}/stop-pay")
async def create_stop_pay(
    account_id: str,
    body: StopPayRequest,
    q2_service: Q2AccountService = Depends(get_q2_account_service),
) -> dict:
    try:
        return q2_service.create_stop_pay(
            account_id,
            check_number=body.check_number,
            amount=body.amount,
            payee=body.payee,
        )
    except Q2ApiError as exc:
        raise HTTPException(
            status_code=exc.status_code or 502, detail=str(exc)
        ) from exc


@router.get("/accounts/{account_id}/stop-pay")
async def list_stop_pay(
    account_id: str,
    q2_service: Q2AccountService = Depends(get_q2_account_service),
) -> dict:
    try:
        return q2_service.list_stop_pay(account_id)
    except Q2ApiError as exc:
        raise HTTPException(
            status_code=exc.status_code or 502, detail=str(exc)
        ) from exc


@router.delete("/accounts/{account_id}/stop-pay/{stop_pay_id}")
async def cancel_stop_pay(
    account_id: str,
    stop_pay_id: str,
    q2_service: Q2AccountService = Depends(get_q2_account_service),
) -> dict:
    del account_id
    try:
        return q2_service.cancel_stop_pay(stop_pay_id)
    except Q2ApiError as exc:
        raise HTTPException(
            status_code=exc.status_code or 502, detail=str(exc)
        ) from exc


@router.post("/sync/accounts", response_model=AccountSyncTriggerResponse)
async def trigger_account_sync(
    product_id: str | None = Query(None),
    session: Session = Depends(get_db_session),
    sync_service: AccountSyncService = Depends(get_account_sync_service),
) -> AccountSyncTriggerResponse:
    try:
        return sync_service.run_sync(session, product_id=product_id)
    except Q2ConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/sync/accounts/status", response_model=AccountSyncStatusResponse)
async def account_sync_status(
    session: Session = Depends(get_db_session),
    sync_service: AccountSyncService = Depends(get_account_sync_service),
) -> AccountSyncStatusResponse:
    return sync_service.get_status(session)
