"""Team points dashboard tests — TDD: written before implementation.

Tests the team dashboard domain: member model, dashboard aggregation.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from redeemflow.portfolio.fake_adapter import FakeBalanceFetcher
from redeemflow.portfolio.team_dashboard import TeamDashboard, TeamDashboardService, TeamMember
from redeemflow.valuations.seed_data import PROGRAM_VALUATIONS


class TestTeamMember:
    def test_frozen_dataclass(self):
        m = TeamMember(
            user_id="auth0|eric",
            name="Eric",
            cards=["UA", "MR"],
            total_points=207000,
            total_value=Decimal("2070.00"),
        )
        with pytest.raises(AttributeError):
            m.user_id = "other"  # type: ignore[misc]

    def test_fields(self):
        m = TeamMember(
            user_id="auth0|eric",
            name="Eric",
            cards=["UA", "MR"],
            total_points=207000,
            total_value=Decimal("2070.00"),
        )
        assert m.user_id == "auth0|eric"
        assert m.name == "Eric"
        assert isinstance(m.total_value, Decimal)


class TestTeamDashboard:
    def test_frozen_dataclass(self):
        d = TeamDashboard(
            team_name="Travel Team",
            members=[],
            total_points=0,
            total_value=Decimal("0"),
            card_count=0,
        )
        with pytest.raises(AttributeError):
            d.team_name = "Other"  # type: ignore[misc]

    def test_totals(self):
        m1 = TeamMember(
            user_id="auth0|eric",
            name="Eric",
            cards=["UA", "MR"],
            total_points=100000,
            total_value=Decimal("1000.00"),
        )
        m2 = TeamMember(
            user_id="auth0|steve",
            name="Steve",
            cards=["AA"],
            total_points=50000,
            total_value=Decimal("500.00"),
        )
        d = TeamDashboard(
            team_name="Travel Team",
            members=[m1, m2],
            total_points=150000,
            total_value=Decimal("1500.00"),
            card_count=3,
        )
        assert d.total_points == 150000
        assert d.total_value == Decimal("1500.00")
        assert d.card_count == 3


class TestTeamDashboardService:
    def test_build_dashboard_with_known_users(self):
        fetcher = FakeBalanceFetcher()
        service = TeamDashboardService(fetcher=fetcher, valuations=PROGRAM_VALUATIONS)
        dashboard = service.build_dashboard(
            team_name="Travel Team",
            member_ids=["auth0|eric", "auth0|steve"],
        )
        assert isinstance(dashboard, TeamDashboard)
        assert dashboard.team_name == "Travel Team"
        assert len(dashboard.members) == 2
        assert dashboard.total_points > 0
        assert dashboard.total_value > Decimal("0")
        assert dashboard.card_count > 0

    def test_unknown_user_returns_empty_member(self):
        fetcher = FakeBalanceFetcher()
        service = TeamDashboardService(fetcher=fetcher, valuations=PROGRAM_VALUATIONS)
        dashboard = service.build_dashboard(
            team_name="Solo Team",
            member_ids=["auth0|unknown_user"],
        )
        assert len(dashboard.members) == 1
        member = dashboard.members[0]
        assert member.total_points == 0
        assert member.total_value == Decimal("0")
        assert member.cards == []

    def test_build_dashboard_empty_member_list(self):
        fetcher = FakeBalanceFetcher()
        service = TeamDashboardService(fetcher=fetcher, valuations=PROGRAM_VALUATIONS)
        dashboard = service.build_dashboard(
            team_name="Empty Team",
            member_ids=[],
        )
        assert len(dashboard.members) == 0
        assert dashboard.total_points == 0
        assert dashboard.total_value == Decimal("0")
        assert dashboard.card_count == 0
