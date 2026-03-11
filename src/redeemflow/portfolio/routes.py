"""Portfolio API — balance retrieval and sync endpoints.

Beck: Thin routes that delegate to the PortfolioPort adapter.
Fowler: Adapter injected via app.state, resolved through Depends.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from redeemflow.identity.auth import get_current_user
from redeemflow.identity.models import User
from redeemflow.portfolio.ports import PortfolioPort
from redeemflow.recommendations.engine import RecommendationEngine

router = APIRouter()

_rec_engine = RecommendationEngine()


def _get_portfolio_port(request: Request) -> PortfolioPort:
    """Resolve the portfolio adapter from app state."""
    return request.app.state.portfolio_port


class SyncResponse(BaseModel):
    user_id: str
    status: str
    programs_synced: int
    programs_failed: int
    message: str


class BalanceResponse(BaseModel):
    program_code: str
    points: int
    estimated_value_dollars: str


class PortfolioResponse(BaseModel):
    balances: list[BalanceResponse]
    total_value_dollars: str


class RecommendationItem(BaseModel):
    program_code: str
    action: str
    rationale: str
    cpp_gain: str
    points_involved: int


class RecommendationsResponse(BaseModel):
    recommendations: list[RecommendationItem]


@router.get("/api/portfolio")
def portfolio(
    user: User = Depends(get_current_user),
    port: PortfolioPort = Depends(_get_portfolio_port),
) -> PortfolioResponse:
    balances = port.fetch_balances(user.id)
    return PortfolioResponse(
        balances=[
            BalanceResponse(
                program_code=b.program_code,
                points=b.points,
                estimated_value_dollars=str(b.estimated_value_dollars),
            )
            for b in balances
        ],
        total_value_dollars=str(sum(b.estimated_value_dollars for b in balances)),
    )


@router.get("/api/recommendations")
def recommendations(
    user: User = Depends(get_current_user),
    port: PortfolioPort = Depends(_get_portfolio_port),
) -> RecommendationsResponse:
    balances = port.fetch_balances(user.id)
    recs = _rec_engine.recommend(balances)
    return RecommendationsResponse(
        recommendations=[
            RecommendationItem(
                program_code=r.program_code,
                action=r.action,
                rationale=r.rationale,
                cpp_gain=str(r.cpp_gain),
                points_involved=r.points_involved,
            )
            for r in recs
        ],
    )


@router.post("/api/portfolio/sync")
def sync_portfolio(
    user: User = Depends(get_current_user),
    port: PortfolioPort = Depends(_get_portfolio_port),
) -> SyncResponse:
    result = port.sync(user.id)
    return SyncResponse(
        user_id=result.user_id,
        status=result.status.value,
        programs_synced=result.programs_synced,
        programs_failed=result.programs_failed,
        message=result.message,
    )
