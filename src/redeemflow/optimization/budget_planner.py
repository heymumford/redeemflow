"""Annual points budget — earning projections and allocation planning.

Beck: Budget is a projection — inputs are earn rates, outputs are forecasts.
Fowler: Specification — budget constraints as composable predicates.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EarningSource:
    """A source of point earnings."""

    name: str
    program_code: str
    monthly_points: int
    category: str  # "card_spend", "bonus", "referral", "travel"


@dataclass(frozen=True)
class AllocationTarget:
    """A planned redemption to budget toward."""

    name: str
    program_code: str
    points_needed: int
    target_date: str = ""
    priority: int = 1  # 1=highest


@dataclass(frozen=True)
class BudgetForecast:
    """Monthly point earnings forecast."""

    month: int  # 1-12
    program_code: str
    projected_earnings: int
    cumulative: int


@dataclass(frozen=True)
class BudgetSummary:
    """Annual budget summary."""

    total_annual_earnings: int
    total_allocation_needed: int
    surplus_or_deficit: int
    months_to_goal: int  # Months until largest allocation is covered
    forecasts_by_program: dict[str, list[BudgetForecast]]
    allocation_feasibility: list[dict]  # Per-target feasibility


def compute_budget(
    sources: list[EarningSource],
    targets: list[AllocationTarget],
    current_balances: dict[str, int] | None = None,
) -> BudgetSummary:
    """Compute annual points budget with feasibility analysis."""
    balances = current_balances or {}

    # Aggregate monthly earnings by program
    monthly_by_program: dict[str, int] = {}
    for s in sources:
        monthly_by_program[s.program_code] = monthly_by_program.get(s.program_code, 0) + s.monthly_points

    # Build 12-month forecasts
    forecasts: dict[str, list[BudgetForecast]] = {}
    for code, monthly in monthly_by_program.items():
        current = balances.get(code, 0)
        program_forecasts = []
        for month in range(1, 13):
            current += monthly
            program_forecasts.append(
                BudgetForecast(
                    month=month,
                    program_code=code,
                    projected_earnings=monthly,
                    cumulative=current,
                )
            )
        forecasts[code] = program_forecasts

    # Annual total
    total_annual = sum(m * 12 for m in monthly_by_program.values())
    total_needed = sum(t.points_needed for t in targets)

    # Per-target feasibility
    feasibility = []
    max_months = 0
    sorted_targets = sorted(targets, key=lambda t: t.priority)

    for target in sorted_targets:
        monthly = monthly_by_program.get(target.program_code, 0)
        current = balances.get(target.program_code, 0)
        remaining = max(0, target.points_needed - current)

        if monthly > 0:
            months = (remaining + monthly - 1) // monthly  # Ceiling division
        else:
            months = 999

        feasible = months <= 12
        max_months = max(max_months, min(months, 12))

        feasibility.append(
            {
                "name": target.name,
                "program_code": target.program_code,
                "points_needed": target.points_needed,
                "current_balance": current,
                "remaining": remaining,
                "months_to_reach": min(months, 999),
                "feasible_this_year": feasible,
                "priority": target.priority,
            }
        )

    return BudgetSummary(
        total_annual_earnings=total_annual,
        total_allocation_needed=total_needed,
        surplus_or_deficit=total_annual - total_needed,
        months_to_goal=max_months,
        forecasts_by_program=forecasts,
        allocation_feasibility=feasibility,
    )
