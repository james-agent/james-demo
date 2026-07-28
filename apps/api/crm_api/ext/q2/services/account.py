"""Q2 Helix account lifecycle service."""

from __future__ import annotations

from typing import Any

from crm_api.ext.q2.client import Q2HelixClient
from crm_api.ext.q2.models.account import (
    AccountCreateRequest,
    AccountUpdateLimitRequest,
    Q2Account,
    StopPayRequest,
)


class AccountService:
    def __init__(self, client: Q2HelixClient | None = None) -> None:
        self.client = client or Q2HelixClient()

    async def create(self, data: AccountCreateRequest) -> Q2Account:
        result = await self.client.post("account/create", data.model_dump())
        return Q2Account.from_helix(_unwrap_account(result))

    async def get(self, account_id: int) -> Q2Account:
        result = await self.client.post("account/get", {"accountId": account_id})
        return Q2Account.from_helix(_unwrap_account(result))

    async def get_by_tag(self, tag: str) -> Q2Account:
        result = await self.client.post("account/getByTag", {"tag": tag})
        return Q2Account.from_helix(_unwrap_account(result))

    async def list_by_customer(self, customer_id: int) -> list[Q2Account]:
        result = await self.client.post("account/list", {"customerId": customer_id})
        items = _unwrap_account_list(result)
        return [Q2Account.from_helix(item) for item in items]

    async def close(self, account_id: int) -> Q2Account:
        result = await self.client.post("account/close", {"accountId": account_id})
        return Q2Account.from_helix(_unwrap_account(result))

    async def lock(self, account_id: int) -> Q2Account:
        result = await self.client.post("account/lock", {"accountId": account_id})
        return Q2Account.from_helix(_unwrap_account(result))

    async def unlock(self, account_id: int) -> Q2Account:
        result = await self.client.post("account/unlock", {"accountId": account_id})
        return Q2Account.from_helix(_unwrap_account(result))

    async def update_limit(self, account_id: int, data: AccountUpdateLimitRequest) -> Any:
        return await self.client.post("account/updateLimit", data.to_helix_payload(account_id))

    async def create_stop_pay(self, account_id: int, data: StopPayRequest) -> Any:
        payload = {"accountId": account_id, **data.model_dump(exclude_none=True)}
        return await self.client.post("stopPay/create", payload)

    async def list_stop_pay(self, account_id: int) -> list[Any]:
        result = await self.client.post("stopPay/list", {"accountId": account_id})
        if isinstance(result, dict):
            items = result.get("stopPays") or result.get("stopPayList") or []
            return items if isinstance(items, list) else []
        return result if isinstance(result, list) else []

    async def cancel_stop_pay(self, stop_pay_id: int) -> Any:
        return await self.client.post("stopPay/cancel", {"stopPayId": stop_pay_id})


def _unwrap_account(result: Any) -> Any:
    if isinstance(result, dict) and "account" in result and isinstance(result["account"], dict):
        return result["account"]
    return result


def _unwrap_account_list(result: Any) -> list[Any]:
    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        items = result.get("accounts") or result.get("accountList") or []
        return items if isinstance(items, list) else []
    return []
