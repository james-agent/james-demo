"""Q2 Helix environment configuration."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Q2Environment = Literal["sandbox", "production"]

DEFAULT_SANDBOX_URL = "https://sandbox-api.helix.q2.com"
DEFAULT_PRODUCTION_URL = "https://api.helix.q2.com"


class Q2ConfigError(ValueError):
    """Raised when required Q2 configuration is missing or invalid."""


class Q2Config(BaseSettings):
    """Settings for Q2 Helix HTTP Basic Auth connectivity."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_url: str = Field(default=DEFAULT_SANDBOX_URL, alias="Q2_HELIX_API_URL")
    api_key: str = Field(default="", alias="Q2_HELIX_API_KEY")
    api_secret: str = Field(default="", alias="Q2_HELIX_API_SECRET")
    program_id: str = Field(default="", alias="Q2_HELIX_PROGRAM_ID")
    default_product_id: str = Field(default="", alias="Q2_HELIX_DEFAULT_PRODUCT_ID")
    environment: Q2Environment = Field(default="sandbox", alias="Q2_ENVIRONMENT")

    @field_validator("environment", mode="before")
    @classmethod
    def normalize_environment(cls, value: object) -> str:
        if value is None or str(value).strip() == "":
            return "sandbox"
        return str(value).strip().lower()

    @property
    def base_url(self) -> str:
        return self.api_url.rstrip("/")

    def missing_fields(self) -> list[str]:
        missing: list[str] = []
        if not self.api_key.strip():
            missing.append("Q2_HELIX_API_KEY")
        if not self.api_secret.strip():
            missing.append("Q2_HELIX_API_SECRET")
        if not self.program_id.strip():
            missing.append("Q2_HELIX_PROGRAM_ID")
        if not self.api_url.strip():
            missing.append("Q2_HELIX_API_URL")
        return missing

    def require_configured(self) -> None:
        missing = self.missing_fields()
        if missing:
            raise Q2ConfigError(
                "Missing required Q2 configuration: " + ", ".join(missing)
            )


@lru_cache
def get_q2_config() -> Q2Config:
    return Q2Config()
