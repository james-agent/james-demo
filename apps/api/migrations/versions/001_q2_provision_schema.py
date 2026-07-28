"""Create Q2 provision mapping tables."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "001_q2_provision_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "q2_customers",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("local_customer_key", sa.String(length=128), nullable=False),
        sa.Column("q2_customer_id", sa.String(length=64), nullable=True),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False, server_default="pending"),
        sa.Column("kyc_status", sa.String(length=64), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name="pk_q2_customers"),
        sa.UniqueConstraint("local_customer_key", name="uq_q2_customers_local_customer_key"),
    )
    # App-enforced uniqueness when set; partial unique where supported (PostgreSQL).
    op.create_index(
        "uq_q2_customers_q2_customer_id",
        "q2_customers",
        ["q2_customer_id"],
        unique=True,
        postgresql_where=sa.text("q2_customer_id IS NOT NULL"),
        sqlite_where=sa.text("q2_customer_id IS NOT NULL"),
    )

    op.create_table(
        "q2_accounts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("q2_customer_row_id", sa.String(length=36), nullable=False),
        sa.Column("q2_customer_id", sa.String(length=64), nullable=False),
        sa.Column("q2_account_id", sa.String(length=64), nullable=True),
        sa.Column("product_id", sa.String(length=64), nullable=False),
        sa.Column("account_tag", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False, server_default="pending"),
        sa.Column("last_error", sa.Text(), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name="pk_q2_accounts"),
        sa.ForeignKeyConstraint(
            ["q2_customer_row_id"],
            ["q2_customers.id"],
            name="fk_q2_accounts_q2_customer_row_id",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        sa.UniqueConstraint("account_tag", name="uq_q2_accounts_account_tag"),
    )
    op.create_index("idx_q2_accounts_q2_customer_row_id", "q2_accounts", ["q2_customer_row_id"])

    op.create_table(
        "q2_provision_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("total_customers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("succeeded_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_q2_provision_runs"),
        sa.CheckConstraint(
            "status IN ('queued','running','succeeded','failed','partial')",
            name="ck_q2_provision_runs_status",
        ),
    )
    op.create_index(
        "idx_q2_provision_runs_status_created",
        "q2_provision_runs",
        ["status", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("idx_q2_provision_runs_status_created", table_name="q2_provision_runs")
    op.drop_table("q2_provision_runs")
    op.drop_index("idx_q2_accounts_q2_customer_row_id", table_name="q2_accounts")
    op.drop_table("q2_accounts")
    op.drop_index("uq_q2_customers_q2_customer_id", table_name="q2_customers")
    op.drop_table("q2_customers")
