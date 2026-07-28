"""Q2 Helix HTTP client — Basic Auth, connection pooling, safe error handling.

Middleware-only: never call Helix from browser/frontend code.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from ext.q2.config import Q2Config, get_q2_config

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30.0
MAX_CONNECTIONS = 20
MAX_KEEPALIVE = 10


class HelixAPIError(Exception):
    """Raised when the Helix API returns a non-success response."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        classification: str = "API_BUSINESS_ERROR",
        payload: Any = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.classification = classification
        self.payload = payload


def _classify_status(status_code: int) -> str:
    if status_code in {401, 403}:
        return "CONFIG_ERROR"
    if status_code in {404, 405, 429, 500, 502, 503, 504}:
        return "API_BUSINESS_ERROR"
    if 400 <= status_code < 500:
        return "API_BUSINESS_ERROR"
    if status_code >= 500:
        return "API_BUSINESS_ERROR"
    return "API_BUSINESS_ERROR"


def _safe_body_snippet(response: httpx.Response) -> Any:
    """Parse JSON when possible; never include Authorization material."""
    try:
        return response.json()
    except Exception:
        text = response.text[:500] if response.text else ""
        return {"raw": text}


class HelixClient:
    """Synchronous Helix client with HTTP Basic Auth and connection pooling."""

    def __init__(self, config: Q2Config | None = None, *, timeout: float = DEFAULT_TIMEOUT) -> None:
        self.config = config or get_q2_config()
        limits = httpx.Limits(
            max_connections=MAX_CONNECTIONS,
            max_keepalive_connections=MAX_KEEPALIVE,
        )
        self._client = httpx.Client(
            base_url=self.config.api_url.rstrip("/"),
            auth=(self.config.api_key, self.config.api_secret),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=timeout,
            limits=limits,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> HelixClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def request(
        self,
        method: str,
        relative_path: str,
        body: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Facade for Helix HTTP I/O using base URL + relative path only.

        Downstream services must call this (or the typed helpers) instead of
        recreating Basic Auth or absolute Helix URLs.
        """
        url_path = relative_path if relative_path.startswith("/") else f"/{relative_path}"
        logger.info(
            "helix_request method=%s path=%s environment=%s",
            method,
            url_path,
            self.config.environment,
        )
        request_kwargs = dict(kwargs)
        if body is not None:
            request_kwargs["json"] = body
        try:
            response = self._client.request(method, url_path, **request_kwargs)
        except httpx.TimeoutException as exc:
            raise HelixAPIError(
                "Helix request timed out — check network/firewall and API URL",
                status_code=None,
                classification="CONFIG_ERROR",
            ) from exc
        except httpx.RequestError as exc:
            raise HelixAPIError(
                f"Helix connection failed: {exc.__class__.__name__}",
                status_code=None,
                classification="CONFIG_ERROR",
            ) from exc

        if response.status_code == 401:
            raise HelixAPIError(
                "Authentication failed (401) — verify Q2_HELIX_API_KEY and Q2_HELIX_API_SECRET",
                status_code=401,
                classification="CONFIG_ERROR",
                payload=_safe_body_snippet(response),
            )
        if response.status_code == 403:
            raise HelixAPIError(
                "Forbidden (403) — production requires IP whitelisting; "
                "sandbox and production whitelists differ. Contact Q2 to whitelist this host.",
                status_code=403,
                classification="CONFIG_ERROR",
                payload=_safe_body_snippet(response),
            )
        if response.status_code == 404:
            raise HelixAPIError(
                "Not found (404) — endpoint or resource missing",
                status_code=404,
                classification="API_BUSINESS_ERROR",
                payload=_safe_body_snippet(response),
            )
        if response.status_code == 429:
            raise HelixAPIError(
                "Rate limit exceeded (429) — back off and retry; see Helix rate-limit guidance",
                status_code=429,
                classification="API_BUSINESS_ERROR",
                payload=_safe_body_snippet(response),
            )
        if response.status_code >= 500:
            raise HelixAPIError(
                f"Helix server error ({response.status_code})",
                status_code=response.status_code,
                classification="API_BUSINESS_ERROR",
                payload=_safe_body_snippet(response),
            )
        if response.status_code >= 400:
            raise HelixAPIError(
                f"Helix request failed ({response.status_code})",
                status_code=response.status_code,
                classification=_classify_status(response.status_code),
                payload=_safe_body_snippet(response),
            )

        if not response.content:
            return {}
        try:
            return response.json()
        except Exception:
            return {"raw": response.text[:500]}

    def test_connectivity(self) -> dict[str, Any]:
        """Official Test Connectivity flow: GET base URL with Basic Auth.

        Success returns a JSON welcome payload.
        See https://docs.helix.q2.com/reference/test-connectivity
        """
        return self.request("GET", "/")

    def get_program(self, program_id: str | None = None) -> dict[str, Any]:
        """Call ``/program/get`` to confirm program configuration and products."""
        pid = program_id or self.config.program_id
        body: dict[str, Any] = {}
        if pid:
            body["programId"] = pid
        return self.request("POST", "/program/get", body=body or None)

    def discover_products(self, program_payload: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Extract product list from a ``/program/get`` response without logging secrets."""
        payload = program_payload if program_payload is not None else self.get_program()
        data = payload.get("data", payload) if isinstance(payload, dict) else {}
        products = data.get("products") or data.get("Products") or []
        if isinstance(products, list):
            return [p for p in products if isinstance(p, dict)]
        return []


def get_helix_client(config: Q2Config | None = None, *, timeout: float = DEFAULT_TIMEOUT) -> HelixClient:
    """Factory for a configured Helix client (no global mutable singleton)."""
    return HelixClient(config=config, timeout=timeout)
