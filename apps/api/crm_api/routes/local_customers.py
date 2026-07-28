"""Local customer persistence routes (source of truth for Q2 sync)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from crm_api.db import get_db
from crm_api.models.customer import Customer
from crm_api.schemas.local_customer import LocalCustomerCreate, LocalCustomerRead, to_read_model

router = APIRouter(prefix="/api/v1/customers", tags=["local-customers"])


@router.post("", response_model=LocalCustomerRead, status_code=201)
async def create_customer(
    body: LocalCustomerCreate,
    db: AsyncSession = Depends(get_db),
) -> LocalCustomerRead:
    customer = Customer(
        email=str(body.email).lower(),
        first_name=body.first_name,
        last_name=body.last_name,
        middle_name=body.middle_name,
        external_ref=body.external_ref,
        birth_date=body.birth_date,
        tax_id=body.tax_id,
        tax_id_type=body.tax_id_type,
        phone_number=body.phone_number,
        address_line1=body.address_line1,
        city=body.city,
        state=body.state,
        postal_code=body.postal_code,
        country_code=body.country_code or "USA",
        q2_sync_status="pending",
    )
    db.add(customer)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Customer email already exists") from exc
    await db.refresh(customer)
    return to_read_model(customer)


@router.get("", response_model=list[LocalCustomerRead])
async def list_customers(db: AsyncSession = Depends(get_db)) -> list[LocalCustomerRead]:
    result = await db.execute(select(Customer).order_by(Customer.created_at))
    return [to_read_model(row) for row in result.scalars().all()]


@router.get("/{customer_id}", response_model=LocalCustomerRead)
async def get_customer(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> LocalCustomerRead:
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return to_read_model(customer)
