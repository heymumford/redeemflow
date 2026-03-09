"""Billing domain — subscription value objects.

Frozen dataclasses for all value objects. Decimal for all financial math.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum


class SubscriptionTier(str, Enum):
    FREE = "free"
    PREMIUM = "premium"
    PRO = "pro"


@dataclass(frozen=True)
class SubscriptionPlan:
    tier: SubscriptionTier
    name: str
    monthly_price: Decimal
    annual_price: Decimal
    features: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Subscription:
    id: str
    user_id: str
    tier: SubscriptionTier
    status: str  # active, cancelled, past_due
    current_period_start: str
    current_period_end: str
    stripe_subscription_id: str | None = None


PREMIUM_PLAN = SubscriptionPlan(
    tier=SubscriptionTier.PREMIUM,
    name="Premium",
    monthly_price=Decimal("9.99"),
    annual_price=Decimal("99.99"),
    features=[
        "AwardWallet balance sync",
        "Points expiration alerts",
        "Transfer recommendations",
        "Premium support",
    ],
)

PRO_PLAN = SubscriptionPlan(
    tier=SubscriptionTier.PRO,
    name="Pro",
    monthly_price=Decimal("24.99"),
    annual_price=Decimal("249.99"),
    features=[
        "Everything in Premium",
        "Advanced optimization engine",
        "Multi-person household tracking",
        "Real-time award search",
        "Priority support",
    ],
)
