"""PII masking helpers for Q2 Helix payloads (logs and API responses)."""

from __future__ import annotations

from typing import Any

_SENSITIVE_KEYS = {
    "taxid",
    "tax_id",
    "ssn",
    "ein",
    "itin",
    "driverslicensenumber",
    "passportnumber",
    "foreigndocumentnumber",
    "accountnumber",
    "accountnumbermasked",
    "customerToken".lower(),
    "customertoken",
}


def mask_value(key: str, value: Any) -> Any:
    """Mask a single sensitive scalar; leave non-PII values unchanged."""
    if value is None:
        return None
    key_l = key.replace("_", "").lower()
    if key_l in {"email", "emailaddress"} and isinstance(value, str) and "@" in value:
        local, _, domain = value.partition("@")
        keep = local[:1] if local else ""
        return f"{keep}***@{domain}"
    if key_l in {"number", "phone", "phonenumber"} and isinstance(value, str) and len(value) >= 4:
        return f"***{value[-4:]}"
    if key_l in _SENSITIVE_KEYS or key_l.endswith("taxid"):
        text = str(value)
        if len(text) <= 4:
            return "****"
        return f"****{text[-4:]}"
    return value


def mask_pii(payload: Any) -> Any:
    """Recursively mask known PII fields in dict/list structures."""
    if isinstance(payload, list):
        return [mask_pii(item) for item in payload]
    if not isinstance(payload, dict):
        return payload
    out: dict[str, Any] = {}
    for key, value in payload.items():
        if isinstance(value, (dict, list)):
            out[key] = mask_pii(value)
        else:
            out[key] = mask_value(key, value)
    return out
