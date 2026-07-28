"""SQLAlchemy engine and session helpers."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator, Generator
from functools import lru_cache

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from crm_api.config import get_settings


class Base(DeclarativeBase):
    """Shared declarative base for ORM models."""


def sync_database_url() -> str:
    override = os.getenv("DATABASE_URL", "").strip()
    if override:
        if override.startswith("sqlite+aiosqlite:"):
            return override.replace("sqlite+aiosqlite:", "sqlite:", 1)
        if override.startswith("postgresql+asyncpg:"):
            return override.replace("postgresql+asyncpg:", "postgresql:", 1)
        return override
    return get_settings().database_url


def async_database_url() -> str:
    override = os.getenv("DATABASE_URL", "").strip()
    if override:
        if override.startswith("sqlite:") and "+aiosqlite" not in override:
            return override.replace("sqlite:", "sqlite+aiosqlite:", 1)
        if override.startswith("postgresql://"):
            return override.replace("postgresql://", "postgresql+asyncpg://", 1)
        return override
    return get_settings().async_database_url


def _is_sqlite(url: str) -> bool:
    return url.startswith("sqlite")


def _is_memory_sqlite(url: str) -> bool:
    return _is_sqlite(url) and (":memory:" in url or "mode=memory" in url)


def _configure_sqlite(engine: Engine) -> None:
    if engine.dialect.name != "sqlite":
        return

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:  # type: ignore[no-untyped-def]
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


@lru_cache
def get_sync_engine() -> Engine:
    url = sync_database_url()
    kwargs: dict = {"future": True}
    if _is_memory_sqlite(url):
        kwargs["connect_args"] = {"check_same_thread": False}
        kwargs["poolclass"] = StaticPool
    elif _is_sqlite(url):
        kwargs["connect_args"] = {"check_same_thread": False}
    engine = create_engine(url, **kwargs)
    _configure_sqlite(engine)
    return engine


@lru_cache
def get_async_engine() -> AsyncEngine:
    url = async_database_url()
    kwargs: dict = {"future": True}
    if _is_memory_sqlite(url):
        kwargs["connect_args"] = {"check_same_thread": False}
        kwargs["poolclass"] = StaticPool
    return create_async_engine(url, **kwargs)


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_sync_engine(), autoflush=False, autocommit=False, class_=Session)


@lru_cache
def get_async_session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=get_async_engine(), expire_on_commit=False, class_=AsyncSession)


def reset_db_engines() -> None:
    """Clear cached engines (used by tests)."""
    get_sync_engine.cache_clear()
    get_async_engine.cache_clear()
    get_session_factory.cache_clear()
    get_async_session_factory.cache_clear()


def get_sync_session() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with get_async_session_factory()() as session:
        yield session


def init_db() -> None:
    """Create tables for local/demo (Alembic is preferred for Postgres)."""
    from crm_api import models  # noqa: F401

    Base.metadata.create_all(bind=get_sync_engine())
