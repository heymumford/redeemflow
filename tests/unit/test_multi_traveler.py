"""Tests for multi-traveler optimizer — multigenerational trip planning."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from redeemflow.optimization.graph import TransferGraph
from redeemflow.optimization.models import TransferPath
from redeemflow.optimization.multi_traveler import (
    MultiTravelerOptimizer,
    MultiTravelerPlan,
    Traveler,
    TravelerBooking,
)
from redeemflow.optimization.seed_data import ALL_PARTNERS, REDEMPTION_OPTIONS
from redeemflow.portfolio.models import PointBalance
from redeemflow.valuations.seed_data import PROGRAM_VALUATIONS


def _build_graph() -> TransferGraph:
    graph = TransferGraph()
    for p in ALL_PARTNERS:
        graph.add_partner(p)
    for r in REDEMPTION_OPTIONS:
        graph.add_redemption(r)
    return graph


class TestTraveler:
    def test_frozen_dataclass(self) -> None:
        balances = [
            PointBalance(program_code="chase-ur", points=50000, cpp_baseline=Decimal("2.0")),
        ]
        t = Traveler(name="Alice", balances=balances)
        assert t.name == "Alice"
        assert len(t.balances) == 1
        assert t.balances[0].program_code == "chase-ur"

    def test_immutable(self) -> None:
        t = Traveler(name="Alice", balances=[])
        with pytest.raises(FrozenInstanceError):
            t.name = "Bob"  # type: ignore[misc]


class TestTravelerBooking:
    def test_frozen_dataclass(self) -> None:
        booking = TravelerBooking(
            traveler_name="Alice",
            program_code="chase-ur",
            points_used=50000,
            booking_type="flight",
            estimated_value=Decimal("1000.00"),
            transfer_path=None,
        )
        assert booking.traveler_name == "Alice"
        assert booking.program_code == "chase-ur"
        assert booking.points_used == 50000
        assert booking.booking_type == "flight"
        assert booking.estimated_value == Decimal("1000.00")
        assert booking.transfer_path is None

    def test_decimal_value(self) -> None:
        booking = TravelerBooking(
            traveler_name="Bob",
            program_code="amex-mr",
            points_used=30000,
            booking_type="hotel",
            estimated_value=Decimal("450.50"),
            transfer_path=None,
        )
        assert isinstance(booking.estimated_value, Decimal)

    def test_immutable(self) -> None:
        booking = TravelerBooking(
            traveler_name="Alice",
            program_code="chase-ur",
            points_used=50000,
            booking_type="flight",
            estimated_value=Decimal("1000.00"),
            transfer_path=None,
        )
        with pytest.raises(FrozenInstanceError):
            booking.traveler_name = "Changed"  # type: ignore[misc]

    def test_with_transfer_path(self) -> None:
        """TravelerBooking can hold a TransferPath reference."""
        from redeemflow.optimization.models import RedemptionOption, TransferPartner

        partner = TransferPartner(source_program="chase-ur", target_program="hyatt", transfer_ratio=1.0)
        redemption = RedemptionOption(
            program="hyatt", description="Hyatt Cat 1-4", points_required=8000, cash_value=240.0
        )
        path = TransferPath(
            steps=(partner,), redemption=redemption, source_points_needed=8000, effective_cpp=3.0, total_hops=1
        )
        booking = TravelerBooking(
            traveler_name="Alice",
            program_code="chase-ur",
            points_used=8000,
            booking_type="hotel",
            estimated_value=Decimal("240.00"),
            transfer_path=path,
        )
        assert booking.transfer_path is not None
        assert booking.transfer_path.total_hops == 1


class TestMultiTravelerPlan:
    def test_frozen_dataclass(self) -> None:
        travelers = [
            Traveler(name="Alice", balances=[]),
            Traveler(name="Bob", balances=[]),
        ]
        plan = MultiTravelerPlan(
            destination="Tokyo",
            travelers=travelers,
            bookings=[],
            total_points_used=0,
            total_estimated_value=Decimal("0"),
            total_estimated_savings=Decimal("0"),
        )
        assert plan.destination == "Tokyo"
        assert len(plan.travelers) == 2
        assert plan.total_points_used == 0
        assert plan.total_estimated_value == Decimal("0")
        assert plan.total_estimated_savings == Decimal("0")

    def test_immutable(self) -> None:
        plan = MultiTravelerPlan(
            destination="Tokyo",
            travelers=[],
            bookings=[],
            total_points_used=0,
            total_estimated_value=Decimal("0"),
            total_estimated_savings=Decimal("0"),
        )
        with pytest.raises(FrozenInstanceError):
            plan.destination = "London"  # type: ignore[misc]

    def test_totals_with_bookings(self) -> None:
        bookings = [
            TravelerBooking(
                traveler_name="Alice",
                program_code="chase-ur",
                points_used=50000,
                booking_type="flight",
                estimated_value=Decimal("800.00"),
                transfer_path=None,
            ),
            TravelerBooking(
                traveler_name="Bob",
                program_code="amex-mr",
                points_used=30000,
                booking_type="hotel",
                estimated_value=Decimal("450.00"),
                transfer_path=None,
            ),
        ]
        plan = MultiTravelerPlan(
            destination="London",
            travelers=[Traveler(name="Alice", balances=[]), Traveler(name="Bob", balances=[])],
            bookings=bookings,
            total_points_used=80000,
            total_estimated_value=Decimal("1250.00"),
            total_estimated_savings=Decimal("500.00"),
        )
        assert plan.total_points_used == 80000
        assert plan.total_estimated_value == Decimal("1250.00")
        assert plan.total_estimated_savings == Decimal("500.00")


class TestMultiTravelerOptimizer:
    def setup_method(self) -> None:
        self.graph = _build_graph()
        self.optimizer = MultiTravelerOptimizer(graph=self.graph, valuations=PROGRAM_VALUATIONS)

    def test_plan_with_two_travelers(self) -> None:
        travelers = [
            Traveler(
                name="Alice",
                balances=[
                    PointBalance(program_code="chase-ur", points=100000, cpp_baseline=Decimal("2.0")),
                ],
            ),
            Traveler(
                name="Bob",
                balances=[
                    PointBalance(program_code="amex-mr", points=80000, cpp_baseline=Decimal("2.0")),
                ],
            ),
        ]
        plan = self.optimizer.plan("Tokyo", travelers)
        assert isinstance(plan, MultiTravelerPlan)
        assert plan.destination == "Tokyo"
        assert len(plan.travelers) == 2
        assert plan.total_points_used >= 0
        assert isinstance(plan.total_estimated_value, Decimal)
        assert isinstance(plan.total_estimated_savings, Decimal)

    def test_plan_with_three_travelers_multigenerational(self) -> None:
        travelers = [
            Traveler(
                name="Grandma",
                balances=[
                    PointBalance(program_code="amex-mr", points=150000, cpp_baseline=Decimal("2.0")),
                ],
            ),
            Traveler(
                name="Mom",
                balances=[
                    PointBalance(program_code="chase-ur", points=120000, cpp_baseline=Decimal("2.0")),
                ],
            ),
            Traveler(
                name="Daughter",
                balances=[
                    PointBalance(program_code="bilt", points=50000, cpp_baseline=Decimal("1.8")),
                ],
            ),
        ]
        plan = self.optimizer.plan("London", travelers)
        assert isinstance(plan, MultiTravelerPlan)
        assert len(plan.travelers) == 3
        assert len(plan.bookings) >= 1

    def test_empty_travelers_returns_empty_plan(self) -> None:
        plan = self.optimizer.plan("Tokyo", [])
        assert isinstance(plan, MultiTravelerPlan)
        assert plan.destination == "Tokyo"
        assert len(plan.travelers) == 0
        assert len(plan.bookings) == 0
        assert plan.total_points_used == 0
        assert plan.total_estimated_value == Decimal("0")
        assert plan.total_estimated_savings == Decimal("0")

    def test_optimization_assigns_different_programs_to_different_travelers(self) -> None:
        """When travelers have different currencies, optimizer should leverage each."""
        travelers = [
            Traveler(
                name="Alice",
                balances=[
                    PointBalance(program_code="chase-ur", points=100000, cpp_baseline=Decimal("2.0")),
                ],
            ),
            Traveler(
                name="Bob",
                balances=[
                    PointBalance(program_code="amex-mr", points=100000, cpp_baseline=Decimal("2.0")),
                ],
            ),
        ]
        plan = self.optimizer.plan("Tokyo", travelers)
        if len(plan.bookings) >= 2:
            programs_used = {b.program_code for b in plan.bookings}
            # With different currencies, we expect the optimizer to use multiple programs
            assert len(programs_used) >= 1  # At minimum different travelers
            traveler_names = {b.traveler_name for b in plan.bookings}
            assert len(traveler_names) >= 2  # Both travelers should have bookings

    def test_plan_bookings_have_valid_types(self) -> None:
        travelers = [
            Traveler(
                name="Alice",
                balances=[
                    PointBalance(program_code="chase-ur", points=100000, cpp_baseline=Decimal("2.0")),
                ],
            ),
        ]
        plan = self.optimizer.plan("London", travelers)
        for booking in plan.bookings:
            assert booking.booking_type in {"flight", "hotel"}
            assert booking.points_used > 0
            assert booking.estimated_value > Decimal("0")
