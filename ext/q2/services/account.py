"""Q2 Helix account lifecycle service.

Uses ``get_helix_client()`` only — never recreates Basic Auth or base URLs.
"""

from __future__ import annotations

import logging
from typing import Any

from ext.q2.client import HelixClient, get_helix_client
from ext.q2.models.account import (
    AccountCreateRequest,
    AccountUpdateLimitRequest,
    Q2Account,
    StopPayRequest,
)
from ext.q2.services._helpers import extract_data, mask_pii, safe_log_payload

logger = logging.getLogger(__name__)


class AccountService:
    """Account create / get / list / close / lock / stop-pay operations."""

    def __init__(self, client: HelixClient | None = None) -> None:
        self._owns_client = client is None
        self.client = client or get_helix_client()

    def close_client(self) -> None:
        if self._owns_client:
            self.client.close()

    def __enter__(self) -> AccountService:
        return self

    def __exit__(self, *args: object) -> None:
        self.close_client()

    def create(self, data: AccountCreateRequest | dict[str, Any]) -> dict[str, Any]:
        body = data.model_dump(exclude_none=True) if isinstance(data, AccountCreateRequest) else dict(data)
        safe_log_payload("account_create", body)
        raw = self.client.request("POST", "account/create", body=body)
        return mask_pii(extract_data(raw))

    def get(self, account_id: int) -> dict[str, Any]:
        raw = self.client.request("POST", "account/get", body={"accountId": account_id})
        return mask_pii(extract_data(raw))

    def get_by_tag(self, tag: str) -> dict[str, Any]:
        raw = self.client.request("POST", "account/getByTag", body={"tag": tag})
        return mask_pii(extract_data(raw))

    def list_by_customer(self, customer_id: int) -> Any:
        raw = self.client.request("POST", "account/list", body={"customerId": customer_id})
        data = extract_data(raw)
        return mask_pii(data)

    def close(self, account_id: int) -> dict[str, Any]:
        logger.info("q2_account_close accountId=%s", account_id)
        raw = self.client.request("POST", "account/close", body={"accountId": account_id})
        return mask_pii(extract_data(raw))

    def lock(self, account_id: int) -> dict[str, Any]:
        logger.info("q2_account_lock accountId=%s", account_id)
        raw = self.client.request("POST", "account/lock", body={"accountId": account_id})
        return mask_pii(extract_data(raw))

    def unlock(self, account_id: int) -> dict[str, Any]:
        logger.info("q2_account_unlock accountId=%s", account_id)
        raw = self.client.request("POST", "account/unlock", body={"accountId": account_id})
        return mask_pii(extract_data(raw))

    def update_limit(
        self,
        account_id: int,
        data: AccountUpdateLimitRequest | dict[str, Any],
    ) -> dict[str, Any]:
        body = data.model_dump(exclude_none=True) if isinstance(data, AccountUpdateLimitRequest) else dict(data)
        body["accountId"] = account_id
        safe_log_payload("account_update_limit", body)
        raw = self.client.request("POST", "account/updateLimit", body=body)
        return mask_pii(extract_data(raw))

    def create_stop_pay(
        self,
        account_id: int,
        data: StopPayRequest | dict[str, Any],
    ) -> dict[str, Any]:
        body = data.model_dump(exclude_none=True) if isinstance(data, StopPayRequest) else dict(data)
        body["accountId"] = account_id
        safe_log_payload("stop_pay_create", body)
        raw = self.client.request("POST", "stopPay/create", body=body)
        return mask_pii(extract_data(raw))

    def list_stop_pay(self, account_id: int) -> Any:
        raw = self.client.request("POST", "stopPay/list", body={"accountId": account_id})
        return mask_pii(extract_data(raw))

    def cancel_stop_pay(self, stop_pay_id: int) -> dict[str, Any]:
        logger.info("q2_stop_pay_cancel stopPayId=%s", stop_pay_id)
        raw = self.client.request("POST", "stopPay/cancel", body={"stopPayId": stop_pay_id})
        return mask_pii(extract_data(raw))

    def to_model(self, payload: dict[str, Any]) -> Q2Account:
        data = extract_data(payload) if "accountId" not in payload else payload
        if not isinstance(data, dict):
            return Q2Account(raw={"value": data})
        return Q2Account(**{k: v for k, v in data.items() if k in Q2Account.model_fields}, raw=data)
