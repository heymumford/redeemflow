"""SQLAlchemy table definitions — schema source of truth.

Uses SQLAlchemy Core (Table + MetaData), not ORM mapped classes.
Keeps the DB layer separate from frozen dataclasses in domain models.
"""

from __future__ import annotations

from sqlalchemy import JSON, Boolean, Integer, MetaData, Numeric, Table, Text, Column, ForeignKey

metadata = MetaData()

subscriptions = Table(
    "subscriptions",
    metadata,
    Column("id", Text, primary_key=True),
    Column("user_id", Text, nullable=False, index=True),
    Column("tier", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("current_period_start", Text, nullable=False),
    Column("current_period_end", Text, nullable=False),
    Column("stripe_subscription_id", Text),
)

donations = Table(
    "donations",
    metadata,
    Column("id", Text, primary_key=True),
    Column("user_id", Text, nullable=False, index=True),
    Column("charity_name", Text, nullable=False),
    Column("charity_state", Text, nullable=False),
    Column("program_code", Text, nullable=False),
    Column("points_donated", Integer, nullable=False),
    Column("dollar_value", Numeric(12, 4), nullable=False),
    Column("status", Text, nullable=False),
    Column("created_at", Text, nullable=False),
    Column("completed_at", Text),
    Column("change_api_reference", Text),
)

community_pools = Table(
    "community_pools",
    metadata,
    Column("id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("creator_id", Text, nullable=False),
    Column("target_charity_name", Text, nullable=False),
    Column("target_charity_state", Text, nullable=False),
    Column("goal_amount", Numeric(12, 4), nullable=False),
    Column("status", Text, nullable=False),
    Column("created_at", Text, nullable=False),
    Column("completed_at", Text),
)

pledges = Table(
    "pledges",
    metadata,
    Column("id", Text, primary_key=True),
    Column("user_id", Text, nullable=False),
    Column("pool_id", Text, ForeignKey("community_pools.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("program_code", Text, nullable=False),
    Column("points_pledged", Integer, nullable=False),
    Column("dollar_value", Numeric(12, 4), nullable=False),
    Column("pledged_at", Text, nullable=False),
)

forum_posts = Table(
    "forum_posts",
    metadata,
    Column("id", Text, primary_key=True),
    Column("author_id", Text, nullable=False, index=True),
    Column("author_name", Text, nullable=False),
    Column("category", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("content", Text, nullable=False),
    Column("created_at", Text, nullable=False),
    Column("updated_at", Text),
    Column("upvotes", Integer, nullable=False, default=0),
    Column("is_pinned", Boolean, nullable=False, default=False),
)

forum_replies = Table(
    "forum_replies",
    metadata,
    Column("id", Text, primary_key=True),
    Column("post_id", Text, ForeignKey("forum_posts.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("author_id", Text, nullable=False),
    Column("author_name", Text, nullable=False),
    Column("content", Text, nullable=False),
    Column("created_at", Text, nullable=False),
    Column("upvotes", Integer, nullable=False, default=0),
)

founder_profiles = Table(
    "founder_profiles",
    metadata,
    Column("user_id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("email", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("joined_at", Text, nullable=False),
    Column("company_name", Text),
    Column("industry", Text),
    Column("verification_source", Text),
    Column("bio", Text),
    Column("travel_interests", JSON, nullable=False, default=[]),
    Column("is_mentor", Boolean, nullable=False, default=False),
    Column("mentor_topics", JSON, nullable=False, default=[]),
)

auto_donate_rules = Table(
    "auto_donate_rules",
    metadata,
    Column("id", Text, primary_key=True),
    Column("user_id", Text, nullable=False, index=True),
    Column("program_code", Text, nullable=False),
    Column("charity_name", Text, nullable=False),
    Column("charity_state", Text, nullable=False),
    Column("days_unused_threshold", Integer, nullable=False),
    Column("is_active", Boolean, nullable=False, default=True),
)

charity_alignments = Table(
    "charity_alignments",
    metadata,
    Column("user_id", Text, primary_key=True),
    Column("charity_name", Text, nullable=False),
    Column("charity_state", Text, nullable=False),
    Column("subscription_tier", Text, nullable=False),
    Column("monthly_contribution", Numeric(12, 4), nullable=False),
    Column("annual_contribution", Numeric(12, 4), nullable=False),
)
