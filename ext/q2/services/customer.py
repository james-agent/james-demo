"""Q2 Helix customer lifecycle service.

Uses ``get_helix_client()`` only — never recreates Basic Auth or base URLs.
"""

from __future__ import annotations

from typing import Any

from ext.q2.client import HelixClient, get_helix_client
from ext.q2.models.customer import (
    CustomerBeneficiary,
    CustomerOnboardRequest,
    CustomerUpdateRequest,
    Q2Customer,
)
from ext.q2.services._helpers import extract_data, mask_pii, safe_log_payload


class CustomerService:
    """Customer onboard / get / update / archive / lock / beneficiaries."""

    def __init__(self, client: HelixClient | None = None) -> None:
        self._owns_client = client is None
        self.client = client or get_helix_client()

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def __enter__(self) -> CustomerService:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def onboard(self, data: CustomerOnboardRequest | dict[str, Any]) -> dict[str, Any]:
        body = data.model_dump(exclude_none=True) if isinstance(data, CustomerOnboardRequest) else dict(data)
        safe_log_payload("customer_onboard", body)
        raw = self.client.request("POST", "customer/onboard", body=body)
        return mask_pii(extract_data(raw))

    def get(self, customer_id: int) -> dict[str, Any]:
        raw = self.client.request("POST", "customer/get", body={"customerId": customer_id})
        return mask_pii(extract_data(raw))

    def get_by_tag(self, tag: str) -> dict[str, Any]:
        raw = self.client.request("POST", "customer/getByTag", body={"tag": tag})
        return mask_pii(extract_data(raw))

    def update(self, customer_id: int, data: CustomerUpdateRequest | dict[str, Any]) -> dict[str, Any]:
        body = data.model_dump(exclude_none=True) if isinstance(data, CustomerUpdateRequest) else dict(data)
        body["customerId"] = customer_id
        safe_log_payload("customer_update", body)
        raw = self.client.request("POST", "customer/update", body=body)
        return mask_pii(extract_data(raw))

    def archive(self, customer_id: int) -> dict[str, Any]:
        raw = self.client.request("POST", "customer/archive", body={"customerId": customer_id})
        return mask_pii(extract_data(raw))

    def lock(self, customer_id: int, reason: str) -> dict[str, Any]:
        body = {"customerId": customer_id, "reason": reason}
        safe_log_payload("customer_lock", body)
        raw = self.client.request("POST", "customer/lock", body=body)
        return mask_pii(extract_data(raw))

    def unlock(self, customer_id: int) -> dict[str, Any]:
        raw = self.client.request("POST", "customer/unlock", body={"customerId": customer_id})
        return mask_pii(extract_data(raw))

    def list_beneficiaries(self, customer_id: int) -> Any:
        raw = self.client.request("POST", "customerBeneficiary/list", body={"customerId": customer_id})
        return mask_pii(extract_data(raw))

    def add_beneficiary(
        self,
        customer_id: int,
        data: CustomerBeneficiary | dict[str, Any],
    ) -> dict[str, Any]:
        body = data.model_dump(exclude_none=True) if isinstance(data, CustomerBeneficiary) else dict(data)
        body["customerId"] = customer_id
        safe_log_payload("customer_beneficiary_create", body)
        raw = self.client.request("POST", "customerBeneficiary/create", body=body)
        return mask_pii(extract_data(raw))

    def to_model(self, payload: dict[str, Any]) -> Q2Customer:
        data = extract_data(payload) if "customerId" not in payload else payload
        if not isinstance(data, dict):
            return Q2Customer(raw={"value": data})
        return Q2Customer(**{k: v for k, v in data.items() if k in Q2Customer.model_fields}, raw=data)
