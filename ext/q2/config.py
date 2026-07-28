"""Q2 Helix environment configuration loader.

Credentials are loaded from environment variables (or a local ``.env`` file).
Never hardcode secrets; never log API keys or secrets.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

# Prefer Q2_HELIX_* names; accept legacy aliases used in some codebases.
_ENV_ALIASES: dict[str, tuple[str, ...]] = {
    "api_url": ("Q2_HELIX_API_URL", "Q2_BASE_URL", "Q2_API_URL"),
    "api_key": ("Q2_HELIX_API_KEY", "Q2_API_KEY"),
    "api_secret": ("Q2_HELIX_API_SECRET", "Q2_API_SECRET"),
    "program_id": ("Q2_HELIX_PROGRAM_ID", "Q2_PROGRAM_ID"),
    "environment": ("Q2_ENVIRONMENT",),
}

SANDBOX_URL = "https://sandbox-api.helix.q2.com"
PRODUCTION_URL = "https://api.helix.q2.com"

REQUIRED_FIELDS = ("api_url", "api_key", "api_secret", "program_id")


def _load_dotenv(path: Path) -> None:
    """Load KEY=VALUE pairs from a .env file into os.environ if not already set."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


def _first_env(*names: str) -> str:
    for name in names:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return ""


@dataclass(frozen=True)
class Q2Config:
    """Immutable Q2 Helix connection settings."""

    api_url: str
    api_key: str
    api_secret: str
    program_id: str
    environment: str  # sandbox | production

    @property
    def is_sandbox(self) -> bool:
        return self.environment.lower() == "sandbox"

    @property
    def is_complete(self) -> bool:
        return all(getattr(self, field).strip() for field in REQUIRED_FIELDS)

    def status_map(self) -> dict[str, str]:
        """Map preferred env var name → SET | MISSING based on actual env (never values)."""
        result: dict[str, str] = {}
        for field in (*REQUIRED_FIELDS, "environment"):
            aliases = _ENV_ALIASES[field]
            preferred = aliases[0]
            result[preferred] = "SET" if _first_env(*aliases) else "MISSING"
        return result

    def missing_fields(self) -> list[str]:
        """Return preferred env var names required for a live Helix call."""
        missing: list[str] = []
        # URL may be derived from Q2_ENVIRONMENT; key/secret/program must be explicit.
        for field in ("api_key", "api_secret", "program_id"):
            if not getattr(self, field).strip():
                missing.append(_ENV_ALIASES[field][0])
        if not _first_env(*_ENV_ALIASES["api_url"]) and not self.api_url:
            missing.append(_ENV_ALIASES["api_url"][0])
        return missing


def _resolve_environment(explicit: str, api_url: str) -> str:
    if explicit:
        normalized = explicit.lower()
        if normalized in {"sandbox", "production"}:
            return normalized
    if "sandbox" in api_url.lower():
        return "sandbox"
    if api_url.rstrip("/").endswith("api.helix.q2.com"):
        return "production"
    return "sandbox"


def _resolve_api_url(raw_url: str, environment: str) -> str:
    if raw_url:
        return raw_url.rstrip("/")
    return SANDBOX_URL if environment == "sandbox" else PRODUCTION_URL


def _split_combined_key(api_key: str, api_secret: str) -> tuple[str, str]:
    """Support ``key:secret`` packed into Q2_HELIX_API_KEY when secret is empty."""
    if api_secret:
        return api_key, api_secret
    if ":" in api_key:
        user, _, password = api_key.partition(":")
        return user, password
    return api_key, api_secret


@lru_cache
def get_q2_config(*, env_file: str | None = None) -> Q2Config:
    """Load Q2 Helix config from the environment.

    Searches for a ``.env`` at the repository root (two levels above this
    package) unless ``env_file`` is provided.
    """
    if env_file:
        _load_dotenv(Path(env_file))
    else:
        repo_root = Path(__file__).resolve().parents[2]
        _load_dotenv(repo_root / ".env")
        # Also allow apps/api/.env for local API-only workflows
        _load_dotenv(repo_root / "apps" / "api" / ".env")

    raw_key = _first_env(*_ENV_ALIASES["api_key"])
    raw_secret = _first_env(*_ENV_ALIASES["api_secret"])
    api_key, api_secret = _split_combined_key(raw_key, raw_secret)

    raw_url = _first_env(*_ENV_ALIASES["api_url"])
    explicit_env = _first_env(*_ENV_ALIASES["environment"])
    environment = _resolve_environment(explicit_env, raw_url)
    api_url = _resolve_api_url(raw_url, environment)

    return Q2Config(
        api_url=api_url,
        api_key=api_key,
        api_secret=api_secret,
        program_id=_first_env(*_ENV_ALIASES["program_id"]),
        environment=environment,
    )
