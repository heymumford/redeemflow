"""Optimization domain — multi-traveler trip optimizer.

Plans optimal point redemptions across multiple travelers for a shared
destination, distributing bookings to maximize collective value.
Supports multigenerational trips where family members pool diverse
loyalty currencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from redeemflow.optimization.graph import TransferGraph
from redeemflow.optimization.models import TransferPath
from redeemflow.portfolio.models import PointBalance
from redeemflow.valuations.models import ProgramValuation


@dataclass(frozen=True)
class Traveler:
    """A traveler with their loyalty program balances."""

    name: str
    balances: list[PointBalance]


@dataclass(frozen=True)
class TravelerBooking:
    """A booking assignment for a specific traveler."""

    traveler_name: str
    program_code: str
    points_used: int
    booking_type: str  # "flight" or "hotel"
    estimated_value: Decimal
    transfer_path: TransferPath | None


@dataclass(frozen=True)
class MultiTravelerPlan:
    """Complete multi-traveler trip plan with optimized bookings."""

    destination: str
    travelers: list[Traveler]
    bookings: list[TravelerBooking]
    total_points_used: int
    total_estimated_value: Decimal
    total_estimated_savings: Decimal


class MultiTravelerOptimizer:
    """Optimizes point redemptions across multiple travelers for a shared trip."""

    def __init__(self, graph: TransferGraph, valuations: dict[str, ProgramValuation]) -> None:
        self._graph = graph
        self._valuations = valuations

    def plan(self, destination: str, travelers: list[Traveler]) -> MultiTravelerPlan:
        """Create an optimized multi-traveler plan.

        Analyzes each traveler's balances and assigns bookings to maximize
        collective value. Travelers with airline-transferable currencies get
        flight bookings; hotel-transferable currencies get hotel bookings.
        """
        if not travelers:
            return MultiTravelerPlan(
                destination=destination,
                travelers=[],
                bookings=[],
                total_points_used=0,
                total_estimated_value=Decimal("0"),
                total_estimated_savings=Decimal("0"),
            )

        bookings: list[TravelerBooking] = []

        # Score each traveler's best options and assign complementary bookings
        traveler_options = self._score_all_travelers(travelers)

        # Assign best flight paths first, then hotels
        assigned_flight_travelers: set[str] = set()
        assigned_hotel_travelers: set[str] = set()

        # Sort by effective CPP descending — best value first
        flight_options = sorted(
            [(t, opt) for t, opt in traveler_options if opt["type"] == "flight"],
            key=lambda x: x[1]["effective_cpp"],
            reverse=True,
        )
        hotel_options = sorted(
            [(t, opt) for t, opt in traveler_options if opt["type"] == "hotel"],
            key=lambda x: x[1]["effective_cpp"],
            reverse=True,
        )

        # Assign flights — one per traveler
        for traveler, opt in flight_options:
            if traveler.name not in assigned_flight_travelers:
                bookings.append(
                    TravelerBooking(
                        traveler_name=traveler.name,
                        program_code=opt["program_code"],
                        points_used=opt["points_needed"],
                        booking_type="flight",
                        estimated_value=opt["estimated_value"],
                        transfer_path=opt.get("path"),
                    )
                )
                assigned_flight_travelers.add(traveler.name)

        # Assign hotels — one per traveler (complementary to flights)
        for traveler, opt in hotel_options:
            if traveler.name not in assigned_hotel_travelers:
                bookings.append(
                    TravelerBooking(
                        traveler_name=traveler.name,
                        program_code=opt["program_code"],
                        points_used=opt["points_needed"],
                        booking_type="hotel",
                        estimated_value=opt["estimated_value"],
                        transfer_path=opt.get("path"),
                    )
                )
                assigned_hotel_travelers.add(traveler.name)

        total_points = sum(b.points_used for b in bookings)
        total_value = sum(b.estimated_value for b in bookings)
        # Estimate savings as 60% of total value (points booking vs cash)
        total_savings = (total_value * Decimal("0.6")).quantize(Decimal("0.01"))

        return MultiTravelerPlan(
            destination=destination,
            travelers=travelers,
            bookings=bookings,
            total_points_used=total_points,
            total_estimated_value=total_value.quantize(Decimal("0.01")),
            total_estimated_savings=total_savings,
        )

    def _score_all_travelers(self, travelers: list[Traveler]) -> list[tuple[Traveler, dict]]:
        """Score each traveler's best flight and hotel options."""
        results: list[tuple[Traveler, dict]] = []

        for traveler in travelers:
            for balance in traveler.balances:
                paths = self._graph.find_paths(balance.program_code, max_hops=2)
                for path in paths:
                    if balance.points < path.source_points_needed:
                        continue

                    booking_type = self._classify_booking(path)
                    val = self._valuations.get(balance.program_code)
                    median_cpp = val.median_cpp if val else balance.cpp_baseline
                    estimated_value = (Decimal(path.source_points_needed) * median_cpp / Decimal(100)).quantize(
                        Decimal("0.01")
                    )

                    results.append(
                        (
                            traveler,
                            {
                                "program_code": balance.program_code,
                                "points_needed": path.source_points_needed,
                                "effective_cpp": path.effective_cpp,
                                "estimated_value": estimated_value,
                                "type": booking_type,
                                "path": path,
                                "description": path.redemption.description,
                            },
                        )
                    )

        return results

    def _classify_booking(self, path: TransferPath) -> str:
        """Classify a transfer path as flight or hotel based on redemption description."""
        desc = path.redemption.description.lower()
        hotel_keywords = {"hotel", "hyatt", "marriott", "hilton", "ihg", "resort", "ziva", "zilara"}
        for keyword in hotel_keywords:
            if keyword in desc:
                return "hotel"
        return "flight"
