"""Booking method optimizer — points vs cash vs mix decision engine.

Beck: Given a price and your points, what's the smartest way to pay?
Fowler: Strategy pattern — each booking method is evaluated independently.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class PaymentMethod(str, Enum):
    POINTS_ONLY = "points_only"
    CASH_ONLY = "cash_only"
    POINTS_PLUS_CASH = "points_plus_cash"
    TRANSFER_THEN_POINTS = "transfer_then_points"


@dataclass(frozen=True)
class BookingOption:
    """A single booking payment option with value analysis."""

    method: PaymentMethod
    points_cost: int
    cash_cost: Decimal
    effective_cpp: Decimal  # What each point is "worth" in this booking
    value_score: Decimal  # Higher = better value for the traveler
    program_code: str
    description: str
    is_recommended: bool = False
    savings_vs_cash: Decimal = Decimal("0")


@dataclass(frozen=True)
class BookingAnalysis:
    """Complete analysis of all payment options for a booking."""

    cash_price: Decimal
    options: list[BookingOption]
    recommended: BookingOption
    recommendation_reason: str


def analyze_booking(
    cash_price: Decimal,
    points_price: int,
    program_code: str,
    program_cpp: Decimal,
    available_points: int = 0,
    transfer_options: list[dict] | None = None,
) -> BookingAnalysis:
    """Analyze all payment methods and recommend the best one.

    Args:
        cash_price: The cash price of the booking
        points_price: Points required for an award booking
        program_code: The loyalty program code
        program_cpp: The baseline CPP for this program
        available_points: User's current point balance
        transfer_options: Available transfer paths [{source, ratio, source_cpp}]
    """
    options: list[BookingOption] = []

    # Option 1: Cash only
    cash_option = BookingOption(
        method=PaymentMethod.CASH_ONLY,
        points_cost=0,
        cash_cost=cash_price,
        effective_cpp=Decimal("0"),
        value_score=Decimal("0"),
        program_code=program_code,
        description="Pay full cash price",
    )
    options.append(cash_option)

    # Option 2: Points only
    if points_price > 0:
        effective_cpp = (cash_price / Decimal(points_price) * 100).quantize(Decimal("0.01"))
        # Value score: how much better than baseline (>1 = good deal)
        value_score = (effective_cpp / program_cpp).quantize(Decimal("0.01")) if program_cpp > 0 else Decimal("0")
        savings = cash_price if available_points >= points_price else Decimal("0")

        points_option = BookingOption(
            method=PaymentMethod.POINTS_ONLY,
            points_cost=points_price,
            cash_cost=Decimal("0"),
            effective_cpp=effective_cpp,
            value_score=value_score,
            program_code=program_code,
            description=f"Redeem {points_price:,} {program_code} points",
            savings_vs_cash=savings,
        )
        options.append(points_option)

    # Option 3: Points + cash (split at 50%)
    if points_price > 0 and cash_price > 0:
        half_points = points_price // 2
        half_cash = (cash_price / 2).quantize(Decimal("0.01"))
        mix_cpp = Decimal("0")
        if half_points > 0:
            mix_cpp = (half_cash / Decimal(half_points) * 100).quantize(Decimal("0.01"))
        mix_value = (mix_cpp / program_cpp).quantize(Decimal("0.01")) if program_cpp > 0 else Decimal("0")
        mix_savings = cash_price - half_cash if available_points >= half_points else Decimal("0")

        mix_option = BookingOption(
            method=PaymentMethod.POINTS_PLUS_CASH,
            points_cost=half_points,
            cash_cost=half_cash,
            effective_cpp=mix_cpp,
            value_score=mix_value,
            program_code=program_code,
            description=f"{half_points:,} points + ${half_cash} cash",
            savings_vs_cash=mix_savings,
        )
        options.append(mix_option)

    # Option 4: Transfer from another program, then redeem
    for xfer in transfer_options or []:
        source = xfer.get("source", "")
        ratio = Decimal(str(xfer.get("ratio", 1)))
        source_cpp = Decimal(str(xfer.get("source_cpp", "1.0")))

        if ratio > 0 and points_price > 0:
            source_points_needed = int(Decimal(points_price) / ratio)
            # Effective CPP from the source program's perspective
            xfer_cpp = Decimal("0")
            if source_points_needed > 0:
                xfer_cpp = (cash_price / Decimal(source_points_needed) * 100).quantize(Decimal("0.01"))
            xfer_value = (xfer_cpp / source_cpp).quantize(Decimal("0.01")) if source_cpp > 0 else Decimal("0")

            xfer_option = BookingOption(
                method=PaymentMethod.TRANSFER_THEN_POINTS,
                points_cost=source_points_needed,
                cash_cost=Decimal("0"),
                effective_cpp=xfer_cpp,
                value_score=xfer_value,
                program_code=source,
                description=f"Transfer {source_points_needed:,} {source} → {program_code} at {ratio}:1",
                savings_vs_cash=cash_price,
            )
            options.append(xfer_option)

    # Find recommendation: highest value_score among affordable options
    affordable = [o for o in options if o.method == PaymentMethod.CASH_ONLY or o.points_cost <= available_points]
    if not affordable:
        affordable = options

    # Among point-based options, pick highest value score
    point_options = [o for o in affordable if o.method != PaymentMethod.CASH_ONLY]
    if point_options:
        best = max(point_options, key=lambda o: o.value_score)
        if best.value_score >= Decimal("1.0"):
            reason = f"Getting {best.effective_cpp}cpp — {best.value_score}x baseline value"
        else:
            best = cash_option
            reason = "Points redemption below baseline value — cash is better"
    else:
        best = cash_option
        reason = "No point options available or affordable"

    # Mark recommended
    final_options = []
    for o in options:
        if o is best:
            final_options.append(
                BookingOption(
                    method=o.method,
                    points_cost=o.points_cost,
                    cash_cost=o.cash_cost,
                    effective_cpp=o.effective_cpp,
                    value_score=o.value_score,
                    program_code=o.program_code,
                    description=o.description,
                    is_recommended=True,
                    savings_vs_cash=o.savings_vs_cash,
                )
            )
        else:
            final_options.append(o)

    return BookingAnalysis(
        cash_price=cash_price,
        options=final_options,
        recommended=best,
        recommendation_reason=reason,
    )
