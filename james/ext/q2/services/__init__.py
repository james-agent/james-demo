"""Shared helpers for Q2 Helix service layers."""

from __future__ import annotations

from typing import Any

from james.ext.q2.errors import Q2APIError
from james.ext.q2.pii import mask_pii

_DUPLICATE_HINTS = ("duplicate", "already exists", "tag already", "unique")


def helix_data(payload: dict[str, Any]) -> Any:
    """Return Helix ``data`` node when present, else the full payload."""
    if "data" in payload:
        return payload["data"]
    return payload


def masked_data(payload: dict[str, Any]) -> Any:
    return mask_pii(helix_data(payload))


def raise_if_duplicate(exc: Q2APIError) -> None:
    """Re-raise duplicate-tag conflicts with a stable code for HTTP 409 mapping."""
    message = (exc.message or "").lower()
    if any(hint in message for hint in _DUPLICATE_HINTS):
        raise Q2APIError(
            exc.message,
            code="DUPLICATE",
            http_status=exc.http_status or 409,
            helix_status=exc.helix_status,
        ) from exc
    raise exc


def summarize_account(raw: dict[str, Any]) -> dict[str, Any]:
    """Map common Helix account properties for API consumers."""
    return {
        "accountId": raw.get("accountId") or raw.get("account_id"),
        "customerId": raw.get("customerId") or raw.get("customer_id"),
        "name": raw.get("name"),
        "status": raw.get("status"),
        "accountStatus": raw.get("accountStatus") or raw.get("status"),
        "type": raw.get("type") or raw.get("accountType") or raw.get("productType"),
        "productId": raw.get("productId") or raw.get("product_id"),
        "tag": raw.get("tag"),
        "isLocked": raw.get("isLocked"),
        "lockTypeCode": raw.get("lockTypeCode"),
        "lockReasonTypeCode": raw.get("lockReasonTypeCode"),
        "availableBalance": raw.get("availableBalance"),
        "accountBalance": raw.get("accountBalance") or raw.get("balance"),
        "accountNumber": raw.get("accountNumber"),
        "routingNumber": raw.get("routingNumber"),
        "openedDate": raw.get("openedDate"),
        "closedDate": raw.get("closedDate"),
        "isCloseable": raw.get("isCloseable") if "isCloseable" in raw else raw.get("isclosable"),
    }


def summarize_customer(raw: dict[str, Any]) -> dict[str, Any]:
    """Map Helix customer properties including KYC / lock / business flags."""
    return {
        "customerId": raw.get("customerId") or raw.get("customer_id"),
        "tag": raw.get("tag"),
        "status": raw.get("status"),
        "kycStatus": raw.get("kycStatus") or raw.get("kyc_status"),
        "isBusiness": raw.get("isBusiness"),
        "isLocked": raw.get("isLocked"),
        "firstName": raw.get("firstName"),
        "lastName": raw.get("lastName"),
        "emailAddress": raw.get("emailAddress"),
        "birthDate": raw.get("birthDate"),
        "taxId": raw.get("taxId"),
        "taxIdType": raw.get("taxIdType"),
        "phones": raw.get("phones"),
        "addresses": raw.get("addresses"),
        "archivedDate": raw.get("archivedDate"),
    }
