"""Deterministic factory functions for all RedeemFlow domain objects.

Each builder returns a valid instance with sensible defaults.
Pass **overrides to customize any field per-test.

Beck: "Make the test easy to write" — these builders eliminate boilerplate.
Fowler: "Test Data Builders" — composable, readable, maintainable.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from redeemflow.billing.models import Subscription, SubscriptionTier
from redeemflow.charity.donation_flow import Donation, DonationStatus
from redeemflow.charity.models import CharityCategory, CharityOrganization
from redeemflow.community.forum import ForumCategory, ForumPost, ForumReply
from redeemflow.community.founders_network import FounderProfile, FounderStatus
from redeemflow.community.models import CommunityPool, Pledge, PoolStatus
from redeemflow.identity.models import User
from redeemflow.notifications.models import Alert, AlertPriority, AlertType
from redeemflow.optimization.models import RedemptionOption, TransferPartner, TransferPath
from redeemflow.portfolio.models import LoyaltyAccount, LoyaltyProgram, PointBalance
from redeemflow.recommendations.models import Recommendation
from redeemflow.search.award_search import AwardResult
from redeemflow.valuations.models import ProgramValuation, ValuationSource

_NOW = datetime.now(UTC).isoformat()
_COUNTER = 0


def _next_id(prefix: str = "test") -> str:
    global _COUNTER
    _COUNTER += 1
    return f"{prefix}-{_COUNTER:04d}"


# --- Identity ---


def build_user(**overrides) -> User:
    defaults = {"id": _next_id("user"), "email": "test@example.com", "name": "Test User", "tier": "free"}
    return User(**(defaults | overrides))


# --- Portfolio ---


def build_program(**overrides) -> LoyaltyProgram:
    defaults = {"code": "chase-ur", "name": "Chase Ultimate Rewards"}
    return LoyaltyProgram(**(defaults | overrides))


def build_balance(**overrides) -> PointBalance:
    defaults = {"program_code": "chase-ur", "points": 50000, "cpp_baseline": Decimal("1.5")}
    return PointBalance(**(defaults | overrides))


def build_account(**overrides) -> LoyaltyAccount:
    defaults = {"user_id": _next_id("user"), "program_code": "chase-ur", "member_id": "M-12345"}
    return LoyaltyAccount(**(defaults | overrides))


# --- Valuations ---


def build_valuation(**overrides) -> ProgramValuation:
    defaults = {
        "program_code": "chase-ur",
        "program_name": "Chase Ultimate Rewards",
        "valuations": {ValuationSource.TPG: Decimal("2.0"), ValuationSource.NERDWALLET: Decimal("1.8")},
        "cash_back_cpp": Decimal("1.0"),
    }
    return ProgramValuation(**(defaults | overrides))


# --- Optimization ---


def build_transfer_partner(**overrides) -> TransferPartner:
    defaults = {
        "source_program": "chase-ur",
        "target_program": "hyatt",
        "transfer_ratio": 1.0,
        "transfer_bonus": 0.0,
        "min_transfer": 1000,
        "is_instant": True,
    }
    return TransferPartner(**(defaults | overrides))


def build_redemption(**overrides) -> RedemptionOption:
    defaults = {
        "program": "hyatt",
        "description": "Category 1-4 free night",
        "points_required": 15000,
        "cash_value": 250.0,
        "availability": "high",
    }
    return RedemptionOption(**(defaults | overrides))


def build_transfer_path(**overrides) -> TransferPath:
    partner = build_transfer_partner()
    redemption = build_redemption()
    defaults = {
        "steps": (partner,),
        "redemption": redemption,
        "source_points_needed": 15000,
        "effective_cpp": 1.67,
        "total_hops": 1,
    }
    return TransferPath(**(defaults | overrides))


# --- Billing ---


def build_subscription(**overrides) -> Subscription:
    defaults = {
        "id": _next_id("sub"),
        "user_id": _next_id("user"),
        "tier": SubscriptionTier.FREE,
        "status": "active",
        "current_period_start": _NOW,
        "current_period_end": _NOW,
        "stripe_subscription_id": None,
    }
    return Subscription(**(defaults | overrides))


# --- Charity ---


def build_charity(**overrides) -> CharityOrganization:
    defaults = {
        "name": "Test Charity",
        "category": CharityCategory.EDUCATION,
        "state": "CA",
        "national_url": "https://example.org",
        "is_501c3": True,
    }
    return CharityOrganization(**(defaults | overrides))


def build_donation(**overrides) -> Donation:
    defaults = {
        "id": _next_id("don"),
        "user_id": _next_id("user"),
        "charity_name": "Test Charity",
        "charity_state": "CA",
        "program_code": "chase-ur",
        "points_donated": 5000,
        "dollar_value": Decimal("75.00"),
        "status": DonationStatus.PENDING,
        "created_at": _NOW,
    }
    return Donation(**(defaults | overrides))


# --- Community Pools ---


def build_pool(**overrides) -> CommunityPool:
    defaults = {
        "id": _next_id("pool"),
        "name": "Test Pool",
        "creator_id": _next_id("user"),
        "target_charity_name": "Test Charity",
        "target_charity_state": "CA",
        "goal_amount": Decimal("1000.00"),
        "status": PoolStatus.OPEN,
        "created_at": _NOW,
    }
    return CommunityPool(**(defaults | overrides))


def build_pledge(**overrides) -> Pledge:
    defaults = {
        "id": _next_id("pledge"),
        "user_id": _next_id("user"),
        "pool_id": _next_id("pool"),
        "program_code": "chase-ur",
        "points_pledged": 2000,
        "dollar_value": Decimal("30.00"),
        "pledged_at": _NOW,
    }
    return Pledge(**(defaults | overrides))


# --- Forum ---


def build_forum_post(**overrides) -> ForumPost:
    defaults = {
        "id": _next_id("post"),
        "author_id": _next_id("user"),
        "author_name": "Test Author",
        "category": ForumCategory.GENERAL,
        "title": "Test Post",
        "content": "Test content for this post.",
        "created_at": _NOW,
    }
    return ForumPost(**(defaults | overrides))


def build_forum_reply(**overrides) -> ForumReply:
    defaults = {
        "id": _next_id("reply"),
        "post_id": _next_id("post"),
        "author_id": _next_id("user"),
        "author_name": "Reply Author",
        "content": "Test reply content.",
        "created_at": _NOW,
    }
    return ForumReply(**(defaults | overrides))


# --- Founders Network ---


def build_founder(**overrides) -> FounderProfile:
    defaults = {
        "user_id": _next_id("founder"),
        "name": "Jane Founder",
        "email": "jane@startup.com",
        "status": FounderStatus.ACTIVE,
        "joined_at": _NOW,
        "company_name": "Test Startup",
        "industry": "tech",
    }
    return FounderProfile(**(defaults | overrides))


# --- Recommendations ---


def build_recommendation(**overrides) -> Recommendation:
    defaults = {
        "program_code": "chase-ur",
        "action": "Transfer to Hyatt",
        "rationale": "Best value for hotel stays",
        "cpp_gain": Decimal("0.50"),
        "points_involved": 50000,
    }
    return Recommendation(**(defaults | overrides))


# --- Notifications ---


def build_alert(**overrides) -> Alert:
    defaults = {
        "id": _next_id("alert"),
        "alert_type": AlertType.SWEET_SPOT,
        "priority": AlertPriority.MEDIUM,
        "title": "Test Alert",
        "message": "A test alert message.",
        "program_code": "chase-ur",
        "action_url": None,
        "created_at": _NOW,
        "expires_at": None,
    }
    return Alert(**(defaults | overrides))


# --- Search ---


def build_award_result(**overrides) -> AwardResult:
    defaults = {
        "program": "united",
        "origin": "ORD",
        "destination": "NRT",
        "date": "2026-06-15",
        "cabin": "business",
        "points_required": 80000,
        "cash_value": Decimal("4500.00"),
        "source": "united.com",
        "direct": True,
        "available_seats": 2,
    }
    return AwardResult(**(defaults | overrides))
