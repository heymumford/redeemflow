"""Tests for conference travel planner — women's conference optimization."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from redeemflow.optimization.graph import TransferGraph
from redeemflow.optimization.seed_data import ALL_PARTNERS, REDEMPTION_OPTIONS
from redeemflow.portfolio.models import PointBalance
from redeemflow.search.conference_planner import (
    Conference,
    ConferencePlanner,
    ConferenceTravelPlan,
    WOMEN_CONFERENCES,
)
from redeemflow.search.safety_scores import FakeSafetyDataProvider
from redeemflow.valuations.seed_data import PROGRAM_VALUATIONS


def _build_graph() -> TransferGraph:
    graph = TransferGraph()
    for p in ALL_PARTNERS:
        graph.add_partner(p)
    for r in REDEMPTION_OPTIONS:
        graph.add_redemption(r)
    return graph


class TestConference:
    def test_frozen_dataclass(self) -> None:
        conf = Conference(
            name="Grace Hopper Celebration",
            city="Orlando",
            country="US",
            start_date="2026-10-06",
            end_date="2026-10-09",
            category="tech",
            typical_attendees=25000,
            website="https://ghc.anitab.org",
        )
        assert conf.name == "Grace Hopper Celebration"
        assert conf.city == "Orlando"
        assert conf.country == "US"
        assert conf.start_date == "2026-10-06"
        assert conf.end_date == "2026-10-09"
        assert conf.category == "tech"
        assert conf.typical_attendees == 25000
        assert conf.website == "https://ghc.anitab.org"

    def test_immutable(self) -> None:
        conf = Conference(
            name="Test",
            city="Test",
            country="US",
            start_date="2026-01-01",
            end_date="2026-01-02",
            category="tech",
        )
        with pytest.raises(FrozenInstanceError):
            conf.name = "Changed"  # type: ignore[misc]

    def test_optional_fields_default_none(self) -> None:
        conf = Conference(
            name="Test",
            city="Test",
            country="US",
            start_date="2026-01-01",
            end_date="2026-01-02",
            category="tech",
        )
        assert conf.typical_attendees is None
        assert conf.website is None


class TestConferenceTravelPlan:
    def test_frozen_dataclass(self) -> None:
        conf = Conference(
            name="Test",
            city="Orlando",
            country="US",
            start_date="2026-01-01",
            end_date="2026-01-03",
            category="tech",
        )
        plan = ConferenceTravelPlan(
            conference=conf,
            origin_city="New York",
            recommended_flights=[{"airline": "Delta", "points": 15000}],
            recommended_hotels=[{"hotel": "Hyatt Regency", "points": 12000}],
            points_options=[{"program": "chase-ur", "points_needed": 27000}],
            estimated_savings=Decimal("450.00"),
            safety_info=None,
        )
        assert plan.conference.name == "Test"
        assert plan.origin_city == "New York"
        assert len(plan.recommended_flights) == 1
        assert len(plan.recommended_hotels) == 1
        assert len(plan.points_options) == 1
        assert plan.estimated_savings == Decimal("450.00")
        assert plan.safety_info is None

    def test_estimated_savings_is_decimal(self) -> None:
        conf = Conference(
            name="Test",
            city="Test",
            country="US",
            start_date="2026-01-01",
            end_date="2026-01-02",
            category="tech",
        )
        plan = ConferenceTravelPlan(
            conference=conf,
            origin_city="SFO",
            recommended_flights=[],
            recommended_hotels=[],
            points_options=[],
            estimated_savings=Decimal("123.45"),
            safety_info=None,
        )
        assert isinstance(plan.estimated_savings, Decimal)

    def test_immutable(self) -> None:
        conf = Conference(
            name="Test",
            city="Test",
            country="US",
            start_date="2026-01-01",
            end_date="2026-01-02",
            category="tech",
        )
        plan = ConferenceTravelPlan(
            conference=conf,
            origin_city="SFO",
            recommended_flights=[],
            recommended_hotels=[],
            points_options=[],
            estimated_savings=Decimal("0"),
            safety_info=None,
        )
        with pytest.raises(FrozenInstanceError):
            plan.origin_city = "LAX"  # type: ignore[misc]


class TestConferencePlanner:
    def setup_method(self) -> None:
        self.graph = _build_graph()
        self.safety = FakeSafetyDataProvider()
        self.planner = ConferencePlanner(
            graph=self.graph,
            valuations=PROGRAM_VALUATIONS,
            safety_provider=self.safety,
        )
        self.balances = [
            PointBalance(program_code="chase-ur", points=100000, cpp_baseline=Decimal("2.0")),
            PointBalance(program_code="amex-mr", points=80000, cpp_baseline=Decimal("2.0")),
        ]

    def test_plan_with_known_conference_and_balances(self) -> None:
        conf = WOMEN_CONFERENCES[0]  # WBENC Nashville
        plan = self.planner.plan(conf, origin_city="New York", balances=self.balances)
        assert isinstance(plan, ConferenceTravelPlan)
        assert plan.conference == conf
        assert plan.origin_city == "New York"
        assert isinstance(plan.estimated_savings, Decimal)

    def test_plan_includes_safety_info_when_available(self) -> None:
        conf = Conference(
            name="Test Tokyo Conf",
            city="Tokyo",
            country="Japan",
            start_date="2026-05-01",
            end_date="2026-05-03",
            category="tech",
        )
        plan = self.planner.plan(conf, origin_city="SFO", balances=self.balances)
        assert plan.safety_info is not None
        assert plan.safety_info.city == "Tokyo"

    def test_plan_points_options_populated(self) -> None:
        conf = WOMEN_CONFERENCES[0]
        plan = self.planner.plan(conf, origin_city="New York", balances=self.balances)
        assert isinstance(plan.points_options, list)
        # With 100K Chase UR + 80K Amex MR, there should be some options
        assert len(plan.points_options) >= 1

    def test_plan_without_safety_provider(self) -> None:
        planner = ConferencePlanner(
            graph=self.graph,
            valuations=PROGRAM_VALUATIONS,
            safety_provider=None,
        )
        conf = WOMEN_CONFERENCES[0]
        plan = planner.plan(conf, origin_city="New York", balances=self.balances)
        assert plan.safety_info is None

    def test_plan_with_empty_balances(self) -> None:
        conf = WOMEN_CONFERENCES[0]
        plan = self.planner.plan(conf, origin_city="New York", balances=[])
        assert isinstance(plan, ConferenceTravelPlan)
        assert len(plan.points_options) == 0
        assert plan.estimated_savings == Decimal("0")


class TestWomenConferences:
    def test_seed_data_has_at_least_5_entries(self) -> None:
        assert len(WOMEN_CONFERENCES) >= 5

    def test_all_have_required_fields(self) -> None:
        for conf in WOMEN_CONFERENCES:
            assert conf.name
            assert conf.city
            assert conf.country
            assert conf.start_date
            assert conf.end_date
            assert conf.category in {"tech", "business", "finance", "women_leadership"}

    def test_grace_hopper_present(self) -> None:
        names = {c.name for c in WOMEN_CONFERENCES}
        assert "Grace Hopper Celebration" in names

    def test_wbenc_present(self) -> None:
        names = {c.name for c in WOMEN_CONFERENCES}
        assert "WBENC National Conference" in names
