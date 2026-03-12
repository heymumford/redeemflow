"""Add multi-tenancy: tenants, tenant_memberships, tenant_id on user tables.

Revision ID: 003
Revises: 002
Create Date: 2026-03-12

Individual users share a default 'tenant-individual' tenant.
Commercial accounts get isolated tenants with separate billing and data.

Uses batch_alter_table for SQLite compatibility (tests run against SQLite).
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None

DEFAULT_TENANT_ID = "tenant-individual"


def upgrade() -> None:
    # 1. Create tenants table
    op.create_table(
        "tenants",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("type", sa.Text, nullable=False),
        sa.Column("created_at", sa.Text, nullable=False),
    )

    # 2. Create tenant_memberships table (composite PK: user_id + tenant_id)
    op.create_table(
        "tenant_memberships",
        sa.Column("user_id", sa.Text, primary_key=True),
        sa.Column("tenant_id", sa.Text, sa.ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True, index=True),
        sa.Column("role", sa.Text, nullable=False, server_default="member"),
        sa.Column("joined_at", sa.Text, nullable=False),
    )

    # 3. Seed default individual tenant (constant, not user input)
    op.execute(
        f"INSERT INTO tenants (id, name, type, created_at) "  # noqa: S608
        f"VALUES ('{DEFAULT_TENANT_ID}', 'Individual', 'individual', '2026-03-12T00:00:00Z')"
    )

    # 4. Add tenant_id column to user-facing tables using batch mode (SQLite compat)
    tables_to_update = [
        "subscriptions",
        "donations",
        "community_pools",
        "forum_posts",
        "founder_profiles",
        "auto_donate_rules",
    ]

    for table in tables_to_update:
        with op.batch_alter_table(table) as batch_op:
            batch_op.add_column(sa.Column("tenant_id", sa.Text, nullable=True))

    # 5. Backfill existing rows with default tenant (constant, not user input)
    for table in tables_to_update:
        op.execute(f"UPDATE {table} SET tenant_id = '{DEFAULT_TENANT_ID}' WHERE tenant_id IS NULL")  # noqa: S608

    # 6. Make tenant_id NOT NULL after backfill (batch mode for SQLite compat)
    for table in tables_to_update:
        with op.batch_alter_table(table) as batch_op:
            batch_op.alter_column("tenant_id", nullable=False)

    # 7. Create indexes after backfill
    for table in tables_to_update:
        op.create_index(f"ix_{table}_tenant_id", table, ["tenant_id"])


def downgrade() -> None:
    tables_to_update = [
        "subscriptions",
        "donations",
        "community_pools",
        "forum_posts",
        "founder_profiles",
        "auto_donate_rules",
    ]

    for table in tables_to_update:
        op.drop_index(f"ix_{table}_tenant_id", table_name=table)
        with op.batch_alter_table(table) as batch_op:
            batch_op.drop_column("tenant_id")

    op.drop_table("tenant_memberships")
    op.drop_table("tenants")
