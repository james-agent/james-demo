"""Q2 Helix account lifecycle and stop-pay service."""

from __future__ import annotations

import logging
from typing import Any, Self

from james.ext.q2.client import HelixClient
from james.ext.q2.errors import Q2APIError
from james.ext.q2.models.account import (
    AccountCloseRequest,
    AccountCreateRequest,
    AccountLockRequest,
    StopPayCreateRequest,
)
from james.ext.q2.pii import mask_pii
from james.ext.q2.services import (
    helix_data,
    masked_data,
    raise_if_duplicate,
    summarize_account,
)

logger = logging.getLogger(__name__)


class AccountService:
    """Server-side account operations against Helix."""

    def __init__(self, client: HelixClient | None = None) -> None:
        self._client = client or HelixClient()
        self._owns_client = client is None

    def close_client(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        self.close_client()

    def create(self, data: AccountCreateRequest | dict[str, Any]) -> dict[str, Any]:
        body = data.model_dump(exclude_none=True) if isinstance(data, AccountCreateRequest) else dict(data)
        logger.info(
            "helix account create customerId=%s productId=%s tag=%s",
            body.get("customerId"),
            body.get("productId"),
            body.get("tag"),
        )
        try:
            payload = self._client.request("POST", "account/create", json_body=body)
        except Q2APIError as exc:
            raise_if_duplicate(exc)
        raw = helix_data(payload)
        if not isinstance(raw, dict):
            return {"data": mask_pii(raw)}
        return mask_pii({**summarize_account(raw), **raw})

    def get(self, customer_id: int, account_id: int) -> dict[str, Any]:
        payload = self._client.request(
            "POST",
            f"account/get/{customer_id}/{account_id}",
            json_body={},
        )
        raw = helix_data(payload)
        if not isinstance(raw, dict):
            return {"accountId": account_id, "customerId": customer_id, "data": mask_pii(raw)}
        return mask_pii({**summarize_account(raw), **raw})

    def list(self, customer_id: int) -> list[Any]:
        payload = self._client.request("POST", f"account/list/{customer_id}", json_body={})
        data = helix_data(payload)
        if isinstance(data, list):
            return [mask_pii({**summarize_account(item), **item} if isinstance(item, dict) else item) for item in data]
        if isinstance(data, dict):
            accounts = data.get("accounts") or data.get("results") or []
            if isinstance(accounts, list):
                return [
                    mask_pii({**summarize_account(item), **item} if isinstance(item, dict) else item)
                    for item in accounts
                ]
            return [mask_pii({**summarize_account(data), **data})]
        return []

    def close(self, data: AccountCloseRequest | dict[str, Any]) -> dict[str, Any]:
        body = data.model_dump(exclude_none=True) if isinstance(data, AccountCloseRequest) else dict(data)
        logger.info(
            "helix account close customerId=%s accountId=%s",
            body.get("customerId"),
            body.get("accountId"),
        )
        payload = self._client.request("POST", "account/close", json_body=body)
        raw = helix_data(payload)
        if not isinstance(raw, dict):
            return {"data": mask_pii(raw)}
        return mask_pii({**summarize_account(raw), **raw})

    def lock(self, data: AccountLockRequest | dict[str, Any]) -> dict[str, Any]:
        body = data.model_dump(exclude_none=True) if isinstance(data, AccountLockRequest) else dict(data)
        logger.info(
            "helix account lock customerId=%s accountId=%s reason=%s",
            body.get("customerId"),
            body.get("accountId"),
            body.get("lockReasonTypeCode"),
        )
        payload = self._client.request("POST", "account/lock", json_body=body)
        raw = helix_data(payload)
        if not isinstance(raw, dict):
            return {"data": mask_pii(raw)}
        return mask_pii({**summarize_account(raw), **raw})

    def unlock(self, customer_id: int, account_id: int) -> dict[str, Any]:
        body = {"customerId": customer_id, "accountId": account_id}
        logger.info("helix account unlock customerId=%s accountId=%s", customer_id, account_id)
        payload = self._client.request("POST", "account/unlock", json_body=body)
        raw = helix_data(payload)
        if not isinstance(raw, dict):
            return {"data": mask_pii(raw)}
        return mask_pii({**summarize_account(raw), **raw})

    def create_stop_pay(self, data: StopPayCreateRequest | dict[str, Any]) -> dict[str, Any]:
        body = data.model_dump(exclude_none=True) if isinstance(data, StopPayCreateRequest) else dict(data)
        payment_type = str(body.get("paymentType") or "Check")
        if payment_type == "ACH":
            path = "account/stopPay/createAchStopPay"
        else:
            path = "account/stopPay/createCheckStopPay"
        logger.info(
            "helix stopPay create type=%s customerId=%s accountId=%s",
            payment_type,
            body.get("customerId"),
            body.get("accountId"),
        )
        payload = self._client.request("POST", path, json_body=body)
        return masked_data(payload) if isinstance(helix_data(payload), dict) else {"data": masked_data(payload)}

    def list_stop_pays(
        self,
        customer_id: int,
        account_id: int,
        *,
        begin_date: str | None = None,
        end_date: str | None = None,
    ) -> list[Any] | dict[str, Any]:
        body: dict[str, Any] = {"customerId": customer_id, "accountId": account_id}
        if begin_date:
            body["beginDate"] = begin_date
        if end_date:
            body["endDate"] = end_date
        payload = self._client.request(
            "POST",
            f"account/stopPay/list/{customer_id}/{account_id}",
            json_body=body,
        )
        return mask_pii(helix_data(payload))

    def cancel_stop_pay(self, customer_id: int, account_id: int, stop_pay_id: int) -> dict[str, Any]:
        """Expire/cancel a stop pay (Helix: /account/stopPay/expire)."""
        body = {
            "customerId": customer_id,
            "accountId": account_id,
            "stopPayId": stop_pay_id,
        }
        logger.info(
            "helix stopPay expire customerId=%s accountId=%s stopPayId=%s",
            customer_id,
            account_id,
            stop_pay_id,
        )
        payload = self._client.request("POST", "account/stopPay/expire", json_body=body)
        return masked_data(payload) if isinstance(helix_data(payload), dict) else {"data": masked_data(payload)}
