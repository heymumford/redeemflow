"""Optimization domain — bank vs burn timing advisor.

Recommends whether to transfer, burn, or bank points
based on active bonuses, CPP trends, and redemption options.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from redeemflow.optimization.graph import TransferGraph
from redeemflow.portfolio.models import PointBalance
from redeemflow.valuations.models import ProgramValuation


@dataclass(frozen=True)
class TimingAdvice:
    """Advice on whether to burn, bank, or transfer points."""

    program_code: str
    recommendation: str  # "burn", "bank", "transfer"
    rationale: str
    confidence: str  # "high", "medium", "low"
    cpp_trend: str  # "rising", "stable", "declining"
    active_bonuses: list[str] = field(default_factory=list)


class TimingAdvisor:
    """Advises on bank vs burn timing for loyalty program points."""

    def __init__(self, graph: TransferGraph, valuations: dict[str, ProgramValuation]) -> None:
        self._graph = graph
        self._valuations = valuations

    def advise(self, program_code: str, points: int) -> TimingAdvice:
        """Produce timing advice for a single program balance."""
        # Check for active transfer bonuses
        bonuses = self._find_active_bonuses(program_code)
        if bonuses:
            best_bonus = bonuses[0]
            return TimingAdvice(
                program_code=program_code,
                recommendation="transfer",
                rationale=f"Active transfer bonus: {best_bonus}. Transfer now for maximum value.",
                confidence="high",
                cpp_trend="stable",
                active_bonuses=bonuses,
            )

        # Check valuation trend (static for now -- future: historical CPP tracking)
        val = self._valuations.get(program_code)
        if val is None:
            return TimingAdvice(
                program_code=program_code,
                recommendation="bank",
                rationale=f"No valuation data for {program_code}. Hold until more data available.",
                confidence="low",
                cpp_trend="stable",
                active_bonuses=[],
            )

        # Assess CPP trend based on source spread
        cpp_trend = self._assess_trend(val)

        if cpp_trend == "declining":
            # Find best redemption to recommend burning
            best_path = self._graph.find_best_path(program_code, points)
            if best_path is not None:
                return TimingAdvice(
                    program_code=program_code,
                    recommendation="burn",
                    rationale=(
                        f"CPP trend declining for {val.program_name}. "
                        f"Best redemption: {best_path.redemption.description} "
                        f"at {best_path.effective_cpp:.1f} CPP."
                    ),
                    confidence="medium",
                    cpp_trend="declining",
                    active_bonuses=[],
                )
            return TimingAdvice(
                program_code=program_code,
                recommendation="burn",
                rationale=f"CPP trend declining for {val.program_name}. Consider redeeming soon.",
                confidence="medium",
                cpp_trend="declining",
                active_bonuses=[],
            )

        # Default: bank (stable or rising)
        return TimingAdvice(
            program_code=program_code,
            recommendation="bank",
            rationale=(
                f"No active bonuses for {val.program_name}. "
                f"CPP {cpp_trend} at median {val.median_cpp}. Hold for better opportunity."
            ),
            confidence="high" if cpp_trend == "rising" else "medium",
            cpp_trend=cpp_trend,
            active_bonuses=[],
        )

    def advise_portfolio(self, balances: list[PointBalance]) -> list[TimingAdvice]:
        """Produce timing advice for every balance in a portfolio."""
        return [self.advise(b.program_code, b.points) for b in balances]

    def _find_active_bonuses(self, program_code: str) -> list[str]:
        """Find all active transfer bonuses from a program."""
        bonuses: list[str] = []
        partners = self._graph.get_partners_from(program_code)
        for partner in partners:
            if partner.transfer_bonus > 0:
                pct = int(partner.transfer_bonus * 100)
                bonuses.append(f"{partner.target_program} {pct}% bonus")
        return bonuses

    def _assess_trend(self, val: ProgramValuation) -> str:
        """Assess CPP trend based on source spread.

        With multiple sources: wide spread suggests instability.
        Single source: assume stable.
        Future: compare to historical CPP values.
        """
        if len(val.valuations) <= 1:
            return "stable"

        spread = val.max_cpp - val.min_cpp
        median = val.median_cpp
        if median == 0:
            return "stable"

        # If spread is >30% of median, consider it volatile (declining signal)
        ratio = spread / median
        if ratio > 0.30:
            return "declining"
        return "stable"
