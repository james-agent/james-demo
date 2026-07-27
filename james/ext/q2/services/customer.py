"""Q2 Helix customer lifecycle service."""

from __future__ import annotations

import logging
from typing import Any, Self

from james.ext.q2.client import HelixClient
from james.ext.q2.errors import Q2APIError
from james.ext.q2.models.customer import (
    CustomerOnboardRequest,
    CustomerUpdateRequest,
)
from james.ext.q2.pii import mask_pii
from james.ext.q2.services import (
    helix_data,
    masked_data,
    raise_if_duplicate,
    summarize_customer,
)

logger = logging.getLogger(__name__)


class CustomerService:
    """Server-side customer operations against Helix (never expose credentials)."""

    def __init__(self, client: HelixClient | None = None) -> None:
        self._client = client or HelixClient()
        self._owns_client = client is None

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def onboard(self, data: CustomerOnboardRequest | dict[str, Any]) -> dict[str, Any]:
        body = data.model_dump(exclude_none=True) if isinstance(data, CustomerOnboardRequest) else dict(data)
        logger.info(
            "helix customer onboard tag=%s isBusiness=%s",
            body.get("tag"),
            body.get("isBusiness"),
        )
        try:
            payload = self._client.request("POST", "customer/onboard", json_body=body)
        except Q2APIError as exc:
            raise_if_duplicate(exc)
        raw = helix_data(payload)
        if not isinstance(raw, dict):
            raw = {"result": raw}
        return mask_pii({**summarize_customer(raw), **{k: v for k, v in raw.items() if k not in summarize_customer(raw)}})

    def get(self, customer_id: int) -> dict[str, Any]:
        payload = self._client.request("POST", f"customer/get/{customer_id}", json_body={})
        raw = helix_data(payload)
        if not isinstance(raw, dict):
            return {"customerId": customer_id, "data": mask_pii(raw)}
        return mask_pii({**summarize_customer(raw), **raw})

    def get_by_tag(self, tag: str) -> dict[str, Any]:
        payload = self._client.request("POST", "customer/getByTag", json_body={"tag": tag})
        raw = helix_data(payload)
        if not isinstance(raw, dict):
            return {"tag": tag, "data": mask_pii(raw)}
        return mask_pii({**summarize_customer(raw), **raw})

    def update(self, customer_id: int, data: CustomerUpdateRequest | dict[str, Any]) -> dict[str, Any]:
        if isinstance(data, CustomerUpdateRequest):
            body = data.model_dump(exclude_none=True)
        else:
            body = dict(data)
        body["customerId"] = customer_id
        logger.info("helix customer update customerId=%s", customer_id)
        payload = self._client.request("POST", "customer/update", json_body=body)
        raw = helix_data(payload)
        if not isinstance(raw, dict):
            return {"customerId": customer_id, "data": mask_pii(raw)}
        return mask_pii({**summarize_customer(raw), **raw})

    def archive(self, customer_id: int, archive_reason: str = "Other") -> dict[str, Any]:
        body = {"customerId": customer_id, "archiveReason": archive_reason}
        logger.info("helix customer archive customerId=%s reason=%s", customer_id, archive_reason)
        payload = self._client.request("POST", "customer/archive", json_body=body)
        data = masked_data(payload)
        return data if isinstance(data, dict) else {"customerId": customer_id, "data": data}

    def lock(self, customer_id: int, reason: str) -> dict[str, Any]:
        body = {"customerId": customer_id, "reason": reason}
        logger.info("helix customer lock customerId=%s", customer_id)
        payload = self._client.request("POST", "customer/lock", json_body=body)
        data = masked_data(payload)
        return data if isinstance(data, dict) else {"customerId": customer_id, "data": data}

    def unlock(self, customer_id: int) -> dict[str, Any]:
        body = {"customerId": customer_id}
        logger.info("helix customer unlock customerId=%s", customer_id)
        payload = self._client.request("POST", "customer/unlock", json_body=body)
        data = masked_data(payload)
        return data if isinstance(data, dict) else {"customerId": customer_id, "data": data}

    def list_beneficiaries(self, customer_id: int) -> list[Any] | dict[str, Any]:
        payload = self._client.request(
            "POST",
            "customer/beneficiary/list",
            json_body={"customerId": customer_id},
        )
        data = helix_data(payload)
        return mask_pii(data)

    def add_beneficiary(self, customer_id: int, data: dict[str, Any]) -> dict[str, Any]:
        body = {**data, "customerId": customer_id}
        logger.info("helix customer add beneficiary customerId=%s", customer_id)
        payload = self._client.request("POST", "customer/beneficiary/create", json_body=body)
        return masked_data(payload) if isinstance(helix_data(payload), dict) else {"customerId": customer_id, "data": masked_data(payload)}
