"""Recommendations domain — CPP optimization engine.

Uses graph-based transfer path optimization via NetworkX.
Falls back to hardcoded recommendations if the graph produces no results.
"""

from __future__ import annotations

from decimal import Decimal

from redeemflow.optimization.graph import TransferGraph
from redeemflow.optimization.seed_data import ALL_PARTNERS, REDEMPTION_OPTIONS
from redeemflow.portfolio.models import PointBalance
from redeemflow.recommendations.models import Recommendation

MIN_POINTS_THRESHOLD = 1000

# Curated transfer partner CPP values (best known redemption for each program).
# Source: community-sourced CPP benchmarks. Fallback for programs not in the graph.
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

# Map legacy program codes to graph program names for graph lookups
_CODE_TO_GRAPH: dict[str, str] = {
    "UR": "chase-ur",
    "MR": "amex-mr",
    "TY": "citi-ty",
}


def _build_default_graph() -> TransferGraph:
    """Build the transfer graph from seed data."""
    graph = TransferGraph()
    for partner in ALL_PARTNERS:
        graph.add_partner(partner)
    for option in REDEMPTION_OPTIONS:
        graph.add_redemption(option)
    return graph


class RecommendationEngine:
    def __init__(self, graph: TransferGraph | None = None) -> None:
        self._graph = graph if graph is not None else _build_default_graph()

    def recommend(self, balances: list[PointBalance]) -> list[Recommendation]:
        if not balances:
            return []

        recs: list[Recommendation] = []
        for balance in balances:
            if balance.points < MIN_POINTS_THRESHOLD:
                continue

            # Try graph-based recommendation first
            graph_rec = self._graph_recommend(balance)
            if graph_rec is not None:
                recs.append(graph_rec)
                continue

            # Fall back to hardcoded
            fallback = self._hardcoded_recommend(balance)
            if fallback is not None:
                recs.append(fallback)

        return sorted(recs, key=lambda r: r.cpp_gain, reverse=True)

    def _graph_recommend(self, balance: PointBalance) -> Recommendation | None:
        """Try to find a graph-based recommendation for a balance."""
        graph_key = _CODE_TO_GRAPH.get(balance.program_code)
        if graph_key is None:
            return None

        path = self._graph.find_best_path(graph_key, balance.points)
        if path is None:
            return None

        effective_cpp = Decimal(str(round(path.effective_cpp, 2)))
        cpp_gain = effective_cpp - balance.cpp_baseline
        if cpp_gain <= 0:
            return None

        target = path.steps[-1].target_program if path.steps else graph_key
        action = f"Transfer to {target} for {path.redemption.description}"

        return Recommendation(
            program_code=balance.program_code,
            action=action,
            rationale=(
                f"{path.redemption.description} offers {effective_cpp} CPP vs {balance.cpp_baseline} CPP baseline"
            ),
            cpp_gain=cpp_gain,
            points_involved=balance.points,
        )

    def _hardcoded_recommend(self, balance: PointBalance) -> Recommendation | None:
        """Fallback to hardcoded recommendation data."""
        redemption = _BEST_REDEMPTIONS.get(balance.program_code)
        if not redemption:
            return None

        action, best_cpp, rationale_template = redemption
        cpp_gain = best_cpp - balance.cpp_baseline
        if cpp_gain <= 0:
            return None

        return Recommendation(
            program_code=balance.program_code,
            action=action,
            rationale=rationale_template.format(cpp=best_cpp, baseline=balance.cpp_baseline),
            cpp_gain=cpp_gain,
            points_involved=balance.points,
        )
