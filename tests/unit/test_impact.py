"""Impact tracking tests — TDD: written before implementation.

Tests the impact tracker domain: value objects and aggregation logic.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from redeemflow.charity.donation_flow import Donation, DonationStatus
from redeemflow.charity.impact import CommunityImpact, ImpactMetric, ImpactTracker


def _make_donation(
    *,
    id: str = "d-1",
    user_id: str = "auth0|eric",
    charity_name: str = "Girl Scouts of the USA",
    charity_state: str = "TX",
    program_code: str = "chase-ur",
    points_donated: int = 10000,
    dollar_value: Decimal = Decimal("170.00"),
    status: DonationStatus = DonationStatus.COMPLETED,
) -> Donation:
    return Donation(
        id=id,
        user_id=user_id,
        charity_name=charity_name,
        charity_state=charity_state,
        program_code=program_code,
        points_donated=points_donated,
        dollar_value=dollar_value,
        status=status,
        created_at="2026-03-09T00:00:00Z",
        completed_at="2026-03-09T00:00:01Z",
    )


class TestImpactMetric:
    def test_frozen_dataclass(self):
        m = ImpactMetric(
            user_id="auth0|eric",
            total_donated=Decimal("170.00"),
            donation_count=1,
            charities_supported=1,
            states_reached=1,
            top_charity="Girl Scouts of the USA",
        )
        with pytest.raises(AttributeError):
            m.total_donated = Decimal("0")  # type: ignore[misc]

    def test_default_top_charity_none(self):
        m = ImpactMetric(
            user_id="auth0|eric",
            total_donated=Decimal("0"),
            donation_count=0,
            charities_supported=0,
            states_reached=0,
        )
        assert m.top_charity is None


class TestCommunityImpact:
    def test_frozen_dataclass(self):
        c = CommunityImpact(
            total_donated=Decimal("500.00"),
            total_donors=3,
            total_donations=5,
            unique_charities=2,
            unique_states=2,
            top_charities=[("Girl Scouts of the USA", Decimal("300.00"))],
        )
        with pytest.raises(AttributeError):
            c.total_donors = 0  # type: ignore[misc]


class TestImpactTracker:
    def test_user_impact_with_donations(self):
        donations = [
            _make_donation(
                id="d-1", dollar_value=Decimal("100.00"), charity_name="Girl Scouts of the USA", charity_state="TX"
            ),
            _make_donation(id="d-2", dollar_value=Decimal("50.00"), charity_name="AAUW", charity_state="CA"),
        ]
        tracker = ImpactTracker(donations)
        impact = tracker.user_impact("auth0|eric")
        assert impact.total_donated == Decimal("150.00")
        assert impact.donation_count == 2
        assert impact.charities_supported == 2
        assert impact.states_reached == 2
        assert impact.top_charity == "Girl Scouts of the USA"

    def test_user_impact_no_donations(self):
        tracker = ImpactTracker([])
        impact = tracker.user_impact("auth0|eric")
        assert impact.total_donated == Decimal("0")
        assert impact.donation_count == 0
        assert impact.charities_supported == 0
        assert impact.states_reached == 0
        assert impact.top_charity is None

    def test_user_impact_filters_by_user(self):
        donations = [
            _make_donation(id="d-1", user_id="auth0|eric", dollar_value=Decimal("100.00")),
            _make_donation(id="d-2", user_id="auth0|steve", dollar_value=Decimal("50.00")),
        ]
        tracker = ImpactTracker(donations)
        eric_impact = tracker.user_impact("auth0|eric")
        assert eric_impact.total_donated == Decimal("100.00")
        assert eric_impact.donation_count == 1

    def test_user_impact_only_counts_completed(self):
        donations = [
            _make_donation(id="d-1", dollar_value=Decimal("100.00"), status=DonationStatus.COMPLETED),
            _make_donation(id="d-2", dollar_value=Decimal("50.00"), status=DonationStatus.FAILED),
        ]
        tracker = ImpactTracker(donations)
        impact = tracker.user_impact("auth0|eric")
        assert impact.total_donated == Decimal("100.00")
        assert impact.donation_count == 1

    def test_community_impact_aggregates_all_users(self):
        donations = [
            _make_donation(
                id="d-1",
                user_id="auth0|eric",
                dollar_value=Decimal("100.00"),
                charity_name="Girl Scouts of the USA",
                charity_state="TX",
            ),
            _make_donation(
                id="d-2", user_id="auth0|steve", dollar_value=Decimal("200.00"), charity_name="AAUW", charity_state="CA"
            ),
            _make_donation(
                id="d-3",
                user_id="auth0|eric",
                dollar_value=Decimal("50.00"),
                charity_name="Girl Scouts of the USA",
                charity_state="NY",
            ),
        ]
        tracker = ImpactTracker(donations)
        community = tracker.community_impact()
        assert community.total_donated == Decimal("350.00")
        assert community.total_donors == 2
        assert community.total_donations == 3
        assert community.unique_charities == 2
        assert community.unique_states == 3

    def test_community_impact_top_charities_sorted(self):
        donations = [
            _make_donation(id="d-1", dollar_value=Decimal("100.00"), charity_name="Girl Scouts of the USA"),
            _make_donation(id="d-2", dollar_value=Decimal("200.00"), charity_name="AAUW"),
            _make_donation(id="d-3", dollar_value=Decimal("50.00"), charity_name="Girl Scouts of the USA"),
        ]
        tracker = ImpactTracker(donations)
        community = tracker.community_impact()
        # AAUW has 200, Girl Scouts has 150 — AAUW should be first
        assert community.top_charities[0][0] == "AAUW"
        assert community.top_charities[0][1] == Decimal("200.00")

    def test_impact_by_state(self):
        donations = [
            _make_donation(id="d-1", dollar_value=Decimal("100.00"), charity_state="TX"),
            _make_donation(id="d-2", dollar_value=Decimal("50.00"), charity_state="CA"),
            _make_donation(id="d-3", dollar_value=Decimal("75.00"), charity_state="TX"),
        ]
        tracker = ImpactTracker(donations)
        by_state = tracker.impact_by_state()
        assert by_state["TX"] == Decimal("175.00")
        assert by_state["CA"] == Decimal("50.00")

    def test_impact_by_charity(self):
        donations = [
            _make_donation(id="d-1", dollar_value=Decimal("100.00"), charity_name="Girl Scouts of the USA"),
            _make_donation(id="d-2", dollar_value=Decimal("200.00"), charity_name="AAUW"),
            _make_donation(id="d-3", dollar_value=Decimal("50.00"), charity_name="Girl Scouts of the USA"),
        ]
        tracker = ImpactTracker(donations)
        by_charity = tracker.impact_by_charity()
        assert by_charity["Girl Scouts of the USA"] == Decimal("150.00")
        assert by_charity["AAUW"] == Decimal("200.00")
