"""Shared FastAPI helpers for Q2 Helix routes."""

from __future__ import annotations

from fastapi import HTTPException

from crm_api.ext.q2.client import Q2HelixError


def raise_q2_http_error(exc: Q2HelixError) -> None:
    status = exc.status_code or 502
    if status == 503:
        detail = exc.message
    elif status == 401:
        detail = "Q2 Helix authentication failed"
    elif status == 403:
        detail = "Q2 Helix access forbidden (check IP whitelist)"
    elif status == 404:
        detail = "Q2 resource not found"
    elif status == 409:
        detail = "Duplicate tag conflict"
    else:
        detail = exc.message or "Q2 Helix request failed"
    raise HTTPException(status_code=status, detail=detail) from exc
