"""Shared pytest fixtures for CRM API tests."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

# Ensure settings can load before imports that touch the DB.
os.environ.setdefault("POSTGRES_PASSWORD", "crm_dev_password")

_TEST_DB_DIR = tempfile.mkdtemp(prefix="crm-api-test-")
_TEST_DB_PATH = Path(_TEST_DB_DIR) / "test.db"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TEST_DB_PATH}"

import pytest

from crm_api.db import Base, get_sync_engine, init_db, reset_db_engines


@pytest.fixture(autouse=True)
def _sqlite_db(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("POSTGRES_PASSWORD", "crm_dev_password")
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{_TEST_DB_PATH}")
    reset_db_engines()
    init_db()
    yield
    # Drop all tables between tests for isolation on the shared file DB.
    Base.metadata.drop_all(bind=get_sync_engine())
    reset_db_engines()
