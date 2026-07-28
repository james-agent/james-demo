"""HTTP client for Q2 Helix API (owned by q2-authentication)."""

from __future__ import annotations

from typing import Any

import httpx

from crm_api.ext.q2.config import Q2Config, get_q2_config


class Q2HelixError(Exception):
    """Raised when Helix returns a non-success HTTP or business status."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        helix_status: int | None = None,
        payload: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.helix_status = helix_status
        self.payload = payload


class Q2HelixClient:
    """
    Server-side Helix client using HTTP Basic Auth and a shared connection pool.

    Paths are relative to ``config.base_url`` (no leading slash).
    """

    def __init__(
        self,
        config: Q2Config | None = None,
        *,
        client: httpx.AsyncClient | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.config = config or get_q2_config()
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            base_url=self.config.base_url,
            auth=(self.config.api_key, self.config.api_secret),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=timeout,
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> Q2HelixClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()

    async def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        if not self.config.is_configured:
            missing = ", ".join(self.config.missing_keys()) or "Q2 credentials"
            raise Q2HelixError(
                f"Q2 Helix is not configured. Missing: {missing}",
                status_code=503,
            )

        relative = path.lstrip("/")
        try:
            response = await self._client.request(method.upper(), relative, json=payload or {})
        except httpx.RequestError as exc:
            raise Q2HelixError(f"Q2 Helix connectivity error: {exc}", status_code=503) from exc

        body: Any
        try:
            body = response.json()
        except ValueError:
            body = {"raw": response.text}

        if response.status_code == 401:
            raise Q2HelixError("Q2 Helix authentication failed", status_code=401, payload=body)
        if response.status_code == 403:
            raise Q2HelixError(
                "Q2 Helix forbidden — IP may not be whitelisted for this environment",
                status_code=403,
                payload=body,
            )
        if response.status_code == 404:
            raise Q2HelixError("Q2 Helix resource not found", status_code=404, payload=body)
        if response.status_code == 409:
            raise Q2HelixError("Q2 Helix conflict (duplicate tag)", status_code=409, payload=body)
        if response.status_code == 429:
            raise Q2HelixError("Q2 Helix rate limited", status_code=429, payload=body)
        if response.status_code >= 500:
            raise Q2HelixError("Q2 Helix server error", status_code=response.status_code, payload=body)
        if response.status_code >= 400:
            message = _extract_message(body) or f"Q2 Helix request failed ({response.status_code})"
            raise Q2HelixError(message, status_code=response.status_code, payload=body)

        if isinstance(body, dict) and "status" in body:
            helix_status = body.get("status")
            if helix_status not in (0, "0", None):
                message = _extract_message(body) or "Q2 Helix business error"
                raise Q2HelixError(
                    message,
                    status_code=response.status_code,
                    helix_status=int(helix_status) if str(helix_status).isdigit() else None,
                    payload=body,
                )
            return body.get("data", body)

        return body

    async def post(self, path: str, payload: dict[str, Any] | None = None) -> Any:
        return await self.request("POST", path, payload)

    async def get_program(self) -> Any:
        payload: dict[str, Any] = {}
        if self.config.program_id:
            payload["programId"] = _as_int_or_str(self.config.program_id)
        return await self.post("program/get", payload)

    async def test_connectivity(self) -> Any:
        """Prefer program/get; fall back to base URL GET for welcome message."""
        try:
            return await self.get_program()
        except Q2HelixError as exc:
            if exc.status_code not in {404, 400}:
                raise
        response = await self._client.get("")
        try:
            return response.json()
        except ValueError as err:
            raise Q2HelixError(
                "Q2 Helix connectivity test returned non-JSON body",
                status_code=response.status_code,
                payload={"raw": response.text},
            ) from err


def _extract_message(body: Any) -> str | None:
    if not isinstance(body, dict):
        return None
    for key in ("message", "error", "detail"):
        value = body.get(key)
        if value:
            return str(value)
    return None


def _as_int_or_str(value: str) -> int | str:
    return int(value) if value.isdigit() else value
