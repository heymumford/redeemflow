"""Optimization API — personalized optimizer, timing advisor, alerts, multi-traveler.

All endpoints require Premium+ auth.
"""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from redeemflow.identity.auth import get_current_user
from redeemflow.identity.models import User
from redeemflow.notifications.alerts import AlertEngine
from redeemflow.optimization.graph import TransferGraph
from redeemflow.optimization.graph_analytics import (
    find_transfer_bonuses,
    graph_summary,
    program_connectivity,
)
from redeemflow.optimization.multi_traveler import MultiTravelerOptimizer, Traveler
from redeemflow.optimization.path_optimizer import find_efficient_paths, find_top_paths
from redeemflow.optimization.personal_optimizer import PersonalOptimizer
from redeemflow.optimization.seed_data import ALL_PARTNERS, REDEMPTION_OPTIONS
from redeemflow.optimization.timing_advisor import TimingAdvisor
from redeemflow.portfolio.awardwallet import FakeAwardWalletAdapter
from redeemflow.portfolio.expiration import EXPIRATION_POLICIES
from redeemflow.portfolio.models import PointBalance
from redeemflow.valuations.seed_data import PROGRAM_VALUATIONS

router = APIRouter()


def _build_graph() -> TransferGraph:
    graph = TransferGraph()
    for p in ALL_PARTNERS:
        graph.add_partner(p)
    for r in REDEMPTION_OPTIONS:
        graph.add_redemption(r)
    return graph


_GRAPH = _build_graph()
_FETCHER = FakeAwardWalletAdapter()


class TimingAdviceRequest(BaseModel):
    program_code: str
    points: int


class TravelerInput(BaseModel):
    name: str
    balances: list[dict]


class MultiTravelerRequest(BaseModel):
    destination: str
    travelers: list[TravelerInput]


@router.post("/api/optimize")
def optimize(user: User = Depends(get_current_user)):
    balances = _FETCHER.fetch_balances(user.id)
    optimizer = PersonalOptimizer(graph=_GRAPH, valuations=PROGRAM_VALUATIONS)
    actions = optimizer.top_actions(balances, n=10)
    return {
        "actions": [
            {
                "program_code": a.program_code,
                "action_type": a.action_type,
                "description": a.description,
                "estimated_value_gain": str(a.estimated_value_gain),
                "urgency": a.urgency,
                "confidence": a.confidence,
            }
            for a in actions
        ]
    }


@router.post("/api/timing-advice")
def timing_advice(req: TimingAdviceRequest, user: User = Depends(get_current_user)):
    advisor = TimingAdvisor(graph=_GRAPH, valuations=PROGRAM_VALUATIONS)
    advice = advisor.advise(req.program_code, req.points)
    return {
        "advice": {
            "program_code": advice.program_code,
            "recommendation": advice.recommendation,
            "rationale": advice.rationale,
            "confidence": advice.confidence,
            "cpp_trend": advice.cpp_trend,
            "active_bonuses": advice.active_bonuses,
        }
    }


@router.get("/api/alerts")
def alerts(user: User = Depends(get_current_user)):
    balances = _FETCHER.fetch_balances(user.id)
    engine = AlertEngine()
    alert_list = engine.generate_alerts(balances, _GRAPH, EXPIRATION_POLICIES)
    return {
        "alerts": [
            {
                "id": a.id,
                "alert_type": a.alert_type.value,
                "priority": a.priority.value,
                "title": a.title,
                "message": a.message,
                "program_code": a.program_code,
                "created_at": a.created_at,
            }
            for a in alert_list
        ]
    }


@router.post("/api/multi-traveler")
def multi_traveler(req: MultiTravelerRequest, user: User = Depends(get_current_user)):
    """Plan a multi-traveler trip with optimized point redemptions."""
    travelers = []
    for t in req.travelers:
        balances = [
            PointBalance(
                program_code=b["program_code"],
                points=b["points"],
                cpp_baseline=Decimal(str(b.get("cpp_baseline", "1.5"))),
            )
            for b in t.balances
        ]
        travelers.append(Traveler(name=t.name, balances=balances))

    optimizer = MultiTravelerOptimizer(graph=_GRAPH, valuations=PROGRAM_VALUATIONS)
    plan = optimizer.plan(req.destination, travelers)
    return {
        "destination": plan.destination,
        "travelers": [{"name": t.name, "balance_count": len(t.balances)} for t in plan.travelers],
        "bookings": [
            {
                "traveler_name": b.traveler_name,
                "program_code": b.program_code,
                "points_used": b.points_used,
                "booking_type": b.booking_type,
                "estimated_value": str(b.estimated_value),
            }
            for b in plan.bookings
        ],
        "total_points_used": plan.total_points_used,
        "total_estimated_value": str(plan.total_estimated_value),
        "total_estimated_savings": str(plan.total_estimated_savings),
    }


@router.get("/api/graph/summary")
def get_graph_summary():
    """Get high-level transfer graph statistics."""
    summary = graph_summary(_GRAPH)
    return {
        "total_programs": summary.total_programs,
        "total_partnerships": summary.total_partnerships,
        "hub_programs": summary.hub_programs,
        "isolated_programs": summary.isolated_programs,
        "avg_connections": summary.avg_connections,
        "densest_program": summary.densest_program,
        "density": summary.density,
    }


@router.get("/api/graph/connectivity/{program}")
def get_program_connectivity(program: str):
    """Get connectivity details for a specific program."""
    if program not in _GRAPH.programs:
        return {"error": f"Unknown program: {program}"}
    conn = program_connectivity(_GRAPH, program)
    return {
        "program": conn.program,
        "outbound_partners": conn.outbound_partners,
        "inbound_partners": conn.inbound_partners,
        "total_connections": conn.total_connections,
        "best_outbound_ratio": conn.best_outbound_ratio,
        "reachable_programs": conn.reachable_programs,
        "is_hub": conn.is_hub,
    }


@router.get("/api/graph/bonuses")
def get_transfer_bonuses():
    """Get all active transfer bonuses."""
    bonuses = find_transfer_bonuses(_GRAPH)
    return {
        "count": len(bonuses),
        "bonuses": [
            {
                "source_program": b.source_program,
                "target_program": b.target_program,
                "transfer_ratio": b.transfer_ratio,
                "transfer_bonus": b.transfer_bonus,
                "effective_ratio": b.effective_ratio,
            }
            for b in bonuses
        ],
    }


class PathSearchRequest(BaseModel):
    program: str
    points: int
    max_results: int = 5


@router.post("/api/paths/top")
def top_paths(req: PathSearchRequest):
    """Find top transfer paths ranked by effective CPP."""
    paths = find_top_paths(_GRAPH, req.program, req.points, req.max_results)
    return {
        "program": req.program,
        "points": req.points,
        "paths": [
            {
                "route": p.route,
                "hops": p.hops,
                "effective_cpp": str(p.effective_cpp),
                "source_points_needed": p.source_points_needed,
                "redemption": p.redemption,
                "efficiency_score": str(p.efficiency_score),
            }
            for p in paths
        ],
    }


@router.post("/api/paths/efficient")
def efficient_paths(req: PathSearchRequest):
    """Find paths ranked by efficiency (CPP per hop)."""
    paths = find_efficient_paths(_GRAPH, req.program, req.points, req.max_results)
    return {
        "program": req.program,
        "points": req.points,
        "paths": [
            {
                "route": p.route,
                "hops": p.hops,
                "effective_cpp": str(p.effective_cpp),
                "source_points_needed": p.source_points_needed,
                "redemption": p.redemption,
                "efficiency_score": str(p.efficiency_score),
            }
            for p in paths
        ],
    }
