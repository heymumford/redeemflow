"""Achievement system — gamification for loyalty optimization milestones.

Beck: Achievements are facts — either earned or not.
Fowler: Specification pattern — each achievement has a predicate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class AchievementCategory(str, Enum):
    PORTFOLIO = "portfolio"
    OPTIMIZATION = "optimization"
    COMMUNITY = "community"
    LEARNING = "learning"
    MILESTONE = "milestone"


class AchievementRarity(str, Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


@dataclass(frozen=True)
class AchievementDef:
    """Definition of an achievement."""

    achievement_id: str
    name: str
    description: str
    category: AchievementCategory
    rarity: AchievementRarity
    points_reward: int = 0
    icon: str = ""


@dataclass(frozen=True)
class EarnedAchievement:
    """A user's earned achievement."""

    achievement_id: str
    earned_at: str
    detail: str = ""


# Achievement catalog
ACHIEVEMENTS: dict[str, AchievementDef] = {
    "first_sync": AchievementDef(
        "first_sync",
        "First Sync",
        "Connect your first loyalty program",
        AchievementCategory.PORTFOLIO,
        AchievementRarity.COMMON,
        100,
    ),
    "portfolio_5": AchievementDef(
        "portfolio_5",
        "Diversified",
        "Track 5 or more loyalty programs",
        AchievementCategory.PORTFOLIO,
        AchievementRarity.UNCOMMON,
        250,
    ),
    "points_100k": AchievementDef(
        "points_100k",
        "Points Collector",
        "Accumulate 100,000+ points across all programs",
        AchievementCategory.MILESTONE,
        AchievementRarity.UNCOMMON,
        500,
    ),
    "points_1m": AchievementDef(
        "points_1m",
        "Millionaire",
        "Accumulate 1,000,000+ points across all programs",
        AchievementCategory.MILESTONE,
        AchievementRarity.LEGENDARY,
        5000,
    ),
    "first_goal": AchievementDef(
        "first_goal",
        "Goal Setter",
        "Create your first savings goal",
        AchievementCategory.OPTIMIZATION,
        AchievementRarity.COMMON,
        100,
    ),
    "goal_complete": AchievementDef(
        "goal_complete",
        "Goal Crusher",
        "Complete a savings goal",
        AchievementCategory.OPTIMIZATION,
        AchievementRarity.UNCOMMON,
        500,
    ),
    "first_trip": AchievementDef(
        "first_trip",
        "Trip Planner",
        "Create your first multi-segment trip",
        AchievementCategory.OPTIMIZATION,
        AchievementRarity.COMMON,
        100,
    ),
    "sweet_spot_hunter": AchievementDef(
        "sweet_spot_hunter",
        "Sweet Spot Hunter",
        "Find a redemption with 2x+ baseline value",
        AchievementCategory.OPTIMIZATION,
        AchievementRarity.RARE,
        1000,
    ),
    "first_donation": AchievementDef(
        "first_donation",
        "Generous Spirit",
        "Make your first points donation",
        AchievementCategory.COMMUNITY,
        AchievementRarity.COMMON,
        200,
    ),
    "household_builder": AchievementDef(
        "household_builder",
        "Family Planner",
        "Add 2+ members to your household",
        AchievementCategory.COMMUNITY,
        AchievementRarity.UNCOMMON,
        300,
    ),
    "pool_contributor": AchievementDef(
        "pool_contributor",
        "Team Player",
        "Contribute to a community pool",
        AchievementCategory.COMMUNITY,
        AchievementRarity.UNCOMMON,
        300,
    ),
    "transfer_explorer": AchievementDef(
        "transfer_explorer",
        "Transfer Explorer",
        "Explore 10+ transfer partnerships",
        AchievementCategory.LEARNING,
        AchievementRarity.RARE,
        500,
    ),
    "value_optimizer": AchievementDef(
        "value_optimizer",
        "Value Optimizer",
        "Achieve 2cpp+ on a booking",
        AchievementCategory.OPTIMIZATION,
        AchievementRarity.EPIC,
        2000,
    ),
}


@dataclass
class UserAchievements:
    """Tracks a user's earned achievements."""

    user_id: str
    earned: list[EarnedAchievement] = field(default_factory=list)

    def grant(self, achievement_id: str, detail: str = "", timestamp: str = "") -> bool:
        """Grant an achievement. Returns False if already earned."""
        if self.has(achievement_id):
            return False

        from datetime import UTC, datetime

        earned = EarnedAchievement(
            achievement_id=achievement_id,
            earned_at=timestamp or datetime.now(UTC).isoformat(),
            detail=detail,
        )
        self.earned.append(earned)
        return True

    def has(self, achievement_id: str) -> bool:
        return any(e.achievement_id == achievement_id for e in self.earned)

    def total_reward_points(self) -> int:
        total = 0
        for e in self.earned:
            defn = ACHIEVEMENTS.get(e.achievement_id)
            if defn:
                total += defn.points_reward
        return total

    def progress_summary(self) -> dict:
        earned_count = len(self.earned)
        total_count = len(ACHIEVEMENTS)
        return {
            "earned": earned_count,
            "total": total_count,
            "completion_pct": round(earned_count / total_count * 100, 1) if total_count > 0 else 0,
            "reward_points": self.total_reward_points(),
        }


# In-memory store
_USER_ACHIEVEMENTS: dict[str, UserAchievements] = {}


def get_user_achievements(user_id: str) -> UserAchievements:
    if user_id not in _USER_ACHIEVEMENTS:
        _USER_ACHIEVEMENTS[user_id] = UserAchievements(user_id=user_id)
    return _USER_ACHIEVEMENTS[user_id]
