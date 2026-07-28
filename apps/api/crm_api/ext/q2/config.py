"""Q2 Helix connection configuration (owned by q2-authentication)."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os


SANDBOX_BASE_URL = "https://sandbox-api.helix.q2.com"
PRODUCTION_BASE_URL = "https://api.helix.q2.com"

REQUIRED_ENV_KEYS = (
    "Q2_HELIX_API_URL",
    "Q2_HELIX_API_KEY",
    "Q2_HELIX_API_SECRET",
    "Q2_HELIX_PROGRAM_ID",
)


@dataclass(frozen=True)
class Q2Config:
    """Immutable Q2 Helix settings loaded from environment."""

    api_url: str
    api_key: str
    api_secret: str
    program_id: str
    environment: str

    @property
    def base_url(self) -> str:
        return self.api_url.rstrip("/")

    @property
    def is_configured(self) -> bool:
        return all(
            [
                bool(self.api_url.strip()),
                bool(self.api_key.strip()),
                bool(self.api_secret.strip()),
                bool(self.program_id.strip()),
            ]
        )

    def missing_keys(self) -> list[str]:
        mapping = {
            "Q2_HELIX_API_URL": self.api_url,
            "Q2_HELIX_API_KEY": self.api_key,
            "Q2_HELIX_API_SECRET": self.api_secret,
            "Q2_HELIX_PROGRAM_ID": self.program_id,
        }
        return [key for key, value in mapping.items() if not str(value or "").strip()]


def _env(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value is not None and str(value).strip() != "":
            return str(value).strip()
    return default


def get_q2_config() -> Q2Config:
    """
    Load Q2 Helix config from environment.

    Prefers ``Q2_HELIX_*`` names; falls back to legacy ``Q2_API_*`` / ``Q2_BASE_URL``.
    """
    environment = _env("Q2_ENVIRONMENT", default="sandbox").lower()
    default_url = PRODUCTION_BASE_URL if environment == "production" else SANDBOX_BASE_URL
    return Q2Config(
        api_url=_env("Q2_HELIX_API_URL", "Q2_BASE_URL", default=default_url),
        api_key=_env("Q2_HELIX_API_KEY", "Q2_API_KEY"),
        api_secret=_env("Q2_HELIX_API_SECRET", "Q2_API_SECRET"),
        program_id=_env("Q2_HELIX_PROGRAM_ID", "Q2_PROGRAM_ID"),
        environment=environment if environment in {"sandbox", "production"} else "sandbox",
    )


@lru_cache
def get_cached_q2_config() -> Q2Config:
    return get_q2_config()


def clear_q2_config_cache() -> None:
    get_cached_q2_config.cache_clear()
