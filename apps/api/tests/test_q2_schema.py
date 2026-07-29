"""Verify Q2 Alembic schema names match the card contract."""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

import ext.q2.models  # noqa: F401
from ext.q2.db import Base

REQUIRED_TABLES = ("q2_customers", "q2_accounts", "q2_provision_runs")
REQUIRED_PKS = {
    "q2_customers": "pk_q2_customers",
    "q2_accounts": "pk_q2_accounts",
    "q2_provision_runs": "pk_q2_provision_runs",
}


def test_migration_file_declares_required_names() -> None:
    migration = Path(__file__).resolve().parents[1] / "migrations" / "versions" / "001_q2_provision_schema.py"
    text = migration.read_text(encoding="utf-8")
    for name in (
        "pk_q2_customers",
        "pk_q2_accounts",
        "pk_q2_provision_runs",
        "fk_q2_accounts_q2_customer_row_id",
        "uq_q2_customers_local_customer_key",
        "uq_q2_customers_q2_customer_id",
        "uq_q2_accounts_account_tag",
        "idx_q2_accounts_q2_customer_row_id",
        "idx_q2_provision_runs_status_created",
        "ck_q2_provision_runs_status",
        "q2_customers",
        "q2_accounts",
        "q2_provision_runs",
    ):
        assert name in text, f"missing {name} in migration"


def test_alembic_upgrade_creates_schema(tmp_path) -> None:
    db_path = tmp_path / "q2_schema.db"
    url = f"sqlite+pysqlite:///{db_path}"
    api_root = Path(__file__).resolve().parents[1]
    cfg = Config(str(api_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(api_root / "migrations"))
    cfg.set_main_option("sqlalchemy.url", url)

    command.upgrade(cfg, "head")

    engine = create_engine(url)
    insp = inspect(engine)
    tables = set(insp.get_table_names())
    for table in REQUIRED_TABLES:
        assert table in tables

    # PK names (SQLite exposes via get_pk_constraint)
    for table, pk_name in REQUIRED_PKS.items():
        pk = insp.get_pk_constraint(table)
        # SQLite may omit custom PK names; ensure columns are correct.
        assert pk.get("constrained_columns") == ["id"]
        if pk.get("name"):
            assert pk["name"] == pk_name

    fks = insp.get_foreign_keys("q2_accounts")
    assert any(
        fk.get("referred_table") == "q2_customers"
        and fk.get("constrained_columns") == ["q2_customer_row_id"]
        and (fk.get("options") or {}).get("ondelete", "").upper() in {"CASCADE", ""}
        for fk in fks
    )

    customer_indexes = {idx["name"] for idx in insp.get_indexes("q2_customers")}
    assert "uq_q2_customers_q2_customer_id" in customer_indexes or any(
        "q2_customer_id" in (idx.get("column_names") or []) for idx in insp.get_indexes("q2_customers")
    )

    account_indexes = {idx["name"] for idx in insp.get_indexes("q2_accounts")}
    assert "idx_q2_accounts_q2_customer_row_id" in account_indexes

    run_indexes = {idx["name"] for idx in insp.get_indexes("q2_provision_runs")}
    assert "idx_q2_provision_runs_status_created" in run_indexes

    # ORM metadata still matches table set.
    assert set(Base.metadata.tables) >= set(REQUIRED_TABLES)
