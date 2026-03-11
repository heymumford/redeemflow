"""Savings goals — target redemption tracking with progress.

Beck: Goals are value objects that know their own progress.
Fowler: Specification pattern — goal completion is a predicate over state.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class GoalStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"


class GoalCategory(str, Enum):
    FLIGHT = "flight"
    HOTEL = "hotel"
    EXPERIENCE = "experience"
    UPGRADE = "upgrade"
    CUSTOM = "custom"


@dataclass(frozen=True)
class SavingsGoal:
    """A redemption target the user is saving toward."""

    goal_id: str
    name: str
    category: GoalCategory
    program_code: str
    target_points: int
    current_points: int
    status: GoalStatus = GoalStatus.ACTIVE
    target_redemption: str = ""  # e.g. "SFO-NRT business class"
    estimated_value: Decimal = Decimal("0")
    notes: str = ""


@dataclass(frozen=True)
class GoalProgress:
    """Computed progress metrics for a goal."""

    goal: SavingsGoal
    points_remaining: int
    percent_complete: Decimal
    is_achievable: bool
    earning_rate_needed: str  # e.g. "5,000 points/month for 4 months"


@dataclass(frozen=True)
class GoalsSummary:
    """Summary of all user goals."""

    total_goals: int
    active_goals: int
    completed_goals: int
    total_points_needed: int
    total_points_saved: int
    overall_progress: Decimal
    goals: list[GoalProgress]


def compute_progress(goal: SavingsGoal) -> GoalProgress:
    """Compute progress metrics for a single goal."""
    remaining = max(0, goal.target_points - goal.current_points)
    pct = Decimal("0")
    if goal.target_points > 0:
        pct = (Decimal(str(goal.current_points)) / Decimal(str(goal.target_points)) * 100).quantize(Decimal("0.1"))
        pct = min(pct, Decimal("100.0"))

    achievable = goal.current_points >= goal.target_points

    if remaining <= 0:
        rate = "Goal reached"
    elif remaining <= 10000:
        rate = f"{remaining:,} points needed — reachable in 1-2 months"
    elif remaining <= 50000:
        months = remaining // 10000 + 1
        rate = f"~{10000:,} points/month for {months} months"
    else:
        months = remaining // 15000 + 1
        rate = f"~{15000:,} points/month for {months} months"

    return GoalProgress(
        goal=goal,
        points_remaining=remaining,
        percent_complete=pct,
        is_achievable=achievable,
        earning_rate_needed=rate,
    )


def summarize_goals(goals: list[SavingsGoal]) -> GoalsSummary:
    """Build summary across all goals."""
    progress_list = [compute_progress(g) for g in goals]
    active = [g for g in goals if g.status == GoalStatus.ACTIVE]
    completed = [g for g in goals if g.status == GoalStatus.COMPLETED]

    total_needed = sum(g.target_points for g in active)
    total_saved = sum(g.current_points for g in active)

    overall = Decimal("0")
    if total_needed > 0:
        overall = (Decimal(str(total_saved)) / Decimal(str(total_needed)) * 100).quantize(Decimal("0.1"))

    return GoalsSummary(
        total_goals=len(goals),
        active_goals=len(active),
        completed_goals=len(completed),
        total_points_needed=total_needed,
        total_points_saved=total_saved,
        overall_progress=overall,
        goals=progress_list,
    )


# In-memory goal store
_GOALS: dict[str, list[SavingsGoal]] = {}
_GOAL_COUNTER: dict[str, int] = {}


def add_goal(user_id: str, goal: SavingsGoal) -> SavingsGoal:
    """Add a goal for a user."""
    if user_id not in _GOALS:
        _GOALS[user_id] = []
    _GOALS[user_id].append(goal)
    return goal


def get_goals(user_id: str) -> list[SavingsGoal]:
    """Get all goals for a user."""
    return _GOALS.get(user_id, [])


def update_goal_points(user_id: str, goal_id: str, current_points: int) -> SavingsGoal | None:
    """Update the current points for a goal."""
    goals = _GOALS.get(user_id, [])
    for i, g in enumerate(goals):
        if g.goal_id == goal_id:
            status = GoalStatus.COMPLETED if current_points >= g.target_points else g.status
            updated = SavingsGoal(
                goal_id=g.goal_id,
                name=g.name,
                category=g.category,
                program_code=g.program_code,
                target_points=g.target_points,
                current_points=current_points,
                status=status,
                target_redemption=g.target_redemption,
                estimated_value=g.estimated_value,
                notes=g.notes,
            )
            goals[i] = updated
            return updated
    return None


def next_goal_id(user_id: str) -> str:
    """Generate next goal ID for a user."""
    count = _GOAL_COUNTER.get(user_id, 0) + 1
    _GOAL_COUNTER[user_id] = count
    return f"goal_{count}"
