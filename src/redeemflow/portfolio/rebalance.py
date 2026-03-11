"""Portfolio rebalancing — concentration risk and optimization suggestions.

Beck: Rebalance is a projection — current state in, actions out.
Fowler: Specification — balance constraints as composable predicates.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class PortfolioBalance:
    """A program balance with valuation."""

    program_code: str
    program_name: str
    points: int
    cpp: Decimal
    value: Decimal  # points * cpp / 100
    pct_of_total: Decimal


@dataclass(frozen=True)
class ConcentrationRisk:
    """Analysis of portfolio concentration."""

    total_programs: int
    total_value: Decimal
    largest_position: PortfolioBalance | None
    largest_pct: Decimal
    risk_level: RiskLevel
    herfindahl_index: Decimal  # Sum of squared market shares, 0-10000
    recommendation: str


@dataclass(frozen=True)
class RebalanceAction:
    """A suggested rebalancing action."""

    action_type: str  # "transfer", "redeem", "accumulate"
    from_program: str
    to_program: str
    points: int
    rationale: str
    impact: str


@dataclass(frozen=True)
class RebalanceReport:
    """Complete portfolio rebalancing analysis."""

    balances: list[PortfolioBalance]
    concentration: ConcentrationRisk
    actions: list[RebalanceAction]
    projected_improvement: str


def analyze_portfolio(
    balances: list[dict],
    valuations: dict[str, Decimal] | None = None,
) -> RebalanceReport:
    """Analyze portfolio and suggest rebalancing actions.

    Args:
        balances: List of {"program_code": str, "program_name": str, "points": int}
        valuations: Map of program_code to cpp (defaults provided)
    """
    default_cpps = {
        "chase-ur": Decimal("1.50"),
        "amex-mr": Decimal("1.30"),
        "citi-typ": Decimal("1.20"),
        "united": Decimal("1.30"),
        "delta": Decimal("1.20"),
        "aa": Decimal("1.40"),
        "hyatt": Decimal("1.70"),
        "marriott": Decimal("0.80"),
        "hilton": Decimal("0.50"),
        "southwest": Decimal("1.40"),
    }
    cpps = valuations or default_cpps

    # Build portfolio balances
    portfolio: list[PortfolioBalance] = []
    total_value = Decimal("0")

    for b in balances:
        code = b["program_code"]
        cpp = cpps.get(code, Decimal("1.00"))
        value = (Decimal(str(b["points"])) * cpp / 100).quantize(Decimal("0.01"))
        total_value += value
        portfolio.append(
            PortfolioBalance(
                program_code=code,
                program_name=b.get("program_name", code),
                points=b["points"],
                cpp=cpp,
                value=value,
                pct_of_total=Decimal("0"),  # Computed below
            )
        )

    # Compute percentages
    if total_value > 0:
        portfolio = [
            PortfolioBalance(
                program_code=pb.program_code,
                program_name=pb.program_name,
                points=pb.points,
                cpp=pb.cpp,
                value=pb.value,
                pct_of_total=(pb.value / total_value * 100).quantize(Decimal("0.1")),
            )
            for pb in portfolio
        ]

    portfolio.sort(key=lambda p: p.value, reverse=True)

    # Concentration analysis
    largest = portfolio[0] if portfolio else None
    largest_pct = largest.pct_of_total if largest else Decimal("0")

    # Herfindahl index: sum of squared percentages
    hhi = sum(pb.pct_of_total**2 for pb in portfolio).quantize(Decimal("0.1")) if portfolio else Decimal("0")

    if largest_pct > 70:
        risk = RiskLevel.CRITICAL
        recommendation = "Portfolio is dangerously concentrated. Diversify urgently."
    elif largest_pct > 50:
        risk = RiskLevel.HIGH
        recommendation = "Portfolio is over-concentrated. Consider transferring to other programs."
    elif largest_pct > 35:
        risk = RiskLevel.MODERATE
        recommendation = "Portfolio has moderate concentration. Monitor and diversify gradually."
    else:
        risk = RiskLevel.LOW
        recommendation = "Portfolio is well-diversified."

    concentration = ConcentrationRisk(
        total_programs=len(portfolio),
        total_value=total_value,
        largest_position=largest,
        largest_pct=largest_pct,
        risk_level=risk,
        herfindahl_index=hhi,
        recommendation=recommendation,
    )

    # Generate actions
    actions: list[RebalanceAction] = []
    if risk in (RiskLevel.HIGH, RiskLevel.CRITICAL) and largest:
        # Suggest transfer from largest to highest-cpp small position
        smaller = [p for p in portfolio if p.program_code != largest.program_code and p.pct_of_total < 20]
        if smaller:
            target = max(smaller, key=lambda p: p.cpp)
            transfer_points = largest.points // 4
            actions.append(
                RebalanceAction(
                    action_type="transfer",
                    from_program=largest.program_code,
                    to_program=target.program_code,
                    points=transfer_points,
                    rationale=f"Reduce {largest.program_code} concentration from {largest_pct}%",
                    impact=f"Moves ~{transfer_points:,} points to higher-value {target.program_code}",
                )
            )

    # Suggest redeeming low-value positions
    for pb in portfolio:
        if pb.cpp < Decimal("0.60") and pb.points > 10000:
            actions.append(
                RebalanceAction(
                    action_type="redeem",
                    from_program=pb.program_code,
                    to_program="",
                    points=pb.points,
                    rationale=f"{pb.program_code} has low cpp ({pb.cpp}). Redeem before devaluation.",
                    impact=f"Extract ${pb.value} value before further decline",
                )
            )

    improvement = "Balanced" if risk == RiskLevel.LOW else f"Reduce concentration from {largest_pct}% to <35%"

    return RebalanceReport(
        balances=portfolio,
        concentration=concentration,
        actions=actions,
        projected_improvement=improvement,
    )
