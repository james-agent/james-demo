"""Alembic migration revision 002 — q2_account_sync."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002_q2_account_sync"
down_revision = "001_initial_customers"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "q2_account_sync",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("q2_customer_id", sa.String(64), nullable=False),
        sa.Column("q2_account_id", sa.String(64), nullable=True),
        sa.Column("product_id", sa.String(64), nullable=False),
        sa.Column("account_tag", sa.String(255), nullable=False),
        sa.Column("account_name", sa.String(255), nullable=True),
        sa.Column(
            "sync_status", sa.String(32), nullable=False, server_default="pending"
        ),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customers.id"],
            name="fk_q2_account_sync_customer_id",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        sa.UniqueConstraint(
            "customer_id", "product_id", name="uq_q2_account_sync_customer_product"
        ),
        sa.UniqueConstraint("account_tag", name="uq_q2_account_sync_account_tag"),
    )
    op.create_index(
        "idx_q2_account_sync_customer_product",
        "q2_account_sync",
        ["customer_id", "product_id"],
        unique=True,
    )
    op.create_index(
        "idx_q2_account_sync_account_tag",
        "q2_account_sync",
        ["account_tag"],
        unique=True,
    )
    op.create_index("idx_q2_account_sync_status", "q2_account_sync", ["sync_status"])


def downgrade() -> None:
    op.drop_index("idx_q2_account_sync_status", table_name="q2_account_sync")
    op.drop_index("idx_q2_account_sync_account_tag", table_name="q2_account_sync")
    op.drop_index("idx_q2_account_sync_customer_product", table_name="q2_account_sync")
    op.drop_table("q2_account_sync")
