"""HTTP error mapping for Q2 customer/account routes."""

from __future__ import annotations

from fastapi import HTTPException

from james.ext.q2.errors import Q2APIError, Q2ConfigError, Q2ConnectivityError


def raise_q2_http(exc: Exception) -> None:
    """Convert Q2 errors into FastAPI HTTPException (never re-raise secrets)."""
    if isinstance(exc, Q2ConfigError):
        raise HTTPException(
            status_code=400,
            detail={"result": "CONFIG_ERROR", "message": exc.message, "code": exc.code},
        ) from exc
    if isinstance(exc, Q2ConnectivityError):
        raise HTTPException(
            status_code=503,
            detail={"result": "API_BUSINESS_ERROR", "message": exc.message, "code": exc.code},
        ) from exc
    if isinstance(exc, Q2APIError):
        if exc.code == "DUPLICATE":
            raise HTTPException(
                status_code=409,
                detail={"result": "DUPLICATE", "message": exc.message, "code": exc.code},
            ) from exc
        status = 404 if exc.code == "NOT_FOUND" else 502
        if exc.http_status == 401 or exc.http_status == 403:
            status = 502
        elif exc.http_status == 404:
            status = 404
        raise HTTPException(
            status_code=status,
            detail={
                "result": "API_BUSINESS_ERROR",
                "message": exc.message,
                "code": exc.code,
                "http_status": exc.http_status,
            },
        ) from exc
    raise exc
