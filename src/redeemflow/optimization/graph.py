"""Optimization domain — directed weighted graph of loyalty program transfer partnerships.

Uses NetworkX DiGraph to model transfer paths between programs,
then finds optimal redemption paths via BFS traversal.
"""

from __future__ import annotations

import math
from collections import deque

import networkx as nx

from redeemflow.optimization.models import RedemptionOption, TransferPartner, TransferPath
from redeemflow.portfolio.models import PointBalance


class TransferGraph:
    """Directed weighted graph of loyalty program transfer partnerships."""

    def __init__(self) -> None:
        self._graph: nx.DiGraph = nx.DiGraph()
        self._redemptions: dict[str, list[RedemptionOption]] = {}

    def add_partner(self, partner: TransferPartner) -> None:
        """Add a transfer partnership as a directed weighted edge."""
        self._graph.add_edge(
            partner.source_program,
            partner.target_program,
            partner=partner,
            weight=partner.effective_ratio,
        )

    def add_redemption(self, option: RedemptionOption) -> None:
        """Store a redemption option as a node attribute."""
        if option.program not in self._graph:
            self._graph.add_node(option.program)
        self._redemptions.setdefault(option.program, []).append(option)

    @property
    def programs(self) -> set[str]:
        """All programs in the graph."""
        return set(self._graph.nodes)

    @property
    def partner_count(self) -> int:
        """Number of transfer partnerships (edges) in the graph."""
        return self._graph.number_of_edges()

    def get_partners_from(self, source: str) -> list[TransferPartner]:
        """Get all outbound transfer partners from a source program."""
        partners: list[TransferPartner] = []
        for _, _, data in self._graph.out_edges(source, data=True):
            partners.append(data["partner"])
        return partners

    def get_redemptions(self, program: str) -> list[RedemptionOption]:
        """Get all redemption options for a program."""
        return list(self._redemptions.get(program, []))

    def find_paths(self, source: str, max_hops: int = 3) -> list[TransferPath]:
        """Find all viable transfer paths from source to any redemption.

        Uses BFS up to max_hops. Returns paths sorted by effective_cpp descending.
        """
        if source not in self._graph:
            return []

        paths: list[TransferPath] = []

        # BFS: queue entries are (current_program, steps_so_far, cumulative_ratio)
        queue: deque[tuple[str, tuple[TransferPartner, ...], float]] = deque()
        queue.append((source, (), 1.0))

        visited_per_path: set[tuple[str, ...]] = set()

        while queue:
            current, steps, cumulative_ratio = queue.popleft()

            # Check for redemptions at current node
            for redemption in self.get_redemptions(current):
                if len(steps) == 0:
                    # Direct redemption (no transfer needed) — skip, that's not a transfer path
                    continue

                if cumulative_ratio <= 0:
                    continue

                source_points = math.ceil(redemption.points_required / cumulative_ratio)
                effective_cpp = redemption.cash_value / source_points * 100 if source_points > 0 else 0.0

                paths.append(
                    TransferPath(
                        steps=steps,
                        redemption=redemption,
                        source_points_needed=source_points,
                        effective_cpp=effective_cpp,
                        total_hops=len(steps),
                    )
                )

            # Explore neighbors if within hop limit
            if len(steps) < max_hops:
                for _, neighbor, data in self._graph.out_edges(current, data=True):
                    partner: TransferPartner = data["partner"]
                    # Prevent cycles within a single path
                    path_key = tuple(s.target_program for s in steps) + (neighbor,)
                    if neighbor == source or neighbor in {s.target_program for s in steps}:
                        continue
                    if path_key in visited_per_path:
                        continue
                    visited_per_path.add(path_key)

                    new_ratio = cumulative_ratio * partner.effective_ratio
                    queue.append((neighbor, steps + (partner,), new_ratio))

        return sorted(paths, key=lambda p: p.effective_cpp, reverse=True)

    def find_best_path(self, source: str, points: int) -> TransferPath | None:
        """Find the best single transfer path for a given balance.

        Returns the highest effective_cpp path where the user has enough points.
        """
        all_paths = self.find_paths(source)
        for path in all_paths:
            if points >= path.source_points_needed:
                return path
        return None

    def optimize_portfolio(self, balances: list[PointBalance]) -> list[TransferPath]:
        """Optimize across all programs in a portfolio.

        Returns top recommendations sorted by effective_cpp descending.
        """
        recommendations: list[TransferPath] = []
        for balance in balances:
            if balance.points <= 0:
                continue
            best = self.find_best_path(balance.program_code, balance.points)
            if best is not None:
                recommendations.append(best)

        return sorted(recommendations, key=lambda p: p.effective_cpp, reverse=True)
