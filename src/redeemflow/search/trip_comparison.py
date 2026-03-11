"""Trip comparison — side-by-side redemption options for the same route.

Beck: Comparison is a projection — inputs are options, output is a ranking.
Fowler: Value Object pattern — each option is an immutable snapshot.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class RedemptionOption:
    """A single redemption option for comparison."""

    program_code: str
    program_name: str
    points_required: int
    cash_price: Decimal
    cpp: Decimal
    cabin_class: str = "economy"
    route: str = ""
    stops: int = 0
    transfer_required: bool = False
    transfer_from: str = ""
    availability: str = "available"  # available, waitlist, unavailable


@dataclass(frozen=True)
class ComparisonResult:
    """Side-by-side comparison of redemption options."""

    route: str
    options: list[RedemptionOption]
    best_value: RedemptionOption
    best_availability: RedemptionOption
    cheapest_points: RedemptionOption
    value_spread: Decimal  # Difference between best and worst cpp


def compare_options(route: str, options: list[RedemptionOption]) -> ComparisonResult:
    """Compare redemption options and rank by value, availability, and cost.

    Returns a ComparisonResult with the options sorted by cpp descending (best first).
    """
    if not options:
        raise ValueError("At least one option is required for comparison")

    # Sort by cpp descending — higher cpp = better value per point
    sorted_by_value = sorted(options, key=lambda o: o.cpp, reverse=True)

    # Best value = highest cpp
    best_value = sorted_by_value[0]

    # Best availability = prefer available, then waitlist, then unavailable; tiebreak by cpp
    availability_rank = {"available": 0, "waitlist": 1, "unavailable": 2}
    best_availability = sorted(
        options,
        key=lambda o: (availability_rank.get(o.availability, 3), -o.cpp),
    )[0]

    # Cheapest in points (among available/waitlist options, fallback to all)
    bookable = [o for o in options if o.availability != "unavailable"]
    pool = bookable if bookable else options
    cheapest_points = sorted(pool, key=lambda o: o.points_required)[0]

    # Value spread
    cpps = [o.cpp for o in options]
    spread = max(cpps) - min(cpps)

    return ComparisonResult(
        route=route,
        options=sorted_by_value,
        best_value=best_value,
        best_availability=best_availability,
        cheapest_points=cheapest_points,
        value_spread=spread,
    )


def rank_options(options: list[RedemptionOption], weights: dict[str, Decimal] | None = None) -> list[dict]:
    """Score and rank options with configurable weights.

    Default weights: value (cpp) 50%, cost (points) 30%, availability 20%.
    """
    w = weights or {
        "value": Decimal("0.50"),
        "cost": Decimal("0.30"),
        "availability": Decimal("0.20"),
    }

    if not options:
        return []

    # Normalize scores to 0-100
    max_cpp = max(o.cpp for o in options)
    min_points = min(o.points_required for o in options)
    max_points = max(o.points_required for o in options)
    avail_scores = {"available": Decimal("100"), "waitlist": Decimal("50"), "unavailable": Decimal("0")}

    ranked = []
    for opt in options:
        value_score = (opt.cpp / max_cpp * 100).quantize(Decimal("0.1")) if max_cpp > 0 else Decimal("0")

        if max_points > min_points:
            cost_score = (max_points - opt.points_required) / (max_points - min_points) * 100
            cost_score = Decimal(str(cost_score)).quantize(Decimal("0.1"))
        else:
            cost_score = Decimal("100")

        avail_score = avail_scores.get(opt.availability, Decimal("0"))

        composite = (w["value"] * value_score + w["cost"] * cost_score + w["availability"] * avail_score).quantize(
            Decimal("0.1")
        )

        ranked.append(
            {
                "program_code": opt.program_code,
                "program_name": opt.program_name,
                "points_required": opt.points_required,
                "cpp": opt.cpp,
                "value_score": value_score,
                "cost_score": cost_score,
                "availability_score": avail_score,
                "composite_score": composite,
                "cabin_class": opt.cabin_class,
                "availability": opt.availability,
            }
        )

    return sorted(ranked, key=lambda r: r["composite_score"], reverse=True)
