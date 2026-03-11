"""Graph analytics — connectivity scoring, path metrics, and transfer network analysis.

Fowler: Separate read models from write models. Analytics is a read-only projection.
Beck: Each function answers one question about the graph structure.
"""

from __future__ import annotations

from dataclasses import dataclass

from redeemflow.optimization.graph import TransferGraph
from redeemflow.optimization.models import TransferPartner


@dataclass(frozen=True)
class ProgramConnectivity:
    """How well-connected a program is in the transfer network."""

    program: str
    outbound_partners: int
    inbound_partners: int
    total_connections: int
    best_outbound_ratio: float
    reachable_programs: int
    is_hub: bool  # Hub = 5+ outbound partners


@dataclass(frozen=True)
class GraphSummary:
    """High-level graph statistics."""

    total_programs: int
    total_partnerships: int
    hub_programs: list[str]
    isolated_programs: list[str]
    avg_connections: float
    densest_program: str
    density: float


def program_connectivity(graph: TransferGraph, program: str) -> ProgramConnectivity:
    """Analyze how well-connected a single program is."""
    outbound = graph.get_partners_from(program)
    inbound_count = 0
    for p in graph.programs:
        for partner in graph.get_partners_from(p):
            if partner.target_program == program:
                inbound_count += 1

    best_ratio = max((p.effective_ratio for p in outbound), default=0.0)

    # Count reachable programs (1 hop)
    reachable = {p.target_program for p in outbound}

    return ProgramConnectivity(
        program=program,
        outbound_partners=len(outbound),
        inbound_partners=inbound_count,
        total_connections=len(outbound) + inbound_count,
        best_outbound_ratio=best_ratio,
        reachable_programs=len(reachable),
        is_hub=len(outbound) >= 5,
    )


def graph_summary(graph: TransferGraph) -> GraphSummary:
    """Compute high-level graph statistics."""
    programs = list(graph.programs)
    connectivities = [program_connectivity(graph, p) for p in programs]

    hubs = [c.program for c in connectivities if c.is_hub]
    isolated = [c.program for c in connectivities if c.total_connections == 0]
    avg = sum(c.total_connections for c in connectivities) / len(connectivities) if connectivities else 0.0

    densest = max(connectivities, key=lambda c: c.total_connections) if connectivities else None
    max_possible_edges = len(programs) * (len(programs) - 1) if len(programs) > 1 else 1
    density = graph.partner_count / max_possible_edges

    return GraphSummary(
        total_programs=len(programs),
        total_partnerships=graph.partner_count,
        hub_programs=sorted(hubs),
        isolated_programs=sorted(isolated),
        avg_connections=round(avg, 1),
        densest_program=densest.program if densest else "",
        density=round(density, 3),
    )


def find_transfer_bonuses(graph: TransferGraph) -> list[TransferPartner]:
    """Find all current transfer bonuses (bonus > 0)."""
    bonuses = []
    for program in graph.programs:
        for partner in graph.get_partners_from(program):
            if partner.transfer_bonus > 0:
                bonuses.append(partner)
    return sorted(bonuses, key=lambda p: p.transfer_bonus, reverse=True)
