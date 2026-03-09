"""Optimization API — personalized optimizer, timing advisor, alerts.

All endpoints require Premium+ auth.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from redeemflow.identity.auth import get_current_user
from redeemflow.identity.models import User
from redeemflow.notifications.alerts import AlertEngine
from redeemflow.optimization.graph import TransferGraph
from redeemflow.optimization.personal_optimizer import PersonalOptimizer
from redeemflow.optimization.seed_data import ALL_PARTNERS, REDEMPTION_OPTIONS
from redeemflow.optimization.timing_advisor import TimingAdvisor
from redeemflow.portfolio.expiration import EXPIRATION_POLICIES
from redeemflow.portfolio.awardwallet import FakeAwardWalletAdapter
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
