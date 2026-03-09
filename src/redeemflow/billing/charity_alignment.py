"""Subscription charity alignment — percentage of subscription fees directed to charity.

Beck: The simplest thing that could work.
Fowler: Frozen dataclass for alignment, service for lifecycle.

Pro tier: 5% of $24.99 = $1.25/month = $15.00/year
Premium tier: 2% of $9.99 = $0.20/month = $2.40/year
Free tier: $0
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from redeemflow.billing.models import PREMIUM_PLAN, PRO_PLAN, SubscriptionTier
from redeemflow.charity.donation_flow import DonationService


@dataclass(frozen=True)
class CharityAlignment:
    user_id: str
    charity_name: str
    charity_state: str
    subscription_tier: SubscriptionTier
    monthly_contribution: Decimal
    annual_contribution: Decimal


# Contribution rates by tier
_CONTRIBUTION_RATES: dict[SubscriptionTier, Decimal] = {
    SubscriptionTier.FREE: Decimal("0"),
    SubscriptionTier.PREMIUM: Decimal("0.02"),
    SubscriptionTier.PRO: Decimal("0.05"),
}

_MONTHLY_PRICES: dict[SubscriptionTier, Decimal] = {
    SubscriptionTier.FREE: Decimal("0"),
    SubscriptionTier.PREMIUM: PREMIUM_PLAN.monthly_price,
    SubscriptionTier.PRO: PRO_PLAN.monthly_price,
}


class CharityAlignmentService:
    """Manages user charity alignment — maps subscription fees to charitable contributions."""

    def __init__(self, donation_service: DonationService) -> None:
        self._donation_service = donation_service
        self._alignments: dict[str, CharityAlignment] = {}

    def align(
        self,
        user_id: str,
        charity_name: str,
        charity_state: str,
        tier: SubscriptionTier,
    ) -> CharityAlignment:
        rate = _CONTRIBUTION_RATES.get(tier, Decimal("0"))
        monthly_price = _MONTHLY_PRICES.get(tier, Decimal("0"))

        monthly_contribution = (monthly_price * rate).quantize(Decimal("0.01"))
        annual_contribution = (monthly_contribution * Decimal("12")).quantize(Decimal("0.01"))

        alignment = CharityAlignment(
            user_id=user_id,
            charity_name=charity_name,
            charity_state=charity_state,
            subscription_tier=tier,
            monthly_contribution=monthly_contribution,
            annual_contribution=annual_contribution,
        )
        self._alignments[user_id] = alignment
        return alignment

    def get_alignment(self, user_id: str) -> CharityAlignment | None:
        return self._alignments.get(user_id)
