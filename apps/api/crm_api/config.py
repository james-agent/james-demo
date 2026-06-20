"""Environment-based configuration for the CRM API."""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_env: str = Field(default="development", alias="API_ENV")

    postgres_host: str = Field(default="db", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_user: str = Field(default="crm", alias="POSTGRES_USER")
    postgres_password: str = Field(
        default="crm_dev_password", alias="POSTGRES_PASSWORD"
    )
    postgres_db: str = Field(default="crm", alias="POSTGRES_DB")

    cors_origins: str = Field(
        default="http://localhost:4200",
        alias="CORS_ORIGINS",
    )

    database_url_override: str | None = Field(default=None, alias="DATABASE_URL")

    @field_validator("postgres_password")
    @classmethod
    def postgres_password_required(cls, value: str) -> str:
        if not value or value.strip() == "":
            raise ValueError(
                "POSTGRES_PASSWORD is required. "
                "Copy .env.example to .env and set a local development password."
            )
        return value

    @property
    def database_url(self) -> str:
        if self.database_url_override:
            return self.database_url_override
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def async_database_url(self) -> str:
        if self.database_url_override:
            if self.database_url_override.startswith("postgresql://"):
                return self.database_url_override.replace(
                    "postgresql://", "postgresql+asyncpg://", 1
                )
            return self.database_url_override
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
