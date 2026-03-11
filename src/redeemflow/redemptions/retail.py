"""Retail redemption analysis — Shop with Points, gift cards, statement credits.

Beck: Name things for what they do — these are value-destruction detectors.

Most retail/shop-with-points redemptions deliver 0.5-0.7 CPP, destroying value
compared to travel redemptions at 1.5-15+ CPP. This module quantifies the loss
so users understand the true cost of retail redemptions.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class RetailType(str, Enum):
    SHOP_WITH_POINTS = "shop_with_points"  # Amazon, airline shopping portals
    GIFT_CARD = "gift_card"
    STATEMENT_CREDIT = "statement_credit"
    MERCHANDISE = "merchandise"


@dataclass(frozen=True)
class RetailRedemption:
    """A retail/non-travel redemption option."""

    program_code: str
    retail_type: RetailType
    description: str
    cpp: Decimal  # Cents per point
    min_points: int = 1

    @property
    def value_rating(self) -> str:
        """Rate the retail redemption value."""
        if self.cpp >= Decimal("1.0"):
            return "fair"
        if self.cpp >= Decimal("0.7"):
            return "below_average"
        return "poor"


@dataclass(frozen=True)
class RetailAnalysis:
    """Analysis comparing retail redemption to travel alternatives."""

    redemption: RetailRedemption
    points: int
    retail_value: Decimal
    travel_value: Decimal  # Same points at best travel CPP
    value_destroyed: Decimal  # travel_value - retail_value
    destruction_pct: Decimal  # % of value lost
    recommendation: str
    rationale: str


# Seed data: real-world retail redemption rates
RETAIL_REDEMPTIONS: list[RetailRedemption] = [
    # Chase UR
    RetailRedemption(
        program_code="chase-ur",
        retail_type=RetailType.SHOP_WITH_POINTS,
        description="Amazon Shop with Points (Chase)",
        cpp=Decimal("0.80"),
        min_points=1,
    ),
    RetailRedemption(
        program_code="chase-ur",
        retail_type=RetailType.STATEMENT_CREDIT,
        description="Chase statement credit",
        cpp=Decimal("1.00"),
        min_points=2000,
    ),
    RetailRedemption(
        program_code="chase-ur",
        retail_type=RetailType.GIFT_CARD,
        description="Chase gift card redemption",
        cpp=Decimal("1.00"),
        min_points=5000,
    ),
    # Amex MR
    RetailRedemption(
        program_code="amex-mr",
        retail_type=RetailType.SHOP_WITH_POINTS,
        description="Amazon Shop with Points (Amex)",
        cpp=Decimal("0.70"),
        min_points=1,
    ),
    RetailRedemption(
        program_code="amex-mr",
        retail_type=RetailType.STATEMENT_CREDIT,
        description="Amex statement credit",
        cpp=Decimal("0.60"),
        min_points=5000,
    ),
    RetailRedemption(
        program_code="amex-mr",
        retail_type=RetailType.GIFT_CARD,
        description="Amex gift card",
        cpp=Decimal("1.00"),
        min_points=5000,
    ),
    # Capital One
    RetailRedemption(
        program_code="capital-one",
        retail_type=RetailType.SHOP_WITH_POINTS,
        description="Amazon Shop with Points (Capital One)",
        cpp=Decimal("0.80"),
        min_points=1,
    ),
    RetailRedemption(
        program_code="capital-one",
        retail_type=RetailType.STATEMENT_CREDIT,
        description="Capital One statement credit",
        cpp=Decimal("1.00"),
        min_points=2500,
    ),
    # Citi TY
    RetailRedemption(
        program_code="citi-ty",
        retail_type=RetailType.SHOP_WITH_POINTS,
        description="Amazon Shop with Points (Citi)",
        cpp=Decimal("0.80"),
        min_points=1,
    ),
    RetailRedemption(
        program_code="citi-ty",
        retail_type=RetailType.GIFT_CARD,
        description="Citi ThankYou gift card",
        cpp=Decimal("1.00"),
        min_points=5000,
    ),
]


def analyze_retail_redemption(
    redemption: RetailRedemption,
    points: int,
    best_travel_cpp: Decimal = Decimal("1.5"),
) -> RetailAnalysis:
    """Analyze a retail redemption vs travel alternatives.

    Quantifies the value destroyed by using points for retail instead of travel.
    """
    retail_value = (redemption.cpp * points / 100).quantize(Decimal("0.01"))
    travel_value = (best_travel_cpp * points / 100).quantize(Decimal("0.01"))
    value_destroyed = travel_value - retail_value
    destruction_pct = (
        ((value_destroyed / travel_value) * 100).quantize(Decimal("0.1")) if travel_value > 0 else Decimal("0")
    )

    if destruction_pct <= Decimal("10"):
        recommendation = "acceptable"
        rationale = f"Retail at {redemption.cpp} CPP is close to travel value — acceptable for convenience"
    elif destruction_pct <= Decimal("30"):
        recommendation = "consider_travel"
        rationale = f"You lose {destruction_pct}% of value — ${value_destroyed} on {points:,} points"
    else:
        recommendation = "avoid"
        rationale = f"You destroy {destruction_pct}% of value — ${value_destroyed} wasted on {points:,} points"

    return RetailAnalysis(
        redemption=redemption,
        points=points,
        retail_value=retail_value,
        travel_value=travel_value,
        value_destroyed=value_destroyed,
        destruction_pct=destruction_pct,
        recommendation=recommendation,
        rationale=rationale,
    )


def find_retail_redemptions(program_code: str) -> list[RetailRedemption]:
    """Find all retail redemptions for a given loyalty program."""
    return [r for r in RETAIL_REDEMPTIONS if r.program_code == program_code]


def worst_retail_redemption(program_code: str) -> RetailRedemption | None:
    """Find the worst CPP retail redemption — the biggest value trap."""
    redemptions = find_retail_redemptions(program_code)
    if not redemptions:
        return None
    return min(redemptions, key=lambda r: r.cpp)
