"""Filter and pagination helpers for CRM customer mock API."""

from __future__ import annotations

import math

from crm_api.customers.mock_data import MOCK_CUSTOMERS
from crm_api.customers.schemas import (
    CustomerDetail,
    CustomerListResponse,
    CustomerSummary,
)

ALLOWED_PAGE_SIZES = {10, 25, 50}
VISIBLE_SEARCH_FIELDS = (
    "name",
    "email",
    "company",
    "country",
    "state",
    "status",
    "warmStatus",
    "phone",
    "segment",
    "accountOwner",
    "leadSource",
)


def _summary(customer: CustomerDetail) -> CustomerSummary:
    return CustomerSummary(**customer.model_dump(exclude={"comments"}))


def _matches_name(customer: CustomerDetail, name: str) -> bool:
    return name.lower() in customer.name.lower()


def _matches_email(customer: CustomerDetail, email: str) -> bool:
    return email.lower() in customer.email.lower()


def _matches_free_search(customer: CustomerDetail, query: str) -> bool:
    needle = query.lower()
    for field in VISIBLE_SEARCH_FIELDS:
        value = getattr(customer, field, "")
        if value is not None and needle in str(value).lower():
            return True
    if customer.lastCommunicationDate is not None:
        if needle in customer.lastCommunicationDate.isoformat().lower():
            return True
    if needle in customer.inclusionDate.isoformat().lower():
        return True
    return False


def filter_customers(
    *,
    name: str | None = None,
    email: str | None = None,
    q: str | None = None,
) -> list[CustomerDetail]:
    results = list(MOCK_CUSTOMERS)
    if name and name.strip():
        results = [c for c in results if _matches_name(c, name.strip())]
    if email and email.strip():
        results = [c for c in results if _matches_email(c, email.strip())]
    if q and q.strip():
        results = [c for c in results if _matches_free_search(c, q.strip())]
    return results


def paginate_customers(
    customers: list[CustomerDetail],
    *,
    page: int,
    page_size: int,
) -> CustomerListResponse:
    total = len(customers)
    total_pages = max(1, math.ceil(total / page_size)) if total else 0
    if total == 0:
        return CustomerListResponse(
            items=[],
            page=1,
            pageSize=page_size,
            totalItems=0,
            totalPages=0,
        )
    safe_page = min(max(page, 1), total_pages)
    start = (safe_page - 1) * page_size
    end = start + page_size
    items = [_summary(c) for c in customers[start:end]]
    return CustomerListResponse(
        items=items,
        page=safe_page,
        pageSize=page_size,
        totalItems=total,
        totalPages=total_pages,
    )


def get_customer_by_id(customer_id: str) -> CustomerDetail | None:
    for customer in MOCK_CUSTOMERS:
        if customer.id == customer_id:
            return customer
    return None
