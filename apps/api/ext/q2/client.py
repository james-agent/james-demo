"""HTTP client for Q2 Helix API."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from ext.q2.config import Q2Config, get_q2_config
from ext.q2.exceptions import Q2ApiError, Q2DuplicateTagError

logger = logging.getLogger(__name__)


def mask_pii(value: str | None) -> str:
    """Mask email/phone-like strings for safe logging."""
    if not value:
        return "<empty>"
    text = str(value)
    if "@" in text:
        local, _, domain = text.partition("@")
        masked_local = local[:1] + "***" if local else "***"
        return f"{masked_local}@{domain}"
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) >= 4:
        return f"***{digits[-4:]}"
    return "***"


class Q2HelixClient:
    """Q2 Helix REST client using HTTP Basic Auth."""

    def __init__(
        self, config: Q2Config | None = None, *, timeout: float = 30.0
    ) -> None:
        self.config = config or get_q2_config()
        self._timeout = timeout

    def _auth(self) -> tuple[str, str]:
        return (self.config.api_key, self.config.api_secret)

    def _url(self, path: str) -> str:
        normalized = path if path.startswith("/") else f"/{path}"
        return f"{self.config.base_url}{normalized}"

    def post(self, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = body or {}
        url = self._url(path)
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(
                    url,
                    json=payload,
                    auth=self._auth(),
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    },
                )
        except httpx.RequestError as exc:
            raise Q2ApiError(f"Q2 request failed: {exc}") from exc

        if response.status_code == 409:
            raise Q2DuplicateTagError(
                "Q2 duplicate tag conflict",
                status_code=409,
                code="DUPLICATE_TAG",
            )

        if response.status_code in {401, 403}:
            raise Q2ApiError(
                "Q2 authentication failed",
                status_code=response.status_code,
                code="AUTH_ERROR",
            )

        if response.status_code >= 400:
            detail = response.text[:500]
            raise Q2ApiError(
                f"Q2 API error ({response.status_code}): {detail}",
                status_code=response.status_code,
            )

        if not response.content:
            return {}
        return response.json()

    def get_program(self) -> dict[str, Any]:
        return self.post("/program/get", {"programId": self.config.program_id})

    def test_connectivity(self) -> dict[str, Any]:
        self.config.require_configured()
        return self.get_program()
