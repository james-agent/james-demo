"""FastAPI helpers shared by Q2 Helix route modules."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from ext.q2.client import HelixAPIError


def helix_http_error(exc: HelixAPIError) -> HTTPException:
    """Map HelixAPIError to a user-friendly HTTPException."""
    status = exc.status_code or 502
    if status == 409:
        detail = "Conflict — a resource with this tag already exists."
    elif status == 404:
        detail = "Resource not found in Helix."
    elif status in {401, 403}:
        detail = "Helix authentication or authorization failed. Check Q2 credentials and IP whitelist."
    elif status == 400:
        detail = _friendly_message(exc) or "Invalid request to Helix."
    elif status == 429:
        detail = "Helix rate limit exceeded. Please retry shortly."
    elif status >= 500:
        detail = "Helix is temporarily unavailable. Please try again later."
    else:
        detail = _friendly_message(exc) or "Helix request failed."
    return HTTPException(status_code=status if 400 <= status < 600 else 502, detail=detail)


def _friendly_message(exc: HelixAPIError) -> str | None:
    payload = exc.payload
    if isinstance(payload, dict):
        for key in ("message", "error", "detail"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        errors = payload.get("errors")
        if isinstance(errors, list) and errors:
            first = errors[0]
            if isinstance(first, str):
                return first
            if isinstance(first, dict):
                msg = first.get("message") or first.get("error")
                if isinstance(msg, str):
                    return msg
    message = str(exc).strip()
    return message or None


def as_json_response(payload: Any) -> Any:
    """Return payload suitable for FastAPI JSON responses."""
    return payload if payload is not None else {}
