"""Helix account adapter."""

from __future__ import annotations

from typing import Any

from ext.q2.client import HelixClient
from ext.q2.errors import Q2NotFoundError


class AccountService:
    def __init__(self, client: HelixClient) -> None:
        self.client = client

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        if self.client.config.mock_mode:
            tag = data.get("tag") or "unknown"
            return {
                "status": 0,
                "message": "Success",
                "data": {
                    "accountId": abs(hash(f"acct-{tag}")) % 10_000_000,
                    "customerId": data.get("customerId"),
                    "productId": data.get("productId"),
                    "name": data.get("name") or "Primary Checking",
                    "tag": tag,
                    "status": "Open",
                    "type": "Checking",
                    "accountNumber": "****0000",
                    "isLocked": False,
                },
            }
        return self.client.post("account/create", data)

    def get(self, account_id: str | int) -> dict[str, Any]:
        if self.client.config.mock_mode:
            return {
                "status": 0,
                "message": "Success",
                "data": {"accountId": account_id, "status": "Open", "accountNumber": "****0000"},
            }
        return self.client.post("account/get", {"accountId": account_id})

    def get_by_tag(self, tag: str) -> dict[str, Any]:
        if self.client.config.mock_mode:
            raise Q2NotFoundError(f"Mock account not found for tag={tag}")
        try:
            return self.client.post("account/getByTag", {"tag": tag})
        except Q2NotFoundError:
            raise
        except Exception as exc:
            message = str(exc).lower()
            if "not found" in message or "404" in message:
                raise Q2NotFoundError(f"Account not found for tag={tag}") from exc
            raise

    def list_by_customer(self, customer_id: str | int) -> dict[str, Any]:
        if self.client.config.mock_mode:
            return {"status": 0, "message": "Success", "data": {"accounts": []}}
        return self.client.post("account/list", {"customerId": customer_id})

    def close(self, account_id: str | int) -> dict[str, Any]:
        if self.client.config.mock_mode:
            return {"status": 0, "message": "Success", "data": {"accountId": account_id, "status": "Closed"}}
        return self.client.post("account/close", {"accountId": account_id})

    def lock(self, account_id: str | int) -> dict[str, Any]:
        if self.client.config.mock_mode:
            return {"status": 0, "message": "Success", "data": {"accountId": account_id, "isLocked": True}}
        return self.client.post("account/lock", {"accountId": account_id})

    def unlock(self, account_id: str | int) -> dict[str, Any]:
        if self.client.config.mock_mode:
            return {"status": 0, "message": "Success", "data": {"accountId": account_id, "isLocked": False}}
        return self.client.post("account/unlock", {"accountId": account_id})
