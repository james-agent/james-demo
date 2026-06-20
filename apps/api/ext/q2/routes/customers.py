"""Q2 customer HTTP routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from crm_api.db import get_db_session
from crm_api.models.q2_customer_sync import Q2CustomerSync
from crm_api.services.customer_registry import get_customer_by_id
from ext.q2.models.customer import CustomerOnboardRequest, Q2CustomerResponse, Q2CustomerSyncRecord
from ext.q2.services.customer import Q2CustomerService
from ext.q2.services.sync_customers import CustomerSyncService, customer_tag

router = APIRouter(prefix="/api/v1/q2", tags=["q2-customers"])


def get_q2_customer_service() -> Q2CustomerService:
    return Q2CustomerService()


@router.post("/customers/onboard", response_model=Q2CustomerResponse)
async def onboard_customer(
    body: CustomerOnboardRequest,
    session: Session = Depends(get_db_session),
    q2_service: Q2CustomerService = Depends(get_q2_customer_service),
) -> Q2CustomerResponse:
    customer = get_customer_by_id(session, body.customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Local customer not found")
    sync_service = CustomerSyncService(q2_service)
    outcome = sync_service.sync_one(session, customer, mode="full")
    if outcome == "failed":
        row = session.scalar(select(Q2CustomerSync).where(Q2CustomerSync.customer_id == customer.id))
        raise HTTPException(status_code=502, detail=row.last_error if row else "Q2 onboard failed")
    return q2_service.get_by_tag(customer_tag(customer.id))


@router.get("/customers/by-tag/{tag}", response_model=Q2CustomerResponse)
async def get_customer_by_tag(
    tag: str,
    q2_service: Q2CustomerService = Depends(get_q2_customer_service),
) -> Q2CustomerResponse:
    try:
        return q2_service.get_by_tag(tag)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/customers/sync-records/{customer_id}", response_model=Q2CustomerSyncRecord)
async def get_sync_record(
    customer_id: UUID,
    session: Session = Depends(get_db_session),
) -> Q2CustomerSyncRecord:
    row = session.scalar(select(Q2CustomerSync).where(Q2CustomerSync.customer_id == customer_id))
    if row is None:
        raise HTTPException(status_code=404, detail="Sync record not found")
    return Q2CustomerSyncRecord.model_validate(row)
