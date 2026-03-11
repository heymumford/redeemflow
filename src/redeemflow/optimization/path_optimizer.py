"""Path optimizer — cost-aware multi-hop routing through the transfer graph.

Fowler: Separate the policy (which path is "best") from the mechanism (finding paths).
Beck: One function answers one question. Path comparison is first-class.

Extends the base TransferGraph with:
- Cost-aware path selection (accounts for transfer fees, min_transfer gates)
- Path comparison for side-by-side analysis
- Efficiency scoring (CPP / hops)
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from redeemflow.optimization.graph import TransferGraph
from redeemflow.optimization.models import TransferPath


@dataclass(frozen=True)
class PathComparison:
    """Side-by-side comparison of two transfer paths."""

    path_a: PathSummary
    path_b: PathSummary
    cpp_difference: Decimal
    recommended: str  # "a" or "b"
    rationale: str


@dataclass(frozen=True)
class PathSummary:
    """Simplified path representation for comparison."""

    route: str  # e.g. "chase-ur → hyatt → Hyatt Cat 1-4"
    hops: int
    effective_cpp: Decimal
    source_points_needed: int
    redemption: str
    efficiency_score: Decimal  # CPP per hop


def summarize_path(path: TransferPath) -> PathSummary:
    """Convert a TransferPath to a comparable PathSummary."""
    route_parts = []
    if path.steps:
        route_parts.append(path.steps[0].source_program)
        for step in path.steps:
            route_parts.append(step.target_program)
    route_parts.append(path.redemption.description)
    route = " → ".join(route_parts)

    cpp = Decimal(str(round(path.effective_cpp, 2)))
    efficiency = (cpp / Decimal(max(path.total_hops, 1))).quantize(Decimal("0.01"))

    return PathSummary(
        route=route,
        hops=path.total_hops,
        effective_cpp=cpp,
        source_points_needed=path.source_points_needed,
        redemption=path.redemption.description,
        efficiency_score=efficiency,
    )


def compare_paths(path_a: TransferPath, path_b: TransferPath) -> PathComparison:
    """Compare two transfer paths and recommend the better one."""
    sum_a = summarize_path(path_a)
    sum_b = summarize_path(path_b)
    diff = sum_a.effective_cpp - sum_b.effective_cpp

    if sum_a.effective_cpp > sum_b.effective_cpp:
        recommended = "a"
        rationale = f"Path A offers {diff} CPP more value"
    elif sum_b.effective_cpp > sum_a.effective_cpp:
        recommended = "b"
        rationale = f"Path B offers {abs(diff)} CPP more value"
    else:
        # Same CPP — prefer fewer hops
        if sum_a.hops <= sum_b.hops:
            recommended = "a"
            rationale = "Same CPP but Path A has fewer transfers"
        else:
            recommended = "b"
            rationale = "Same CPP but Path B has fewer transfers"

    return PathComparison(
        path_a=sum_a,
        path_b=sum_b,
        cpp_difference=abs(diff),
        recommended=recommended,
        rationale=rationale,
    )


def find_top_paths(
    graph: TransferGraph,
    source: str,
    points: int,
    max_results: int = 5,
) -> list[PathSummary]:
    """Find the top N transfer paths ranked by effective CPP.

    Filters paths where the user has enough points to execute.
    """
    all_paths = graph.find_paths(source, max_hops=3)
    viable = [p for p in all_paths if points >= p.source_points_needed]
    return [summarize_path(p) for p in viable[:max_results]]


def find_efficient_paths(
    graph: TransferGraph,
    source: str,
    points: int,
    max_results: int = 5,
) -> list[PathSummary]:
    """Find paths ranked by efficiency (CPP per hop).

    Prefers simpler paths that still deliver good value.
    """
    all_paths = graph.find_paths(source, max_hops=3)
    viable = [p for p in all_paths if points >= p.source_points_needed]
    summaries = [summarize_path(p) for p in viable]
    summaries.sort(key=lambda s: s.efficiency_score, reverse=True)
    return summaries[:max_results]
