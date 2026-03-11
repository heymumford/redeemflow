"""Hotel transfer analysis — value assessment for hotel-to-airline transfers.

Fowler: Separate query from mutation. This module is pure read-model projection.
Beck: Name things for what they do, not what they are.

Hotel transfers (Marriott 3:1, Hilton 10:1, IHG 5:1) are generally poor value
compared to direct hotel redemptions. This module quantifies the tradeoff so
users can make informed decisions.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from redeemflow.optimization.graph import TransferGraph


@dataclass(frozen=True)
class HotelTransferAssessment:
    """Assessment of a hotel-to-airline transfer option."""

    hotel_program: str
    airline_program: str
    transfer_ratio: float
    hotel_points_needed: int
    airline_miles_received: int
    hotel_cpp_if_redeemed: Decimal
    airline_cpp_if_transferred: Decimal
    value_ratio: Decimal  # airline_cpp / hotel_cpp — below 1.0 means hotel redemption wins
    recommendation: str  # "transfer", "redeem_hotel", "situational"
    rationale: str


@dataclass(frozen=True)
class HotelProgramSummary:
    """Summary of a hotel program's transfer economics."""

    program: str
    airline_partners: list[str]
    transfer_ratio: float
    best_direct_cpp: Decimal
    best_transfer_cpp: Decimal
    transfer_penalty: Decimal  # How much value lost by transferring vs redeeming
    assessments: list[HotelTransferAssessment]


def assess_hotel_transfer(
    graph: TransferGraph,
    hotel_program: str,
    airline_program: str,
    hotel_points: int,
) -> HotelTransferAssessment | None:
    """Assess whether transferring hotel points to an airline is worthwhile.

    Compares the hotel CPP (if redeemed directly) against the airline CPP
    (if transferred then redeemed). Most hotel-to-airline transfers destroy value.
    """
    partners = graph.get_partners_from(hotel_program)
    partner = next(
        (p for p in partners if p.target_program == airline_program),
        None,
    )
    if partner is None:
        return None

    # Best direct hotel redemption CPP
    hotel_redemptions = graph.get_redemptions(hotel_program)
    viable_hotel = [r for r in hotel_redemptions if hotel_points >= r.points_required]
    hotel_cpp = Decimal("0")
    if viable_hotel:
        best_hotel = max(viable_hotel, key=lambda r: r.cpp)
        hotel_cpp = Decimal(str(round(best_hotel.cpp, 2)))

    # Airline CPP after transfer
    airline_miles = int(hotel_points * partner.effective_ratio)
    airline_redemptions = graph.get_redemptions(airline_program)
    viable_airline = [r for r in airline_redemptions if airline_miles >= r.points_required]
    airline_cpp = Decimal("0")
    if viable_airline:
        best_airline = max(viable_airline, key=lambda r: r.cpp)
        # Calculate CPP relative to original hotel points spent
        airline_cpp = Decimal(str(round(best_airline.cash_value / hotel_points * 100, 2)))

    # Value ratio
    value_ratio = (airline_cpp / hotel_cpp).quantize(Decimal("0.01")) if hotel_cpp > 0 else Decimal("0")

    # Recommendation logic
    if value_ratio > Decimal("1.2"):
        recommendation = "transfer"
        rationale = f"Transfer yields {value_ratio}x the value of direct hotel redemption"
    elif value_ratio == Decimal("0"):
        recommendation = "redeem_hotel"
        rationale = "No viable airline redemption after transfer — redeem hotel directly"
    elif value_ratio < Decimal("0.8"):
        recommendation = "redeem_hotel"
        multiplier = (Decimal("1") / value_ratio).quantize(Decimal("0.1"))
        rationale = f"Direct hotel redemption is {multiplier}x better"
    else:
        recommendation = "situational"
        rationale = "Values are close — depends on whether you need flights or hotels"

    return HotelTransferAssessment(
        hotel_program=hotel_program,
        airline_program=airline_program,
        transfer_ratio=partner.effective_ratio,
        hotel_points_needed=hotel_points,
        airline_miles_received=airline_miles,
        hotel_cpp_if_redeemed=hotel_cpp,
        airline_cpp_if_transferred=airline_cpp,
        value_ratio=value_ratio,
        recommendation=recommendation,
        rationale=rationale,
    )


def summarize_hotel_program(
    graph: TransferGraph,
    hotel_program: str,
    sample_points: int = 100000,
) -> HotelProgramSummary:
    """Summarize a hotel program's transfer economics."""
    partners = graph.get_partners_from(hotel_program)
    airline_partners = [p for p in partners if p.target_program not in ("marriott", "hilton", "ihg", "hyatt")]

    assessments = []
    for partner in airline_partners:
        assessment = assess_hotel_transfer(graph, hotel_program, partner.target_program, sample_points)
        if assessment is not None:
            assessments.append(assessment)

    # Best direct hotel CPP
    hotel_redemptions = graph.get_redemptions(hotel_program)
    viable_hotel = [r for r in hotel_redemptions if sample_points >= r.points_required]
    best_direct_cpp = Decimal("0")
    if viable_hotel:
        best_direct_cpp = Decimal(str(round(max(r.cpp for r in viable_hotel), 2)))

    # Best transfer CPP
    best_transfer_cpp = max(
        (a.airline_cpp_if_transferred for a in assessments),
        default=Decimal("0"),
    )

    transfer_penalty = best_direct_cpp - best_transfer_cpp if best_direct_cpp > best_transfer_cpp else Decimal("0")

    return HotelProgramSummary(
        program=hotel_program,
        airline_partners=[p.target_program for p in airline_partners],
        transfer_ratio=airline_partners[0].effective_ratio if airline_partners else 0.0,
        best_direct_cpp=best_direct_cpp,
        best_transfer_cpp=best_transfer_cpp,
        transfer_penalty=transfer_penalty,
        assessments=assessments,
    )
