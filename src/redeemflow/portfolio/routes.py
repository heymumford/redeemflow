"""Portfolio API — balance retrieval and sync endpoints.

Beck: Thin routes that delegate to the PortfolioPort adapter.
Fowler: Adapter injected via app.state, resolved through Depends.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from redeemflow.identity.auth import get_current_user
from redeemflow.identity.models import User
from redeemflow.portfolio.calendar import build_calendar
from redeemflow.portfolio.expiration import EXPIRATION_POLICIES
from redeemflow.portfolio.goals import (
    GoalCategory,
    SavingsGoal,
    add_goal,
    get_goals,
    next_goal_id,
    summarize_goals,
    update_goal_points,
)
from redeemflow.portfolio.household import HouseholdMember, get_or_create_household
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


@router.get("/api/portfolio/calendar")
def expiration_calendar(
    user: User = Depends(get_current_user),
    port: PortfolioPort = Depends(_get_portfolio_port),
):
    """Get expiration calendar for all portfolio balances."""
    balances = port.fetch_balances(user.id)
    summary = build_calendar(balances, EXPIRATION_POLICIES)

    return {
        "total_programs": summary.total_programs,
        "programs_with_expiry": summary.programs_with_expiry,
        "programs_safe": summary.programs_safe,
        "critical_count": summary.critical_count,
        "warning_count": summary.warning_count,
        "total_points_at_risk": summary.total_points_at_risk,
        "total_value_at_risk": str(summary.total_value_at_risk),
        "events": [
            {
                "program_code": e.program_code,
                "program_name": e.program_name,
                "event_type": e.event_type,
                "days_remaining": e.days_remaining,
                "points_at_risk": e.points_at_risk,
                "value_at_risk": str(e.value_at_risk),
                "urgency": e.urgency.value,
                "description": e.description,
                "action": e.action,
            }
            for e in summary.events
        ],
        "next_event": (
            {
                "program_code": summary.next_event.program_code,
                "days_remaining": summary.next_event.days_remaining,
                "urgency": summary.next_event.urgency.value,
                "description": summary.next_event.description,
            }
            if summary.next_event
            else None
        ),
    }


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


class AddMemberRequest(BaseModel):
    member_id: str
    name: str
    role: str = "other"
    programs: dict[str, int] = {}


@router.get("/api/household")
def get_household_summary(user: User = Depends(get_current_user)):
    """Get household summary with pooled balances and optimization opportunities."""
    household = get_or_create_household(user.id)
    summary = household.summarize()
    return {
        "household_id": summary.household_id,
        "member_count": summary.member_count,
        "total_programs": summary.total_programs,
        "total_points": summary.total_points,
        "unique_programs": summary.unique_programs,
        "pooled_balances": [
            {
                "program_code": b.program_code,
                "total_points": b.total_points,
                "member_count": b.member_count,
                "contributors": b.contributors,
            }
            for b in summary.pooled_balances
        ],
        "optimization_opportunities": summary.optimization_opportunities,
    }


@router.post("/api/household/member")
def add_household_member(req: AddMemberRequest, user: User = Depends(get_current_user)):
    """Add a member to the household."""
    household = get_or_create_household(user.id)
    member = HouseholdMember(
        member_id=req.member_id,
        name=req.name,
        role=req.role,
        programs=req.programs,
    )
    household.add_member(member)
    return {"status": "added", "member_id": req.member_id, "household_members": len(household.members)}


@router.delete("/api/household/member/{member_id}")
def remove_household_member(member_id: str, user: User = Depends(get_current_user)):
    """Remove a member from the household."""
    household = get_or_create_household(user.id)
    removed = household.remove_member(member_id)
    return {"status": "removed" if removed else "not_found", "member_id": member_id}


class CreateGoalRequest(BaseModel):
    name: str
    category: str = "custom"
    program_code: str
    target_points: int
    current_points: int = 0
    target_redemption: str = ""
    estimated_value: float = 0
    notes: str = ""


class UpdateGoalPointsRequest(BaseModel):
    current_points: int


@router.get("/api/goals")
def list_goals(user: User = Depends(get_current_user)):
    """Get all savings goals with progress."""
    goals = get_goals(user.id)
    summary = summarize_goals(goals)
    return {
        "total_goals": summary.total_goals,
        "active_goals": summary.active_goals,
        "completed_goals": summary.completed_goals,
        "overall_progress": str(summary.overall_progress),
        "total_points_needed": summary.total_points_needed,
        "total_points_saved": summary.total_points_saved,
        "goals": [
            {
                "goal_id": p.goal.goal_id,
                "name": p.goal.name,
                "category": p.goal.category.value,
                "program_code": p.goal.program_code,
                "target_points": p.goal.target_points,
                "current_points": p.goal.current_points,
                "status": p.goal.status.value,
                "target_redemption": p.goal.target_redemption,
                "points_remaining": p.points_remaining,
                "percent_complete": str(p.percent_complete),
                "is_achievable": p.is_achievable,
                "earning_rate_needed": p.earning_rate_needed,
            }
            for p in summary.goals
        ],
    }


@router.post("/api/goals")
def create_goal(req: CreateGoalRequest, user: User = Depends(get_current_user)):
    """Create a new savings goal."""
    from decimal import Decimal

    try:
        category = GoalCategory(req.category)
    except ValueError:
        category = GoalCategory.CUSTOM

    goal_id = next_goal_id(user.id)
    goal = SavingsGoal(
        goal_id=goal_id,
        name=req.name,
        category=category,
        program_code=req.program_code,
        target_points=req.target_points,
        current_points=req.current_points,
        target_redemption=req.target_redemption,
        estimated_value=Decimal(str(req.estimated_value)),
        notes=req.notes,
    )
    add_goal(user.id, goal)
    return {"status": "created", "goal_id": goal_id}


@router.put("/api/goals/{goal_id}/points")
def update_points(goal_id: str, req: UpdateGoalPointsRequest, user: User = Depends(get_current_user)):
    """Update progress on a goal."""
    updated = update_goal_points(user.id, goal_id, req.current_points)
    if updated is None:
        return {"error": "Goal not found"}
    return {
        "status": "updated",
        "goal_id": goal_id,
        "current_points": updated.current_points,
        "goal_status": updated.status.value,
    }
