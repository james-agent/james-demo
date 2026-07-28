"""Shared helpers for Q2 Helix domain services."""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

_PII_KEYS = frozenset(
    {
        "taxId",
        "ssn",
        "ein",
        "itin",
        "accountNumber",
        "fullAccountNumber",
        "cardNumber",
        "cvv",
    }
)


def extract_data(payload: Any) -> Any:
    """Unwrap Helix ``{status, message, data}`` envelopes when present."""
    if not isinstance(payload, dict):
        return payload
    if "data" in payload:
        return payload["data"]
    return payload


def mask_pii(value: Any) -> Any:
    """Recursively mask sensitive fields for logs and API responses."""
    if isinstance(value, dict):
        masked: dict[str, Any] = {}
        for key, item in value.items():
            if key in _PII_KEYS and item is not None:
                masked[key] = _mask_scalar(str(item))
            else:
                masked[key] = mask_pii(item)
        return masked
    if isinstance(value, list):
        return [mask_pii(item) for item in value]
    return value


def _mask_scalar(raw: str) -> str:
    digits = re.sub(r"\D", "", raw)
    if len(digits) >= 4:
        return f"****{digits[-4:]}"
    if raw:
        return "****"
    return raw


def safe_log_payload(action: str, payload: Any) -> None:
    """Log request/response metadata without raw PII."""
    logger.info("q2_%s payload=%s", action, mask_pii(payload))
