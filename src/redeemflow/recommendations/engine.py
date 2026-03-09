"""Recommendations domain — CPP optimization engine.

Walking skeleton: hardcoded transfer partner data.
Sprint 3+ replaces with graph-based optimization via NetworkX.
"""

from __future__ import annotations

from decimal import Decimal

from redeemflow.portfolio.models import PointBalance
from redeemflow.recommendations.models import Recommendation

MIN_POINTS_THRESHOLD = 1000

# Curated transfer partner CPP values (best known redemption for each program).
# Source: community-sourced CPP benchmarks. Updated manually for MVP.
_BEST_REDEMPTIONS: dict[str, tuple[str, Decimal, str]] = {
    "UA": (
        "Book Polaris business class",
        Decimal("2.2"),
        "Polaris J offers {cpp} CPP vs {baseline} CPP baseline",
    ),
    "AA": (
        "Book JAL first class via AA",
        Decimal("2.5"),
        "JAL F via AA offers {cpp} CPP vs {baseline} CPP baseline",
    ),
    "DL": (
        "Book Delta One to Europe",
        Decimal("1.8"),
        "Delta One transatlantic offers {cpp} CPP vs {baseline} CPP baseline",
    ),
    "MR": (
        "Transfer to Aeroplan for Star Alliance",
        Decimal("1.8"),
        "Aeroplan sweet spots offer {cpp} CPP vs {baseline} CPP baseline",
    ),
    "UR": (
        "Transfer to Hyatt for Category 1-4",
        Decimal("2.0"),
        "Hyatt Cat 1-4 offers {cpp} CPP vs {baseline} CPP baseline",
    ),
    "HH": (
        "Book 5th-night-free aspirational",
        Decimal("0.7"),
        "5th night free aspirational offers {cpp} CPP vs {baseline} CPP baseline",
    ),
    "TY": (
        "Transfer to Turkish Miles&Smiles",
        Decimal("1.9"),
        "Turkish J offers {cpp} CPP vs {baseline} CPP baseline",
    ),
}


class RecommendationEngine:
    def recommend(self, balances: list[PointBalance]) -> list[Recommendation]:
        if not balances:
            return []

        recs: list[Recommendation] = []
        for balance in balances:
            if balance.points < MIN_POINTS_THRESHOLD:
                continue

            redemption = _BEST_REDEMPTIONS.get(balance.program_code)
            if not redemption:
                continue

            action, best_cpp, rationale_template = redemption
            cpp_gain = best_cpp - balance.cpp_baseline
            if cpp_gain <= 0:
                continue

            recs.append(
                Recommendation(
                    program_code=balance.program_code,
                    action=action,
                    rationale=rationale_template.format(cpp=best_cpp, baseline=balance.cpp_baseline),
                    cpp_gain=cpp_gain,
                    points_involved=balance.points,
                )
            )

        return sorted(recs, key=lambda r: r.cpp_gain, reverse=True)
