"""Savings analysis service — portfolio-wide value gap and optimization opportunities.

Fowler: Aggregate Root pattern — SavingsAnalysis owns the computation boundary.
Beck: One method, one job. Each method answers exactly one question.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from redeemflow.valuations.aggregator import AggregationStrategy, aggregate_cpp
from redeemflow.valuations.models import ProgramValuation


@dataclass(frozen=True)
class ProgramSavingsDetail:
    """Per-program breakdown in a savings analysis."""

    program_code: str
    program_name: str
    points: int
    travel_value: Decimal
    cash_back_value: Decimal
    opportunity_cost: Decimal
    aggregated_cpp: Decimal
    confidence: str
    optimization_hint: str


@dataclass(frozen=True)
class SavingsAnalysis:
    """Portfolio-wide savings analysis result."""

    programs: list[ProgramSavingsDetail]
    total_travel_value: Decimal
    total_cash_back_value: Decimal
    total_opportunity_cost: Decimal
    total_points: int
    weighted_avg_cpp: Decimal
    best_program: str | None
    worst_program: str | None


def _optimization_hint(opp_cost: Decimal, cpp: Decimal, points: int) -> str:
    """Generate a simple optimization hint based on opportunity cost and CPP."""
    if points == 0:
        return "no_balance"
    if opp_cost <= Decimal("0"):
        return "cash_back_preferred"
    if cpp >= Decimal("1.8"):
        return "high_value_transfer"
    if cpp >= Decimal("1.2"):
        return "moderate_value_hold"
    return "low_value_consider_cashback"


def analyze_savings(
    balances: dict[str, int],
    valuations: dict[str, ProgramValuation],
    strategy: AggregationStrategy = AggregationStrategy.MEDIAN,
) -> SavingsAnalysis:
    """Analyze savings across a portfolio of loyalty programs.

    Args:
        balances: dict mapping program_code to points balance
        valuations: dict mapping program_code to ProgramValuation
        strategy: aggregation strategy to use for CPP calculation
    """
    programs: list[ProgramSavingsDetail] = []
    total_travel = Decimal("0")
    total_cash = Decimal("0")
    total_points = 0
    weighted_cpp_sum = Decimal("0")

    for code, points in balances.items():
        val = valuations.get(code)
        if val is None or points == 0:
            continue

        agg = aggregate_cpp(val, strategy)
        travel = val.dollar_value(points)
        cash = val.cash_back_value(points)
        opp = travel - cash

        hint = _optimization_hint(opp, agg.aggregated_cpp, points)

        programs.append(
            ProgramSavingsDetail(
                program_code=code,
                program_name=val.program_name,
                points=points,
                travel_value=travel,
                cash_back_value=cash,
                opportunity_cost=opp,
                aggregated_cpp=agg.aggregated_cpp,
                confidence=agg.confidence,
                optimization_hint=hint,
            )
        )

        total_travel += travel
        total_cash += cash
        total_points += points
        weighted_cpp_sum += agg.aggregated_cpp * Decimal(points)

    # Sort by opportunity cost descending — biggest savings gap first
    programs.sort(key=lambda p: p.opportunity_cost, reverse=True)

    weighted_avg_cpp = Decimal("0")
    if total_points > 0:
        weighted_avg_cpp = (weighted_cpp_sum / Decimal(total_points)).quantize(Decimal("0.01"))

    best = programs[0].program_code if programs else None
    worst = programs[-1].program_code if programs else None

    return SavingsAnalysis(
        programs=programs,
        total_travel_value=total_travel,
        total_cash_back_value=total_cash,
        total_opportunity_cost=total_travel - total_cash,
        total_points=total_points,
        weighted_avg_cpp=weighted_avg_cpp,
        best_program=best,
        worst_program=worst,
    )
