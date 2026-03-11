"""Points calculator — earn rates, redemption math, and break-even analysis.

Beck: Calculator is pure function — inputs in, numbers out.
Fowler: Specification — composable earning rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class EarnRate:
    """Points earned per dollar spent in a category."""

    program_code: str
    category: str  # dining, travel, grocery, gas, other
    points_per_dollar: Decimal


@dataclass(frozen=True)
class EarningProjection:
    """Projected points from spending."""

    program_code: str
    monthly_spend: Decimal
    earn_rate: Decimal
    monthly_points: int
    annual_points: int
    months_to_target: int  # 0 = already met


@dataclass(frozen=True)
class BreakEvenAnalysis:
    """When an annual fee card pays for itself via point value."""

    program_code: str
    annual_fee: Decimal
    monthly_spend: Decimal
    earn_rate: Decimal
    cpp: Decimal
    monthly_points_earned: int
    annual_points_earned: int
    annual_value: Decimal
    net_value: Decimal  # annual_value - annual_fee
    break_even_monthly_spend: Decimal  # Spend needed to break even
    is_worth_it: bool


# Common earn rates
EARN_RATES: dict[str, list[EarnRate]] = {
    "chase-ur": [
        EarnRate("chase-ur", "dining", Decimal("3")),
        EarnRate("chase-ur", "travel", Decimal("3")),
        EarnRate("chase-ur", "grocery", Decimal("1")),
        EarnRate("chase-ur", "gas", Decimal("1")),
        EarnRate("chase-ur", "other", Decimal("1")),
    ],
    "amex-mr": [
        EarnRate("amex-mr", "dining", Decimal("4")),
        EarnRate("amex-mr", "travel", Decimal("5")),
        EarnRate("amex-mr", "grocery", Decimal("4")),
        EarnRate("amex-mr", "gas", Decimal("1")),
        EarnRate("amex-mr", "other", Decimal("1")),
    ],
    "citi-typ": [
        EarnRate("citi-typ", "dining", Decimal("3")),
        EarnRate("citi-typ", "travel", Decimal("3")),
        EarnRate("citi-typ", "grocery", Decimal("1")),
        EarnRate("citi-typ", "gas", Decimal("1")),
        EarnRate("citi-typ", "other", Decimal("1")),
    ],
}


def get_earn_rate(program_code: str, category: str) -> Decimal:
    """Get points per dollar for a program and spending category."""
    rates = EARN_RATES.get(program_code, [])
    for r in rates:
        if r.category == category:
            return r.points_per_dollar
    return Decimal("1")  # Default 1x


def project_earnings(
    program_code: str,
    monthly_spend: Decimal,
    category: str = "other",
    target_points: int = 0,
    existing_points: int = 0,
) -> EarningProjection:
    """Project how many points will be earned from spending."""
    rate = get_earn_rate(program_code, category)
    monthly_points = int(monthly_spend * rate)
    annual_points = monthly_points * 12

    if target_points > 0 and monthly_points > 0:
        remaining = max(0, target_points - existing_points)
        months = (remaining + monthly_points - 1) // monthly_points
    else:
        months = 0

    return EarningProjection(
        program_code=program_code,
        monthly_spend=monthly_spend,
        earn_rate=rate,
        monthly_points=monthly_points,
        annual_points=annual_points,
        months_to_target=months,
    )


def break_even(
    program_code: str,
    annual_fee: Decimal,
    monthly_spend: Decimal,
    category: str = "other",
    cpp: Decimal = Decimal("1.5"),
) -> BreakEvenAnalysis:
    """Analyze whether a card's annual fee is justified by earning value."""
    rate = get_earn_rate(program_code, category)
    monthly_points = int(monthly_spend * rate)
    annual_points = monthly_points * 12
    annual_value = (Decimal(str(annual_points)) * cpp / 100).quantize(Decimal("0.01"))
    net = annual_value - annual_fee

    # Break-even monthly spend: annual_fee = monthly_spend * rate * 12 * cpp / 100
    if rate > 0 and cpp > 0:
        be_spend = (annual_fee * 100 / (rate * 12 * cpp)).quantize(Decimal("0.01"))
    else:
        be_spend = Decimal("999999.99")

    return BreakEvenAnalysis(
        program_code=program_code,
        annual_fee=annual_fee,
        monthly_spend=monthly_spend,
        earn_rate=rate,
        cpp=cpp,
        monthly_points_earned=monthly_points,
        annual_points_earned=annual_points,
        annual_value=annual_value,
        net_value=net,
        break_even_monthly_spend=be_spend,
        is_worth_it=net > 0,
    )


def points_needed_for_value(target_value: Decimal, cpp: Decimal) -> int:
    """Calculate points needed to achieve a target dollar value."""
    if cpp <= 0:
        return 0
    return int((target_value * 100 / cpp).quantize(Decimal("1")))


def value_of_points(points: int, cpp: Decimal) -> Decimal:
    """Calculate the dollar value of a given number of points."""
    return (Decimal(str(points)) * cpp / 100).quantize(Decimal("0.01"))
