"""Pytest configuration for CRM API tests."""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
