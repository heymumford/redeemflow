"""Initial schema — 9 tables for all stateful domain models.

Revision ID: 001
Revises: None
Create Date: 2026-03-09
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("user_id", sa.Text, nullable=False, index=True),
        sa.Column("tier", sa.Text, nullable=False),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("current_period_start", sa.Text, nullable=False),
        sa.Column("current_period_end", sa.Text, nullable=False),
        sa.Column("stripe_subscription_id", sa.Text),
    )
    op.create_table(
        "donations",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("user_id", sa.Text, nullable=False, index=True),
        sa.Column("charity_name", sa.Text, nullable=False),
        sa.Column("charity_state", sa.Text, nullable=False),
        sa.Column("program_code", sa.Text, nullable=False),
        sa.Column("points_donated", sa.Integer, nullable=False),
        sa.Column("dollar_value", sa.Numeric(12, 4), nullable=False),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("created_at", sa.Text, nullable=False),
        sa.Column("completed_at", sa.Text),
        sa.Column("change_api_reference", sa.Text),
    )
    op.create_table(
        "community_pools",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("creator_id", sa.Text, nullable=False),
        sa.Column("target_charity_name", sa.Text, nullable=False),
        sa.Column("target_charity_state", sa.Text, nullable=False),
        sa.Column("goal_amount", sa.Numeric(12, 4), nullable=False),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("created_at", sa.Text, nullable=False),
        sa.Column("completed_at", sa.Text),
    )
    op.create_table(
        "pledges",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("user_id", sa.Text, nullable=False),
        sa.Column(
            "pool_id", sa.Text, sa.ForeignKey("community_pools.id", ondelete="CASCADE"), nullable=False, index=True
        ),
        sa.Column("program_code", sa.Text, nullable=False),
        sa.Column("points_pledged", sa.Integer, nullable=False),
        sa.Column("dollar_value", sa.Numeric(12, 4), nullable=False),
        sa.Column("pledged_at", sa.Text, nullable=False),
    )
    op.create_table(
        "forum_posts",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("author_id", sa.Text, nullable=False, index=True),
        sa.Column("author_name", sa.Text, nullable=False),
        sa.Column("category", sa.Text, nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("created_at", sa.Text, nullable=False),
        sa.Column("updated_at", sa.Text),
        sa.Column("upvotes", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_pinned", sa.Boolean, nullable=False, server_default="false"),
    )
    op.create_table(
        "forum_replies",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("post_id", sa.Text, sa.ForeignKey("forum_posts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("author_id", sa.Text, nullable=False),
        sa.Column("author_name", sa.Text, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("created_at", sa.Text, nullable=False),
        sa.Column("upvotes", sa.Integer, nullable=False, server_default="0"),
    )
    op.create_table(
        "founder_profiles",
        sa.Column("user_id", sa.Text, primary_key=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("email", sa.Text, nullable=False),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("joined_at", sa.Text, nullable=False),
        sa.Column("company_name", sa.Text),
        sa.Column("industry", sa.Text),
        sa.Column("verification_source", sa.Text),
        sa.Column("bio", sa.Text),
        sa.Column("travel_interests", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("is_mentor", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("mentor_topics", sa.JSON, nullable=False, server_default="[]"),
    )
    op.create_table(
        "auto_donate_rules",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("user_id", sa.Text, nullable=False, index=True),
        sa.Column("program_code", sa.Text, nullable=False),
        sa.Column("charity_name", sa.Text, nullable=False),
        sa.Column("charity_state", sa.Text, nullable=False),
        sa.Column("days_unused_threshold", sa.Integer, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
    )
    op.create_table(
        "charity_alignments",
        sa.Column("user_id", sa.Text, primary_key=True),
        sa.Column("charity_name", sa.Text, nullable=False),
        sa.Column("charity_state", sa.Text, nullable=False),
        sa.Column("subscription_tier", sa.Text, nullable=False),
        sa.Column("monthly_contribution", sa.Numeric(12, 4), nullable=False),
        sa.Column("annual_contribution", sa.Numeric(12, 4), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("charity_alignments")
    op.drop_table("auto_donate_rules")
    op.drop_table("founder_profiles")
    op.drop_table("forum_replies")
    op.drop_table("forum_posts")
    op.drop_table("pledges")
    op.drop_table("community_pools")
    op.drop_table("donations")
    op.drop_table("subscriptions")
