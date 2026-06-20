"""Q2 customer bulk sync routes."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from crm_api.db import get_db_session
from ext.q2.models.customer import SyncStatusResponse, SyncTriggerResponse
from ext.q2.services.sync_customers import CustomerSyncService

router = APIRouter(prefix="/api/v1/q2/sync", tags=["q2-sync"])


def get_sync_service() -> CustomerSyncService:
    return CustomerSyncService()


@router.post("/customers", response_model=SyncTriggerResponse)
async def trigger_customer_sync(
    mode: Literal["full", "incremental"] = Query("full"),
    session: Session = Depends(get_db_session),
    sync_service: CustomerSyncService = Depends(get_sync_service),
) -> SyncTriggerResponse:
    return sync_service.run_sync(session, mode=mode)


@router.get("/customers/status", response_model=SyncStatusResponse)
async def customer_sync_status(
    session: Session = Depends(get_db_session),
    sync_service: CustomerSyncService = Depends(get_sync_service),
) -> SyncStatusResponse:
    return sync_service.get_status(session)
