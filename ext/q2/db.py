"""SQLAlchemy engine and session helpers for local Q2 customer persistence."""

from __future__ import annotations

import os
from collections.abc import Iterator
from functools import lru_cache
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

Base = declarative_base()


def resolve_database_url() -> str:
    """Resolve DB URL: explicit override → Postgres settings → local SQLite."""
    explicit = (
        os.environ.get("Q2_DATABASE_URL", "").strip()
        or os.environ.get("DATABASE_URL", "").strip()
    )
    if explicit:
        return explicit

    host = os.environ.get("POSTGRES_HOST", "").strip()
    user = os.environ.get("POSTGRES_USER", "").strip()
    password = os.environ.get("POSTGRES_PASSWORD", "").strip()
    db_name = os.environ.get("POSTGRES_DB", "").strip()
    port = os.environ.get("POSTGRES_PORT", "5432").strip() or "5432"
    if host and user and db_name:
        return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db_name}"

    data_dir = Path(__file__).resolve().parents[2] / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{data_dir / 'q2_local.db'}"


def _configure_sqlite(engine: Engine) -> None:
    if engine.dialect.name != "sqlite":
        return

    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_connection, _connection_record) -> None:  # type: ignore[no-untyped-def]
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


@lru_cache
def get_engine(url: str | None = None) -> Engine:
    database_url = url or resolve_database_url()
    connect_args: dict = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    engine = create_engine(database_url, future=True, connect_args=connect_args)
    _configure_sqlite(engine)
    return engine


def get_session_factory(url: str | None = None) -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(url), autoflush=False, autocommit=False, future=True)


def get_db_session() -> Iterator[Session]:
    """FastAPI dependency yielding a request-scoped session."""
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db(*, url: str | None = None, create_tables: bool = True) -> Engine:
    """Initialize engine and optionally create ORM tables (dev/SQLite)."""
    # Import models so metadata is populated.
    from ext.q2.models import local_customer as _local_customer  # noqa: F401

    engine = get_engine(url)
    if create_tables:
        Base.metadata.create_all(bind=engine)
    return engine
