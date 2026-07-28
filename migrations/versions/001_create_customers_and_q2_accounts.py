"""Create customers and customer_q2_accounts tables (exact schema).

Revision ID: 001_q2_local_customers
Revises:
Create Date: 2026-07-28
"""

from __future__ import annotations

from alembic import op

revision = "001_q2_local_customers"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL DDL matching the card schema exactly (PKs, FKs, indexes, checks).
    op.execute(
        """
        CREATE TABLE customers (
            id UUID NOT NULL,
            tag VARCHAR(50) NOT NULL,
            full_name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NULL,
            phone VARCHAR(64) NULL,
            date_of_birth DATE NULL,
            status VARCHAR(32) NOT NULL DEFAULT 'active',
            q2_customer_id VARCHAR(64) NULL,
            provision_status VARCHAR(32) NOT NULL DEFAULT 'pending',
            last_provision_error TEXT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT pk_customers PRIMARY KEY (id),
            CONSTRAINT uq_customers_tag UNIQUE (tag),
            CONSTRAINT ck_customers_provision_status
                CHECK (provision_status IN ('pending','customer_created','account_created','failed')),
            CONSTRAINT ck_customers_status
                CHECK (status IN ('active','inactive','archived'))
        )
        """
    )
    op.execute("CREATE INDEX idx_customers_q2_customer_id ON customers (q2_customer_id)")
    op.execute("CREATE INDEX idx_customers_provision_status ON customers (provision_status)")

    op.execute(
        """
        CREATE TABLE customer_q2_accounts (
            id UUID NOT NULL,
            customer_id UUID NOT NULL,
            q2_account_id VARCHAR(64) NOT NULL,
            product_id VARCHAR(64) NOT NULL,
            account_tag VARCHAR(50) NOT NULL,
            account_name VARCHAR(255) NOT NULL,
            status VARCHAR(32) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT pk_customer_q2_accounts PRIMARY KEY (id),
            CONSTRAINT fk_customer_q2_accounts_customer_id
                FOREIGN KEY (customer_id) REFERENCES customers(id)
                ON DELETE CASCADE ON UPDATE CASCADE,
            CONSTRAINT uq_customer_q2_accounts_account_tag UNIQUE (account_tag),
            CONSTRAINT uq_customer_q2_accounts_q2_account_id UNIQUE (q2_account_id)
        )
        """
    )
    op.execute(
        "CREATE INDEX idx_customer_q2_accounts_customer_id ON customer_q2_accounts (customer_id)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS customer_q2_accounts")
    op.execute("DROP TABLE IF EXISTS customers")
