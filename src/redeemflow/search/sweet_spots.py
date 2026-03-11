"""Sweet spots engine — find high-value redemptions where points beat cash.

Fowler: Strategy pattern for value calculation. Value objects for results.
Beck: Simple data in, simple data out. No side effects.

A "sweet spot" is a redemption where the CPP exceeds a threshold (typically 1.5x)
relative to the program's baseline CPP, indicating outsized value.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class SweetSpotCategory(str, Enum):
    FLIGHTS = "flights"
    HOTELS = "hotels"
    EXPERIENCES = "experiences"
    TRANSFERS = "transfers"


class ValueRating(str, Enum):
    EXCEPTIONAL = "exceptional"  # >= 3x baseline
    EXCELLENT = "excellent"  # >= 2x baseline
    GOOD = "good"  # >= 1.5x baseline
    FAIR = "fair"  # >= 1x baseline


@dataclass(frozen=True)
class SweetSpot:
    """A high-value redemption opportunity."""

    program: str
    program_name: str
    category: SweetSpotCategory
    description: str
    points_required: int
    cash_equivalent: Decimal
    effective_cpp: Decimal
    baseline_cpp: Decimal
    value_multiplier: Decimal
    rating: ValueRating
    route: str | None = None
    cabin: str | None = None
    hotel_category: str | None = None
    notes: str | None = None


def _rate(multiplier: Decimal) -> ValueRating:
    if multiplier >= Decimal("3.0"):
        return ValueRating.EXCEPTIONAL
    if multiplier >= Decimal("2.0"):
        return ValueRating.EXCELLENT
    if multiplier >= Decimal("1.5"):
        return ValueRating.GOOD
    return ValueRating.FAIR


# Curated sweet spots from community-sourced data
SWEET_SPOTS_DATA: list[dict] = [
    {
        "program": "united",
        "program_name": "United MileagePlus",
        "category": SweetSpotCategory.FLIGHTS,
        "description": "Polaris business class to Europe",
        "points_required": 60000,
        "cash_equivalent": Decimal("3000"),
        "baseline_cpp": Decimal("1.2"),
        "route": "US-Europe",
        "cabin": "business",
    },
    {
        "program": "hyatt",
        "program_name": "World of Hyatt",
        "category": SweetSpotCategory.HOTELS,
        "description": "Category 1-4 Hyatt stays",
        "points_required": 8000,
        "cash_equivalent": Decimal("250"),
        "baseline_cpp": Decimal("1.7"),
        "hotel_category": "1-4",
    },
    {
        "program": "chase-ur",
        "program_name": "Chase Ultimate Rewards",
        "category": SweetSpotCategory.TRANSFERS,
        "description": "Transfer to Hyatt for Category 1-4",
        "points_required": 8000,
        "cash_equivalent": Decimal("250"),
        "baseline_cpp": Decimal("1.8"),
        "notes": "1:1 transfer to World of Hyatt",
    },
    {
        "program": "amex-mr",
        "program_name": "Amex Membership Rewards",
        "category": SweetSpotCategory.TRANSFERS,
        "description": "Transfer to ANA for round-trip J to Japan",
        "points_required": 88000,
        "cash_equivalent": Decimal("5000"),
        "baseline_cpp": Decimal("1.8"),
        "route": "US-Japan",
        "cabin": "business",
        "notes": "Via Virgin Atlantic or direct to ANA",
    },
    {
        "program": "american",
        "program_name": "American AAdvantage",
        "category": SweetSpotCategory.FLIGHTS,
        "description": "JAL first class US-Japan",
        "points_required": 80000,
        "cash_equivalent": Decimal("12000"),
        "baseline_cpp": Decimal("1.5"),
        "route": "US-Japan",
        "cabin": "first",
    },
    {
        "program": "british-airways",
        "program_name": "British Airways Avios",
        "category": SweetSpotCategory.FLIGHTS,
        "description": "Short-haul off-peak domestic",
        "points_required": 7500,
        "cash_equivalent": Decimal("200"),
        "baseline_cpp": Decimal("1.3"),
        "route": "US domestic short-haul",
        "cabin": "economy",
    },
    {
        "program": "hilton",
        "program_name": "Hilton Honors",
        "category": SweetSpotCategory.HOTELS,
        "description": "5th night free on aspirational properties",
        "points_required": 380000,
        "cash_equivalent": Decimal("2500"),
        "baseline_cpp": Decimal("0.5"),
        "hotel_category": "aspirational",
        "notes": "5th night free effectively gives 20% discount",
    },
    {
        "program": "marriott",
        "program_name": "Marriott Bonvoy",
        "category": SweetSpotCategory.HOTELS,
        "description": "Category 1-3 off-peak stays",
        "points_required": 10000,
        "cash_equivalent": Decimal("150"),
        "baseline_cpp": Decimal("0.7"),
        "hotel_category": "1-3",
    },
    {
        "program": "southwest",
        "program_name": "Southwest Rapid Rewards",
        "category": SweetSpotCategory.FLIGHTS,
        "description": "Wanna Get Away fares (no blackouts)",
        "points_required": 5000,
        "cash_equivalent": Decimal("100"),
        "baseline_cpp": Decimal("1.2"),
        "route": "US domestic",
        "cabin": "economy",
        "notes": "No change or cancellation fees",
    },
    {
        "program": "air-canada",
        "program_name": "Air Canada Aeroplan",
        "category": SweetSpotCategory.FLIGHTS,
        "description": "Star Alliance business class to Europe",
        "points_required": 70000,
        "cash_equivalent": Decimal("4000"),
        "baseline_cpp": Decimal("1.5"),
        "route": "US-Europe",
        "cabin": "business",
    },
]


def _build_sweet_spots() -> list[SweetSpot]:
    """Convert raw data into SweetSpot value objects with computed fields."""
    spots = []
    for data in SWEET_SPOTS_DATA:
        points = data["points_required"]
        cash = data["cash_equivalent"]
        baseline = data["baseline_cpp"]

        effective = (cash / Decimal(points) * Decimal(100)).quantize(Decimal("0.01"))
        multiplier = (effective / baseline).quantize(Decimal("0.01"))

        spots.append(
            SweetSpot(
                program=data["program"],
                program_name=data["program_name"],
                category=data["category"],
                description=data["description"],
                points_required=points,
                cash_equivalent=cash,
                effective_cpp=effective,
                baseline_cpp=baseline,
                value_multiplier=multiplier,
                rating=_rate(multiplier),
                route=data.get("route"),
                cabin=data.get("cabin"),
                hotel_category=data.get("hotel_category"),
                notes=data.get("notes"),
            )
        )
    return spots


ALL_SWEET_SPOTS = _build_sweet_spots()


def find_sweet_spots(
    category: SweetSpotCategory | None = None,
    program: str | None = None,
    min_rating: ValueRating = ValueRating.FAIR,
) -> list[SweetSpot]:
    """Find sweet spots filtered by category, program, and minimum rating."""
    rating_order = [ValueRating.FAIR, ValueRating.GOOD, ValueRating.EXCELLENT, ValueRating.EXCEPTIONAL]
    min_idx = rating_order.index(min_rating)

    results = []
    for spot in ALL_SWEET_SPOTS:
        if category and spot.category != category:
            continue
        if program and spot.program != program:
            continue
        spot_idx = rating_order.index(spot.rating)
        if spot_idx < min_idx:
            continue
        results.append(spot)

    results.sort(key=lambda s: s.value_multiplier, reverse=True)
    return results
