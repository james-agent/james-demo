"""Q2 Helix customer API service."""

from __future__ import annotations

import logging
from typing import Any

from crm_api.models.customer import Customer
from ext.q2.client import Q2HelixClient, mask_pii
from ext.q2.exceptions import Q2ApiError, Q2DuplicateTagError
from ext.q2.models.customer import Q2CustomerResponse

logger = logging.getLogger(__name__)


def _extract_customer_payload(data: dict[str, Any]) -> Q2CustomerResponse:
    body = data.get("data") if isinstance(data.get("data"), dict) else data
    return Q2CustomerResponse(
        customer_id=str(body.get("customerId") or body.get("id") or "") or None,
        tag=body.get("tag"),
        kyc_status=body.get("kycStatus"),
        status=body.get("status"),
        raw=body if isinstance(body, dict) else data,
    )


def _build_onboard_body(customer: Customer, tag: str) -> dict[str, Any]:
    body: dict[str, Any] = {
        "tag": tag,
        "firstName": customer.first_name,
        "lastName": customer.last_name,
        "emailAddress": customer.email,
    }
    if customer.phone:
        body["phoneNumber"] = customer.phone
    if customer.date_of_birth:
        body["birthDate"] = customer.date_of_birth.isoformat()
    if customer.address_line1:
        body["addressLine1"] = customer.address_line1
    if customer.address_city:
        body["city"] = customer.address_city
    if customer.address_state:
        body["state"] = customer.address_state
    if customer.address_postal_code:
        body["postalCode"] = customer.address_postal_code
    return body


class Q2CustomerService:
    def __init__(self, client: Q2HelixClient | None = None) -> None:
        self.client = client or Q2HelixClient()

    def onboard(self, customer: Customer, tag: str) -> Q2CustomerResponse:
        body = _build_onboard_body(customer, tag)
        logger.info(
            "Onboarding customer tag=%s email=%s",
            tag,
            mask_pii(customer.email),
        )
        try:
            response = self.client.post("/customer/onboard", body)
            return _extract_customer_payload(response)
        except Q2DuplicateTagError:
            logger.info("Duplicate tag %s — fetching existing Q2 customer", tag)
            return self.get_by_tag(tag)

    def get(self, customer_id: str) -> Q2CustomerResponse:
        response = self.client.post("/customer/get", {"customerId": customer_id})
        return _extract_customer_payload(response)

    def get_by_tag(self, tag: str) -> Q2CustomerResponse:
        response = self.client.post("/customer/getByTag", {"tag": tag})
        return _extract_customer_payload(response)

    def safe_get_by_tag(self, tag: str) -> Q2CustomerResponse | None:
        try:
            return self.get_by_tag(tag)
        except Q2ApiError as exc:
            if exc.status_code == 404:
                return None
            raise
