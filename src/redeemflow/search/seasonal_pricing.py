"""Seasonal pricing intelligence — peak/off-peak patterns and booking windows.

Beck: Seasonal data is a projection — inputs are historical patterns, outputs are advisories.
Fowler: Specification — season constraints as composable predicates.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class Season(str, Enum):
    PEAK = "peak"
    SHOULDER = "shoulder"
    OFF_PEAK = "off_peak"


class BookingUrgency(str, Enum):
    BOOK_NOW = "book_now"
    GOOD_TIME = "good_time"
    WAIT = "wait"
    AVOID = "avoid"


@dataclass(frozen=True)
class SeasonalPattern:
    """Pricing pattern for a route in a given season."""

    route: str
    season: Season
    months: list[int]  # 1-12
    avg_points: int
    avg_cash: Decimal
    availability_rating: str  # high, medium, low
    demand_level: str  # high, medium, low
    notes: str = ""


@dataclass(frozen=True)
class BookingWindow:
    """Optimal booking window advice."""

    route: str
    travel_month: int
    ideal_book_months_ahead: int
    urgency: BookingUrgency
    reason: str
    savings_vs_last_minute_pct: int  # e.g., 30 = 30% savings


@dataclass(frozen=True)
class SeasonalAdvisory:
    """Complete seasonal analysis for a route."""

    route: str
    current_season: Season
    current_month: int
    patterns: list[SeasonalPattern]
    best_value_months: list[int]
    worst_value_months: list[int]
    booking_window: BookingWindow
    price_index: Decimal  # 100 = average, >100 = expensive, <100 = cheap


# Seed data for common routes
_ROUTE_PATTERNS: dict[str, list[SeasonalPattern]] = {
    "SFO-NRT": [
        SeasonalPattern(
            "SFO-NRT",
            Season.PEAK,
            [6, 7, 8, 12],
            80000,
            Decimal("1800"),
            "low",
            "high",
            "Cherry blossom (Mar-Apr) and summer drive peak demand",
        ),
        SeasonalPattern(
            "SFO-NRT",
            Season.SHOULDER,
            [3, 4, 5, 9, 10],
            65000,
            Decimal("1200"),
            "medium",
            "medium",
            "Spring and fall offer best weather with moderate pricing",
        ),
        SeasonalPattern(
            "SFO-NRT",
            Season.OFF_PEAK,
            [1, 2, 11],
            50000,
            Decimal("800"),
            "high",
            "low",
            "Winter months except holidays offer best availability",
        ),
    ],
    "JFK-LHR": [
        SeasonalPattern(
            "JFK-LHR",
            Season.PEAK,
            [6, 7, 8],
            70000,
            Decimal("2200"),
            "low",
            "high",
            "Summer travel dominates transatlantic demand",
        ),
        SeasonalPattern(
            "JFK-LHR",
            Season.SHOULDER,
            [4, 5, 9, 10, 12],
            55000,
            Decimal("1400"),
            "medium",
            "medium",
            "Spring/fall and holiday season",
        ),
        SeasonalPattern(
            "JFK-LHR",
            Season.OFF_PEAK,
            [1, 2, 3, 11],
            40000,
            Decimal("700"),
            "high",
            "low",
            "January-March offers exceptional award availability",
        ),
    ],
    "LAX-CDG": [
        SeasonalPattern(
            "LAX-CDG", Season.PEAK, [6, 7, 8], 75000, Decimal("2000"), "low", "high", "Summer Paris is peak season"
        ),
        SeasonalPattern(
            "LAX-CDG",
            Season.SHOULDER,
            [4, 5, 9, 10],
            60000,
            Decimal("1300"),
            "medium",
            "medium",
            "Spring and fall are ideal for Paris weather and pricing",
        ),
        SeasonalPattern(
            "LAX-CDG",
            Season.OFF_PEAK,
            [1, 2, 3, 11, 12],
            45000,
            Decimal("750"),
            "high",
            "low",
            "Winter months have the best award availability",
        ),
    ],
}


def get_season(route: str, month: int) -> Season:
    """Determine the season for a route in a given month."""
    patterns = _ROUTE_PATTERNS.get(route, [])
    for p in patterns:
        if month in p.months:
            return p.season
    # Default heuristic
    if month in (6, 7, 8, 12):
        return Season.PEAK
    if month in (3, 4, 5, 9, 10):
        return Season.SHOULDER
    return Season.OFF_PEAK


def get_seasonal_patterns(route: str) -> list[SeasonalPattern]:
    """Get all seasonal patterns for a route."""
    return _ROUTE_PATTERNS.get(route, [])


def compute_price_index(route: str, month: int) -> Decimal:
    """Compute a price index (100 = average) for a route in a given month.

    Values >100 indicate above-average pricing, <100 indicate below-average.
    """
    patterns = _ROUTE_PATTERNS.get(route)
    if not patterns:
        return Decimal("100")

    all_points = [p.avg_points for p in patterns]
    avg_all = sum(all_points) / len(all_points)

    season = get_season(route, month)
    for p in patterns:
        if p.season == season:
            if avg_all > 0:
                return (Decimal(str(p.avg_points)) / Decimal(str(avg_all)) * 100).quantize(Decimal("0.1"))
    return Decimal("100")


def compute_booking_window(route: str, travel_month: int) -> BookingWindow:
    """Compute optimal booking window for a route and travel month."""
    season = get_season(route, travel_month)

    if season == Season.PEAK:
        return BookingWindow(
            route=route,
            travel_month=travel_month,
            ideal_book_months_ahead=6,
            urgency=BookingUrgency.BOOK_NOW,
            reason="Peak season — award availability drops quickly. Book 6+ months ahead.",
            savings_vs_last_minute_pct=40,
        )
    if season == Season.SHOULDER:
        return BookingWindow(
            route=route,
            travel_month=travel_month,
            ideal_book_months_ahead=3,
            urgency=BookingUrgency.GOOD_TIME,
            reason="Shoulder season — good availability if booked 3+ months ahead.",
            savings_vs_last_minute_pct=25,
        )
    return BookingWindow(
        route=route,
        travel_month=travel_month,
        ideal_book_months_ahead=1,
        urgency=BookingUrgency.WAIT,
        reason="Off-peak — plenty of availability. Can book closer to travel date.",
        savings_vs_last_minute_pct=10,
    )


def seasonal_advisory(route: str, current_month: int) -> SeasonalAdvisory:
    """Generate a complete seasonal advisory for a route."""
    patterns = get_seasonal_patterns(route)
    season = get_season(route, current_month)
    price_index = compute_price_index(route, current_month)
    booking = compute_booking_window(route, current_month)

    # Find best and worst value months
    month_costs: list[tuple[int, int]] = []
    for p in patterns:
        for m in p.months:
            month_costs.append((m, p.avg_points))

    if month_costs:
        month_costs.sort(key=lambda x: x[1])
        best_months = [m for m, _ in month_costs[:3]]
        worst_months = [m for m, _ in month_costs[-3:]]
    else:
        best_months = [1, 2, 11]
        worst_months = [6, 7, 8]

    return SeasonalAdvisory(
        route=route,
        current_season=season,
        current_month=current_month,
        patterns=patterns,
        best_value_months=best_months,
        worst_value_months=worst_months,
        booking_window=booking,
        price_index=price_index,
    )
