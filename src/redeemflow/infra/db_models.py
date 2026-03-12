"""SQLAlchemy table definitions — schema source of truth.

Uses SQLAlchemy Core (Table + MetaData), not ORM mapped classes.
Keeps the DB layer separate from frozen dataclasses in domain models.

Each table has companion to_domain() / from_domain() module-level functions
in pg_repositories.py for bidirectional conversion with frozen dataclasses.
"""

from __future__ import annotations

from sqlalchemy import JSON, Boolean, Column, Float, ForeignKey, Integer, MetaData, Numeric, Table, Text

metadata = MetaData()

# --- Tenancy tables ---

tenants = Table(
    "tenants",
    metadata,
    Column("id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("type", Text, nullable=False),  # individual | commercial
    Column("created_at", Text, nullable=False),
)

tenant_memberships = Table(
    "tenant_memberships",
    metadata,
    Column("user_id", Text, nullable=False),
    Column("tenant_id", Text, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("role", Text, nullable=False, default="member"),  # owner | admin | member
    Column("joined_at", Text, nullable=False),
)

# --- Portfolio tables ---

loyalty_programs = Table(
    "loyalty_programs",
    metadata,
    Column("code", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("category", Text, nullable=False),
    Column("cpp_min", Float, nullable=False),
    Column("cpp_max", Float, nullable=False),
)

transfer_partners = Table(
    "transfer_partners",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("source_program", Text, nullable=False, index=True),
    Column("target_program", Text, nullable=False, index=True),
    Column("transfer_ratio", Float, nullable=False),
    Column("transfer_bonus", Float, nullable=False, default=0.0),
    Column("min_transfer", Integer, nullable=False, default=1000),
    Column("is_instant", Boolean, nullable=False, default=True),
)

user_portfolios = Table(
    "user_portfolios",
    metadata,
    Column("user_id", Text, primary_key=True),
)

program_balances = Table(
    "program_balances",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Text, ForeignKey("user_portfolios.user_id", ondelete="CASCADE"), nullable=False, index=True),
    Column("program_code", Text, nullable=False),
    Column("points", Integer, nullable=False),
    Column("cpp_baseline", Numeric(8, 4), nullable=False),
)

# --- Charity tables ---

charity_partners = Table(
    "charity_partners",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Text, nullable=False),
    Column("category", Text, nullable=False),
    Column("state", Text, nullable=False),
    Column("national_url", Text, nullable=False),
    Column("is_501c3", Boolean, nullable=False),
    Column("chapter_name", Text),
    Column("chapter_url", Text),
    Column("donation_url", Text),
    Column("accepts_points_donation", Boolean, nullable=False, default=False),
    Column("ein", Text),
    Column("description", Text),
)

# --- Billing tables ---

subscriptions = Table(
    "subscriptions",
    metadata,
    Column("id", Text, primary_key=True),
    Column("user_id", Text, nullable=False, index=True),
    Column("tenant_id", Text, ForeignKey("tenants.id"), nullable=True, index=True),
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
    Column("tenant_id", Text, ForeignKey("tenants.id"), nullable=True, index=True),
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
    Column("tenant_id", Text, ForeignKey("tenants.id"), nullable=True, index=True),
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
    Column("tenant_id", Text, ForeignKey("tenants.id"), nullable=True, index=True),
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
    Column("tenant_id", Text, ForeignKey("tenants.id"), nullable=True, index=True),
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
    Column("tenant_id", Text, ForeignKey("tenants.id"), nullable=True, index=True),
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
