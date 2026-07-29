"""Q2 Helix HTTP client errors and classification helpers."""

from __future__ import annotations

from typing import Any


class Q2Error(Exception):
    """Base Helix integration error."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "API_BUSINESS_ERROR",
        http_status: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.http_status = http_status
        self.details = details or {}


class Q2ConfigError(Q2Error):
    def __init__(self, message: str, *, missing_keys: list[str] | None = None) -> None:
        super().__init__(
            message,
            code="CONFIG_ERROR",
            details={"missing_keys": missing_keys or []},
        )
        self.missing_keys = missing_keys or []


class Q2NotFoundError(Q2Error):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, code="NOT_FOUND", http_status=404)


class Q2ConflictError(Q2Error):
    def __init__(self, message: str = "Conflict") -> None:
        super().__init__(message, code="CONFLICT", http_status=409)


def classify_http_error(status_code: int, body_text: str) -> Q2Error:
    """Map Helix HTTP failures to operator-safe error codes (no secrets)."""
    snippet = (body_text or "")[:300]
    if status_code == 401:
        return Q2Error(
            "Helix authentication failed (401). Verify Q2_HELIX_API_KEY / Q2_HELIX_API_SECRET.",
            code="AUTH_ERROR",
            http_status=401,
            details={"body": snippet},
        )
    if status_code == 403:
        return Q2Error(
            "Helix forbidden (403). Confirm IP allowlisting for this environment.",
            code="IP_ALLOWLIST_ERROR",
            http_status=403,
            details={"body": snippet},
        )
    if status_code == 404:
        return Q2NotFoundError(f"Helix resource not found: {snippet or '404'}")
    if status_code == 409:
        return Q2ConflictError(f"Helix conflict (duplicate tag?): {snippet or '409'}")
    if status_code >= 500:
        return Q2Error(
            f"Helix server error ({status_code}).",
            code="HELIX_SERVER_ERROR",
            http_status=status_code,
            details={"body": snippet},
        )
    return Q2Error(
        f"Helix request failed ({status_code}).",
        code="API_BUSINESS_ERROR",
        http_status=status_code,
        details={"body": snippet},
    )
