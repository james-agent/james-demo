"""Q2 Helix customer/account sync routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from crm_api.db import get_db
from crm_api.ext.q2.client import Q2HelixClient, Q2HelixError
from crm_api.ext.q2.routes.deps import raise_q2_http_error
from crm_api.ext.q2.services.customer_account_sync import (
    CustomerAccountSyncService,
    SyncBatchResult,
    SyncRowResult,
)

router = APIRouter(prefix="/api/v1/q2/sync", tags=["q2-sync"])


@router.post("/customers", response_model=SyncBatchResult)
async def sync_all_customers(db: AsyncSession = Depends(get_db)) -> SyncBatchResult:
    try:
        async with Q2HelixClient() as client:
            result = await CustomerAccountSyncService(db, client).sync_all()
        await db.commit()
        return result
    except Q2HelixError as exc:
        await db.rollback()
        raise_q2_http_error(exc)


@router.post("/customers/{local_customer_id}", response_model=SyncRowResult)
async def sync_one_customer(
    local_customer_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> SyncRowResult:
    try:
        async with Q2HelixClient() as client:
            result = await CustomerAccountSyncService(db, client).sync_by_id(local_customer_id)
        await db.commit()
        return result
    except Q2HelixError as exc:
        await db.rollback()
        raise_q2_http_error(exc)
