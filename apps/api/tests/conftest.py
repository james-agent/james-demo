"""Shared pytest fixtures for CRM API + Q2 tests."""

from __future__ import annotations

import os

# Force isolated SQLite for tests (never reuse platform DATABASE_URL).
os.environ["POSTGRES_PASSWORD"] = "crm_dev_password"
os.environ["CRM_DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["Q2_MOCK_MODE"] = "true"
os.environ["Q2_ENVIRONMENT"] = "sandbox"
os.environ["Q2_HELIX_API_URL"] = "https://sandbox-api.helix.q2.com"
os.environ["Q2_HELIX_API_KEY"] = "test-key"
os.environ["Q2_HELIX_API_SECRET"] = "test-secret"
os.environ["Q2_HELIX_PROGRAM_ID"] = "test-program"
os.environ["Q2_HELIX_PRODUCT_ID"] = "1"
os.environ["Q2_ALLOW_PLACEHOLDER_PII"] = "true"

from crm_api.config import get_settings
from ext.q2.config import clear_q2_config_cache
from ext.q2.db import Base, get_engine, reset_db_caches


def pytest_configure() -> None:
    get_settings.cache_clear()
    clear_q2_config_cache()
    reset_db_caches()
    Base.metadata.create_all(bind=get_engine())
