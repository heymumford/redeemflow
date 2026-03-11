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
from redeemflow.optimization.booking_optimizer import analyze_booking
from redeemflow.optimization.budget_planner import (
    AllocationTarget,
    EarningSource,
    compute_budget,
)
from redeemflow.optimization.graph import TransferGraph
from redeemflow.optimization.graph_analytics import (
    find_transfer_bonuses,
    graph_summary,
    program_connectivity,
)
from redeemflow.optimization.hotel_transfers import assess_hotel_transfer, summarize_hotel_program
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


class BookingAnalysisRequest(BaseModel):
    cash_price: float
    points_price: int
    program_code: str
    available_points: int = 0
    transfers: list[dict] = []


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


class HotelTransferRequest(BaseModel):
    hotel_program: str
    airline_program: str
    points: int = 100000


@router.post("/api/hotel-transfer/assess")
def assess_transfer(req: HotelTransferRequest):
    """Assess whether a hotel-to-airline transfer is worthwhile."""
    assessment = assess_hotel_transfer(_GRAPH, req.hotel_program, req.airline_program, req.points)
    if assessment is None:
        return {"error": f"No transfer partnership between {req.hotel_program} and {req.airline_program}"}
    return {
        "hotel_program": assessment.hotel_program,
        "airline_program": assessment.airline_program,
        "transfer_ratio": assessment.transfer_ratio,
        "hotel_points_needed": assessment.hotel_points_needed,
        "airline_miles_received": assessment.airline_miles_received,
        "hotel_cpp_if_redeemed": str(assessment.hotel_cpp_if_redeemed),
        "airline_cpp_if_transferred": str(assessment.airline_cpp_if_transferred),
        "value_ratio": str(assessment.value_ratio),
        "recommendation": assessment.recommendation,
        "rationale": assessment.rationale,
    }


@router.get("/api/hotel-transfer/summary/{program}")
def hotel_transfer_summary(program: str, points: int = 100000):
    """Get hotel program transfer economics summary."""
    if program not in _GRAPH.programs:
        return {"error": f"Unknown program: {program}"}
    summary = summarize_hotel_program(_GRAPH, program, points)
    return {
        "program": summary.program,
        "airline_partners": summary.airline_partners,
        "transfer_ratio": summary.transfer_ratio,
        "best_direct_cpp": str(summary.best_direct_cpp),
        "best_transfer_cpp": str(summary.best_transfer_cpp),
        "transfer_penalty": str(summary.transfer_penalty),
        "assessments": [
            {
                "airline": a.airline_program,
                "transfer_ratio": a.transfer_ratio,
                "airline_miles_received": a.airline_miles_received,
                "hotel_cpp": str(a.hotel_cpp_if_redeemed),
                "airline_cpp": str(a.airline_cpp_if_transferred),
                "value_ratio": str(a.value_ratio),
                "recommendation": a.recommendation,
            }
            for a in summary.assessments
        ],
    }


class BudgetSourceInput(BaseModel):
    name: str
    program_code: str
    monthly_points: int
    category: str = "card_spend"


class BudgetTargetInput(BaseModel):
    name: str
    program_code: str
    points_needed: int
    target_date: str = ""
    priority: int = 1


class BudgetPlanRequest(BaseModel):
    sources: list[BudgetSourceInput]
    targets: list[BudgetTargetInput] = []
    current_balances: dict[str, int] = {}


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


@router.post("/api/budget-plan")
def budget_plan(req: BudgetPlanRequest, user: User = Depends(get_current_user)):
    """Compute annual points budget with earning projections and allocation feasibility."""
    sources = [
        EarningSource(
            name=s.name,
            program_code=s.program_code,
            monthly_points=s.monthly_points,
            category=s.category,
        )
        for s in req.sources
    ]
    targets = [
        AllocationTarget(
            name=t.name,
            program_code=t.program_code,
            points_needed=t.points_needed,
            target_date=t.target_date,
            priority=t.priority,
        )
        for t in req.targets
    ]
    result = compute_budget(sources, targets, req.current_balances or None)
    return {
        "total_annual_earnings": result.total_annual_earnings,
        "total_allocation_needed": result.total_allocation_needed,
        "surplus_or_deficit": result.surplus_or_deficit,
        "months_to_goal": result.months_to_goal,
        "forecasts": {
            code: [
                {
                    "month": f.month,
                    "projected_earnings": f.projected_earnings,
                    "cumulative": f.cumulative,
                }
                for f in forecasts
            ]
            for code, forecasts in result.forecasts_by_program.items()
        },
        "allocation_feasibility": result.allocation_feasibility,
    }


@router.post("/api/booking-analysis")
def booking_analysis(req: BookingAnalysisRequest, user: User = Depends(get_current_user)):
    """Analyze booking payment options: points vs cash vs mix."""
    val = PROGRAM_VALUATIONS.get(req.program_code)
    if val is None:
        return {"error": f"Unknown program: {req.program_code}"}

    result = analyze_booking(
        cash_price=Decimal(str(req.cash_price)),
        points_price=req.points_price,
        program_code=req.program_code,
        program_cpp=val.median_cpp,
        available_points=req.available_points,
        transfer_options=req.transfers if req.transfers else None,
    )

    return {
        "cash_price": str(result.cash_price),
        "recommendation": {
            "method": result.recommended.method.value,
            "points_cost": result.recommended.points_cost,
            "cash_cost": str(result.recommended.cash_cost),
            "effective_cpp": str(result.recommended.effective_cpp),
            "value_score": str(result.recommended.value_score),
            "description": result.recommended.description,
            "savings_vs_cash": str(result.recommended.savings_vs_cash),
        },
        "reason": result.recommendation_reason,
        "options": [
            {
                "method": o.method.value,
                "points_cost": o.points_cost,
                "cash_cost": str(o.cash_cost),
                "effective_cpp": str(o.effective_cpp),
                "value_score": str(o.value_score),
                "program_code": o.program_code,
                "description": o.description,
                "is_recommended": o.is_recommended,
                "savings_vs_cash": str(o.savings_vs_cash),
            }
            for o in result.options
        ],
    }
