"""Q2 Helix environment configuration (owned by q2-authentication)."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from james.ext.q2.errors import Q2ConfigError

_SANDBOX_URL = "https://sandbox-api.helix.q2.com"
_PRODUCTION_URL = "https://api.helix.q2.com"


class Q2Config(BaseSettings):
    """Helix credentials and optional Caliper/AMQP settings from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    q2_helix_api_url: str = Field(default="", alias="Q2_HELIX_API_URL")
    q2_helix_api_key: str = Field(default="", alias="Q2_HELIX_API_KEY")
    q2_helix_api_secret: str = Field(default="", alias="Q2_HELIX_API_SECRET")
    q2_helix_program_id: str = Field(default="", alias="Q2_HELIX_PROGRAM_ID")
    q2_environment: str = Field(default="sandbox", alias="Q2_ENVIRONMENT")

    q2_caliper_api_url: str = Field(default="", alias="Q2_CALIPER_API_URL")
    q2_caliper_api_key: str = Field(default="", alias="Q2_CALIPER_API_KEY")
    q2_amqp_connection_string: str = Field(default="", alias="Q2_AMQP_CONNECTION_STRING")

    @field_validator("q2_environment")
    @classmethod
    def normalize_environment(cls, value: str) -> str:
        env = (value or "sandbox").strip().lower()
        if env not in {"sandbox", "production"}:
            raise ValueError("Q2_ENVIRONMENT must be 'sandbox' or 'production'")
        return env

    @property
    def helix_base_url(self) -> str:
        """Resolved Helix base URL (no trailing slash)."""
        configured = (self.q2_helix_api_url or "").strip().rstrip("/")
        if configured:
            return configured
        if self.q2_environment == "production":
            return _PRODUCTION_URL
        return _SANDBOX_URL

    @property
    def helix_configured(self) -> bool:
        return bool(
            self.q2_helix_api_key.strip()
            and self.q2_helix_api_secret.strip()
            and self.helix_base_url
        )

    @property
    def caliper_configured(self) -> bool:
        return bool(self.q2_caliper_api_url.strip() and self.q2_caliper_api_key.strip())

    @property
    def amqp_configured(self) -> bool:
        return bool(self.q2_amqp_connection_string.strip())

    def missing_helix_vars(self) -> list[str]:
        missing: list[str] = []
        if not self.q2_helix_api_key.strip():
            missing.append("Q2_HELIX_API_KEY")
        if not self.q2_helix_api_secret.strip():
            missing.append("Q2_HELIX_API_SECRET")
        if not (self.q2_helix_api_url or "").strip() and not self.q2_environment:
            missing.append("Q2_HELIX_API_URL")
        return missing

    def require_helix(self) -> None:
        missing = self.missing_helix_vars()
        if missing:
            raise Q2ConfigError(
                "Missing required Q2 Helix environment variables: " + ", ".join(missing),
                code="MISSING_ENV",
            )


@lru_cache
def get_q2_config() -> Q2Config:
    return Q2Config()


def reset_q2_config() -> None:
    """Clear cached config (tests / gate script after .env changes)."""
    get_q2_config.cache_clear()
