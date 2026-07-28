"""Create customers table with Q2 Helix linkage columns."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260728_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("external_ref", sa.String(length=64), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("first_name", sa.String(length=64), nullable=False),
        sa.Column("last_name", sa.String(length=128), nullable=False),
        sa.Column("middle_name", sa.String(length=64), nullable=True),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("tax_id", sa.String(length=32), nullable=True),
        sa.Column("tax_id_type", sa.String(length=16), nullable=True),
        sa.Column("phone_number", sa.String(length=16), nullable=True),
        sa.Column("address_line1", sa.String(length=100), nullable=True),
        sa.Column("city", sa.String(length=64), nullable=True),
        sa.Column("state", sa.String(length=2), nullable=True),
        sa.Column("postal_code", sa.String(length=10), nullable=True),
        sa.Column("country_code", sa.String(length=3), nullable=True, server_default="USA"),
        sa.Column("q2_customer_id", sa.BigInteger(), nullable=True),
        sa.Column("q2_account_id", sa.BigInteger(), nullable=True),
        sa.Column("q2_customer_tag", sa.String(length=50), nullable=True),
        sa.Column("q2_account_tag", sa.String(length=50), nullable=True),
        sa.Column(
            "q2_sync_status",
            sa.String(length=32),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("q2_last_error", sa.Text(), nullable=True),
        sa.Column("q2_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_customers"),
        sa.CheckConstraint(
            "q2_sync_status IN ('pending','customer_linked','account_linked',"
            "'skipped_incomplete','failed')",
            name="ck_customers_q2_sync_status",
        ),
    )
    op.create_index("uq_customers_email", "customers", ["email"], unique=True)
    op.create_index(
        "uq_customers_q2_customer_tag",
        "customers",
        ["q2_customer_tag"],
        unique=True,
        postgresql_where=sa.text("q2_customer_tag IS NOT NULL"),
        sqlite_where=sa.text("q2_customer_tag IS NOT NULL"),
    )
    op.create_index(
        "uq_customers_q2_customer_id",
        "customers",
        ["q2_customer_id"],
        unique=True,
        postgresql_where=sa.text("q2_customer_id IS NOT NULL"),
        sqlite_where=sa.text("q2_customer_id IS NOT NULL"),
    )
    op.create_index("idx_customers_q2_sync_status", "customers", ["q2_sync_status"])


def downgrade() -> None:
    op.drop_index("idx_customers_q2_sync_status", table_name="customers")
    op.drop_index("uq_customers_q2_customer_id", table_name="customers")
    op.drop_index("uq_customers_q2_customer_tag", table_name="customers")
    op.drop_index("uq_customers_email", table_name="customers")
    op.drop_table("customers")
