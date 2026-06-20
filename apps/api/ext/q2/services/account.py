"""Q2 Helix account API service."""

from __future__ import annotations

import logging
from typing import Any

from ext.q2.client import Q2HelixClient
from ext.q2.exceptions import Q2ApiError, Q2DuplicateTagError
from ext.q2.models.account import Q2Account, Q2AccountListResponse

logger = logging.getLogger(__name__)


def _extract_account_payload(data: dict[str, Any]) -> Q2Account:
    body = data.get("data") if isinstance(data.get("data"), dict) else data
    return Q2Account(
        account_id=_str_or_none(body.get("accountId")),
        customer_id=_str_or_none(body.get("customerId")),
        product_id=_str_or_none(body.get("productId")),
        account_balance=body.get("accountBalance"),
        available_balance=body.get("availableBalance"),
        pending_balance=body.get("pendingBalance"),
        status=body.get("status"),
        type=body.get("type"),
        tag=body.get("tag"),
        routing_number=body.get("routingNumber"),
        account_number=body.get("accountNumber"),
        is_locked=body.get("isLocked"),
        name=body.get("name"),
        raw=body if isinstance(body, dict) else data,
    )


def _str_or_none(value: object) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text or None


class Q2AccountService:
    def __init__(self, client: Q2HelixClient | None = None) -> None:
        self.client = client or Q2HelixClient()

    def create(
        self,
        *,
        customer_id: str,
        product_id: str,
        name: str,
        tag: str,
    ) -> Q2Account:
        body = {
            "customerId": customer_id,
            "productId": product_id,
            "name": name,
            "tag": tag,
        }
        logger.info(
            "Creating Q2 account customer_id=%s product_id=%s tag=%s",
            customer_id,
            product_id,
            tag,
        )
        try:
            response = self.client.post("/account/create", body)
            return _extract_account_payload(response)
        except Q2DuplicateTagError:
            logger.info("Duplicate account tag %s — fetching existing account", tag)
            return self.get_by_tag(tag)

    def get(self, account_id: str) -> Q2Account:
        response = self.client.post("/account/get", {"accountId": account_id})
        return _extract_account_payload(response)

    def get_by_tag(self, tag: str) -> Q2Account:
        response = self.client.post("/account/getByTag", {"tag": tag})
        return _extract_account_payload(response)

    def safe_get_by_tag(self, tag: str) -> Q2Account | None:
        try:
            return self.get_by_tag(tag)
        except Q2ApiError as exc:
            if exc.status_code == 404:
                return None
            raise

    def list_by_customer(self, customer_id: str) -> Q2AccountListResponse:
        response = self.client.post("/account/list", {"customerId": customer_id})
        data = (
            response.get("data") if isinstance(response.get("data"), dict) else response
        )
        raw_accounts = data.get("accounts") if isinstance(data, dict) else []
        accounts = [
            _extract_account_payload(item)
            for item in raw_accounts
            if isinstance(item, dict)
        ]
        return Q2AccountListResponse(accounts=accounts)

    def close(self, account_id: str) -> Q2Account:
        response = self.client.post("/account/close", {"accountId": account_id})
        return _extract_account_payload(response)

    def lock(self, account_id: str) -> Q2Account:
        response = self.client.post("/account/lock", {"accountId": account_id})
        return _extract_account_payload(response)

    def unlock(self, account_id: str) -> Q2Account:
        response = self.client.post("/account/unlock", {"accountId": account_id})
        return _extract_account_payload(response)

    def update_limit(
        self,
        account_id: str,
        *,
        limit_amount: float | None = None,
        limit_type: str | None = None,
    ) -> Q2Account:
        body: dict[str, Any] = {"accountId": account_id}
        if limit_amount is not None:
            body["limitAmount"] = limit_amount
        if limit_type is not None:
            body["limitType"] = limit_type
        response = self.client.post("/account/updateLimit", body)
        return _extract_account_payload(response)

    def create_stop_pay(
        self,
        account_id: str,
        *,
        check_number: str | None = None,
        amount: float | None = None,
        payee: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"accountId": account_id}
        if check_number is not None:
            body["checkNumber"] = check_number
        if amount is not None:
            body["amount"] = amount
        if payee is not None:
            body["payee"] = payee
        return self.client.post("/stopPay/create", body)

    def list_stop_pay(self, account_id: str) -> dict[str, Any]:
        return self.client.post("/stopPay/list", {"accountId": account_id})

    def cancel_stop_pay(self, stop_pay_id: str) -> dict[str, Any]:
        return self.client.post("/stopPay/cancel", {"stopPayId": stop_pay_id})
