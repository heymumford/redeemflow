"""Add loyalty_programs, transfer_partners, user_portfolios, program_balances, charity_partners.

Revision ID: 002
Revises: 001
Create Date: 2026-03-11
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "loyalty_programs",
        sa.Column("code", sa.Text, primary_key=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("category", sa.Text, nullable=False),
        sa.Column("cpp_min", sa.Float, nullable=False),
        sa.Column("cpp_max", sa.Float, nullable=False),
    )
    op.create_table(
        "transfer_partners",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("source_program", sa.Text, nullable=False, index=True),
        sa.Column("target_program", sa.Text, nullable=False, index=True),
        sa.Column("transfer_ratio", sa.Float, nullable=False),
        sa.Column("transfer_bonus", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("min_transfer", sa.Integer, nullable=False, server_default="1000"),
        sa.Column("is_instant", sa.Boolean, nullable=False, server_default="true"),
    )
    op.create_table(
        "user_portfolios",
        sa.Column("user_id", sa.Text, primary_key=True),
    )
    op.create_table(
        "program_balances",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Text,
            sa.ForeignKey("user_portfolios.user_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("program_code", sa.Text, nullable=False),
        sa.Column("points", sa.Integer, nullable=False),
        sa.Column("cpp_baseline", sa.Numeric(8, 4), nullable=False),
    )
    op.create_table(
        "charity_partners",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("category", sa.Text, nullable=False),
        sa.Column("state", sa.Text, nullable=False),
        sa.Column("national_url", sa.Text, nullable=False),
        sa.Column("is_501c3", sa.Boolean, nullable=False),
        sa.Column("chapter_name", sa.Text),
        sa.Column("chapter_url", sa.Text),
        sa.Column("donation_url", sa.Text),
        sa.Column("accepts_points_donation", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("ein", sa.Text),
        sa.Column("description", sa.Text),
    )


def downgrade() -> None:
    op.drop_table("charity_partners")
    op.drop_table("program_balances")
    op.drop_table("user_portfolios")
    op.drop_table("transfer_partners")
    op.drop_table("loyalty_programs")
