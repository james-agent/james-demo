"""Q2 Helix environment configuration (owned by q2-authentication)."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os


REQUIRED_ENV_KEYS = (
    "Q2_HELIX_API_URL",
    "Q2_HELIX_API_KEY",
    "Q2_HELIX_API_SECRET",
    "Q2_HELIX_PROGRAM_ID",
)


@dataclass(frozen=True)
class Q2Config:
    """Immutable Helix connection settings loaded from the environment."""

    api_url: str
    api_key: str
    api_secret: str
    program_id: str
    environment: str
    product_id: str
    mock_mode: bool
    allow_placeholder_pii: bool
    timeout_seconds: float

    @property
    def missing_keys(self) -> list[str]:
        missing: list[str] = []
        if not self.api_url:
            missing.append("Q2_HELIX_API_URL")
        if not self.api_key:
            missing.append("Q2_HELIX_API_KEY")
        if not self.api_secret:
            missing.append("Q2_HELIX_API_SECRET")
        if not self.program_id:
            missing.append("Q2_HELIX_PROGRAM_ID")
        return missing

    @property
    def is_configured(self) -> bool:
        return not self.missing_keys or self.mock_mode


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


def _env_bool(name: str, default: bool = False) -> bool:
    raw = _env(name, "true" if default else "false").lower()
    return raw in {"1", "true", "yes", "on"}


def load_q2_config() -> Q2Config:
    """Load Helix settings without caching (gate checks need fresh values)."""
    environment = _env("Q2_ENVIRONMENT", "sandbox").lower() or "sandbox"
    default_url = (
        "https://sandbox-api.helix.q2.com"
        if environment != "production"
        else "https://api.helix.q2.com"
    )
    return Q2Config(
        api_url=_env("Q2_HELIX_API_URL", default_url).rstrip("/"),
        api_key=_env("Q2_HELIX_API_KEY"),
        api_secret=_env("Q2_HELIX_API_SECRET"),
        program_id=_env("Q2_HELIX_PROGRAM_ID"),
        environment=environment,
        product_id=_env("Q2_HELIX_PRODUCT_ID", "1"),
        mock_mode=_env_bool("Q2_MOCK_MODE", False),
        allow_placeholder_pii=_env_bool("Q2_ALLOW_PLACEHOLDER_PII", True),
        timeout_seconds=float(_env("Q2_HELIX_TIMEOUT_SECONDS", "30") or "30"),
    )


@lru_cache
def get_q2_config() -> Q2Config:
    """Cached config for request handlers."""
    return load_q2_config()


def clear_q2_config_cache() -> None:
    get_q2_config.cache_clear()
