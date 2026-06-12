"""Read-only mock CRM customer endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from crm_api.customers.schemas import CustomerDetail, CustomerListResponse
from crm_api.customers.service import ALLOWED_PAGE_SIZES, filter_customers, get_customer_by_id, paginate_customers

router = APIRouter(prefix="/api/v1/crm", tags=["crm-customers"])


@router.get("/customers", response_model=CustomerListResponse)
async def list_customers(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1),
    name: str | None = Query(None),
    email: str | None = Query(None),
    q: str | None = Query(None),
) -> CustomerListResponse:
    if pageSize not in ALLOWED_PAGE_SIZES:
        raise HTTPException(status_code=400, detail="Invalid pageSize. Allowed values: 10, 25, 50.")
    filtered = filter_customers(name=name, email=email, q=q)
    return paginate_customers(filtered, page=page, page_size=pageSize)


@router.get("/customers/{customer_id}", response_model=CustomerDetail)
async def get_customer(customer_id: str) -> CustomerDetail:
    customer = get_customer_by_id(customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer
