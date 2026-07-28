"""Q2 Helix customer lifecycle service."""

from __future__ import annotations

from typing import Any

from crm_api.ext.q2.client import Q2HelixClient
from crm_api.ext.q2.models.customer import (
    CustomerBeneficiary,
    CustomerOnboardRequest,
    CustomerUpdateRequest,
    Q2Customer,
)


class CustomerService:
    def __init__(self, client: Q2HelixClient | None = None) -> None:
        self.client = client or Q2HelixClient()

    async def onboard(self, data: CustomerOnboardRequest) -> Q2Customer:
        payload = data.model_dump(exclude_none=True)
        result = await self.client.post("customer/onboard", payload)
        return Q2Customer.from_helix(_unwrap(result))

    async def get(self, customer_id: int) -> Q2Customer:
        result = await self.client.post("customer/get", {"customerId": customer_id})
        return Q2Customer.from_helix(_unwrap(result))

    async def get_by_tag(self, tag: str) -> Q2Customer:
        result = await self.client.post("customer/getByTag", {"tag": tag})
        return Q2Customer.from_helix(_unwrap(result))

    async def update(self, customer_id: int, data: CustomerUpdateRequest) -> Q2Customer:
        payload = {"customerId": customer_id, **data.model_dump(exclude_none=True)}
        result = await self.client.post("customer/update", payload)
        return Q2Customer.from_helix(_unwrap(result))

    async def archive(self, customer_id: int) -> Q2Customer:
        result = await self.client.post("customer/archive", {"customerId": customer_id})
        return Q2Customer.from_helix(_unwrap(result))

    async def lock(self, customer_id: int, reason: str) -> Q2Customer:
        result = await self.client.post(
            "customer/lock",
            {"customerId": customer_id, "reason": reason},
        )
        return Q2Customer.from_helix(_unwrap(result))

    async def unlock(self, customer_id: int) -> Q2Customer:
        result = await self.client.post("customer/unlock", {"customerId": customer_id})
        return Q2Customer.from_helix(_unwrap(result))

    async def list_beneficiaries(self, customer_id: int) -> list[dict[str, Any]]:
        result = await self.client.post("customerBeneficiary/list", {"customerId": customer_id})
        data = _unwrap(result)
        if isinstance(data, dict):
            items = data.get("beneficiaries") or data.get("customerBeneficiaries") or []
            return items if isinstance(items, list) else []
        return data if isinstance(data, list) else []

    async def add_beneficiary(self, customer_id: int, data: CustomerBeneficiary) -> Any:
        payload = {"customerId": customer_id, **data.model_dump(exclude_none=True)}
        return await self.client.post("customerBeneficiary/create", payload)


def _unwrap(result: Any) -> Any:
    if isinstance(result, dict) and "customer" in result and isinstance(result["customer"], dict):
        return result["customer"]
    return result
