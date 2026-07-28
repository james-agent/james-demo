"""Helix customer adapter."""

from __future__ import annotations

from typing import Any

from ext.q2.client import HelixClient
from ext.q2.errors import Q2NotFoundError


class CustomerService:
    def __init__(self, client: HelixClient) -> None:
        self.client = client

    def onboard(self, data: dict[str, Any]) -> dict[str, Any]:
        if self.client.config.mock_mode:
            tag = data.get("tag") or "unknown"
            return {
                "status": 0,
                "message": "Success",
                "data": {
                    "customerId": abs(hash(tag)) % 10_000_000,
                    "tag": tag,
                    "status": "Active",
                    "kycStatus": "Verified",
                    "emailAddress": data.get("emailAddress"),
                },
            }
        return self.client.post("customer/onboard", data)

    def get(self, customer_id: str | int) -> dict[str, Any]:
        if self.client.config.mock_mode:
            return {
                "status": 0,
                "message": "Success",
                "data": {"customerId": customer_id, "status": "Active", "kycStatus": "Verified"},
            }
        return self.client.post("customer/get", {"customerId": customer_id})

    def get_by_tag(self, tag: str) -> dict[str, Any]:
        if self.client.config.mock_mode:
            # Mock store is ephemeral; treat missing as not found unless caller already mapped.
            raise Q2NotFoundError(f"Mock customer not found for tag={tag}")
        try:
            return self.client.post("customer/getByTag", {"tag": tag})
        except Q2NotFoundError:
            raise
        except Exception as exc:
            # Some Helix programs return business status instead of HTTP 404.
            message = str(exc).lower()
            if "not found" in message or "404" in message:
                raise Q2NotFoundError(f"Customer not found for tag={tag}") from exc
            raise

    def update(self, customer_id: str | int, data: dict[str, Any]) -> dict[str, Any]:
        payload = {"customerId": customer_id, **data}
        if self.client.config.mock_mode:
            return {"status": 0, "message": "Success", "data": payload}
        return self.client.post("customer/update", payload)

    def archive(self, customer_id: str | int) -> dict[str, Any]:
        if self.client.config.mock_mode:
            return {"status": 0, "message": "Success", "data": {"customerId": customer_id, "status": "Archived"}}
        return self.client.post("customer/archive", {"customerId": customer_id})

    def lock(self, customer_id: str | int, reason: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"customerId": customer_id}
        if reason:
            payload["reason"] = reason
        if self.client.config.mock_mode:
            return {"status": 0, "message": "Success", "data": {**payload, "isLocked": True}}
        return self.client.post("customer/lock", payload)

    def unlock(self, customer_id: str | int) -> dict[str, Any]:
        if self.client.config.mock_mode:
            return {"status": 0, "message": "Success", "data": {"customerId": customer_id, "isLocked": False}}
        return self.client.post("customer/unlock", {"customerId": customer_id})
