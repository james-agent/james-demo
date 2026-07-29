"""Shared FastAPI dependencies for Q2 operator routes."""

from __future__ import annotations

from collections.abc import Generator

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ext.q2.client import HelixClient
from ext.q2.config import Q2Config, load_q2_config
from ext.q2.db import get_db_session
from ext.q2.errors import Q2ConfigError, Q2Error, Q2NotFoundError

# Re-export for route modules.
get_session = get_db_session


def get_q2_config_dep() -> Q2Config:
    return load_q2_config()


def get_helix_client() -> Generator[HelixClient, None, None]:
    """Yield an authenticated Helix client and always close it."""
    client = HelixClient(load_q2_config())
    try:
        yield client
    finally:
        client.close()


def raise_q2_http(exc: Q2Error) -> None:
    """Map Helix/domain errors to operator-safe HTTPException detail."""
    if isinstance(exc, Q2ConfigError):
        raise HTTPException(
            status_code=503,
            detail={"code": exc.code, "message": exc.message, **exc.details},
        ) from exc
    if isinstance(exc, Q2NotFoundError):
        raise HTTPException(
            status_code=404,
            detail={"code": exc.code, "message": exc.message},
        ) from exc
    status = exc.http_status or 502
    if status < 400 or status > 599:
        status = 502
    raise HTTPException(
        status_code=status,
        detail={"code": exc.code, "message": exc.message},
    ) from exc


__all__ = [
    "Session",
    "get_helix_client",
    "get_q2_config_dep",
    "get_session",
    "raise_q2_http",
]
