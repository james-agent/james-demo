"""Alembic migration revision 001 — customers and q2_customer_sync."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001_initial_customers"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("external_ref", sa.String(255), nullable=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(32), nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("address_line1", sa.String(255), nullable=True),
        sa.Column("address_city", sa.String(255), nullable=True),
        sa.Column("address_state", sa.String(32), nullable=True),
        sa.Column("address_postal_code", sa.String(20), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
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
        sa.UniqueConstraint("email", name="uq_customers_email"),
    )
    op.create_index("idx_customers_email", "customers", ["email"], unique=True)

    op.create_table(
        "q2_customer_sync",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("q2_customer_id", sa.String(64), nullable=True),
        sa.Column("tag", sa.String(255), nullable=False),
        sa.Column("kyc_status", sa.String(64), nullable=True),
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
            name="fk_q2_customer_sync_customer_id",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        sa.UniqueConstraint("customer_id", name="uq_q2_customer_sync_customer_id"),
        sa.UniqueConstraint("tag", name="uq_q2_customer_sync_tag"),
    )
    op.create_index(
        "idx_q2_customer_sync_customer_id",
        "q2_customer_sync",
        ["customer_id"],
        unique=True,
    )
    op.create_index(
        "idx_q2_customer_sync_tag", "q2_customer_sync", ["tag"], unique=True
    )
    op.create_index("idx_q2_customer_sync_status", "q2_customer_sync", ["sync_status"])


def downgrade() -> None:
    op.drop_index("idx_q2_customer_sync_status", table_name="q2_customer_sync")
    op.drop_index("idx_q2_customer_sync_tag", table_name="q2_customer_sync")
    op.drop_index("idx_q2_customer_sync_customer_id", table_name="q2_customer_sync")
    op.drop_table("q2_customer_sync")
    op.drop_index("idx_customers_email", table_name="customers")
    op.drop_table("customers")
