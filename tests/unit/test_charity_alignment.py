"""Subscription charity alignment tests — TDD: written before implementation.

Tests the charity alignment domain: contribution calculation by tier.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from redeemflow.billing.charity_alignment import CharityAlignment, CharityAlignmentService
from redeemflow.billing.models import SubscriptionTier
from redeemflow.charity.donation_flow import DonationService, FakeDonationProvider
from redeemflow.charity.seed_data import CHARITY_NETWORK
from redeemflow.valuations.seed_data import PROGRAM_VALUATIONS


def _make_donation_service() -> DonationService:
    return DonationService(
        provider=FakeDonationProvider(),
        valuations=PROGRAM_VALUATIONS,
        charity_network=CHARITY_NETWORK,
    )


class TestCharityAlignment:
    def test_frozen_dataclass(self):
        ca = CharityAlignment(
            user_id="auth0|eric",
            charity_name="Girl Scouts of the USA",
            charity_state="TX",
            subscription_tier=SubscriptionTier.PRO,
            monthly_contribution=Decimal("1.25"),
            annual_contribution=Decimal("15.00"),
        )
        with pytest.raises(AttributeError):
            ca.user_id = "other"  # type: ignore[misc]

    def test_fields(self):
        ca = CharityAlignment(
            user_id="auth0|eric",
            charity_name="Girl Scouts of the USA",
            charity_state="TX",
            subscription_tier=SubscriptionTier.PRO,
            monthly_contribution=Decimal("1.25"),
            annual_contribution=Decimal("15.00"),
        )
        assert ca.subscription_tier == SubscriptionTier.PRO
        assert isinstance(ca.monthly_contribution, Decimal)
        assert isinstance(ca.annual_contribution, Decimal)


class TestCharityAlignmentService:
    def test_align_pro_tier(self):
        service = CharityAlignmentService(donation_service=_make_donation_service())
        alignment = service.align(
            user_id="auth0|eric",
            charity_name="Girl Scouts of the USA",
            charity_state="TX",
            tier=SubscriptionTier.PRO,
        )
        assert isinstance(alignment, CharityAlignment)
        # Pro: 5% of $24.99 = $1.2495 -> $1.25/month
        assert alignment.monthly_contribution == Decimal("1.25")
        # $1.25 * 12 = $15.00/year
        assert alignment.annual_contribution == Decimal("15.00")

    def test_align_premium_tier(self):
        service = CharityAlignmentService(donation_service=_make_donation_service())
        alignment = service.align(
            user_id="auth0|eric",
            charity_name="Girl Scouts of the USA",
            charity_state="TX",
            tier=SubscriptionTier.PREMIUM,
        )
        assert isinstance(alignment, CharityAlignment)
        # Premium: 2% of $9.99 = $0.1998 -> $0.20/month
        assert alignment.monthly_contribution == Decimal("0.20")
        # $0.20 * 12 = $2.40/year
        assert alignment.annual_contribution == Decimal("2.40")

    def test_get_alignment_none_before_set(self):
        service = CharityAlignmentService(donation_service=_make_donation_service())
        assert service.get_alignment("auth0|eric") is None

    def test_get_alignment_after_set(self):
        service = CharityAlignmentService(donation_service=_make_donation_service())
        service.align(
            user_id="auth0|eric",
            charity_name="Girl Scouts of the USA",
            charity_state="TX",
            tier=SubscriptionTier.PRO,
        )
        alignment = service.get_alignment("auth0|eric")
        assert alignment is not None
        assert alignment.user_id == "auth0|eric"

    def test_align_free_tier_zero_contribution(self):
        service = CharityAlignmentService(donation_service=_make_donation_service())
        alignment = service.align(
            user_id="auth0|eric",
            charity_name="Girl Scouts of the USA",
            charity_state="TX",
            tier=SubscriptionTier.FREE,
        )
        assert alignment.monthly_contribution == Decimal("0")
        assert alignment.annual_contribution == Decimal("0")
