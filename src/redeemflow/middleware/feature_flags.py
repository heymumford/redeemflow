"""Feature flags — runtime toggles with tier gates and percentage rollouts.

Beck: A flag is a fact — on or off for a given context.
Fowler: Strategy pattern — flag evaluation strategies are pluggable.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum


class FlagStatus(str, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    PERCENTAGE = "percentage"
    TIER_GATED = "tier_gated"


@dataclass(frozen=True)
class FeatureFlag:
    """A feature flag definition."""

    name: str
    description: str
    status: FlagStatus
    percentage: int = 100  # 0-100, used when status=PERCENTAGE
    allowed_tiers: list[str] = field(default_factory=list)  # used when status=TIER_GATED
    metadata: dict = field(default_factory=dict)


def _hash_user_to_bucket(user_id: str, flag_name: str) -> int:
    """Deterministic hash of user+flag to a 0-99 bucket."""
    h = hashlib.sha256(f"{user_id}:{flag_name}".encode()).hexdigest()
    return int(h[:8], 16) % 100


@dataclass
class FlagRegistry:
    """Central registry of feature flags."""

    _flags: dict[str, FeatureFlag] = field(default_factory=dict)

    def register(self, flag: FeatureFlag) -> None:
        """Register or update a flag."""
        self._flags[flag.name] = flag

    def is_enabled(self, flag_name: str, user_id: str = "", tier: str = "free") -> bool:
        """Evaluate whether a flag is enabled for a given context."""
        flag = self._flags.get(flag_name)
        if flag is None:
            return False

        if flag.status == FlagStatus.ENABLED:
            return True
        if flag.status == FlagStatus.DISABLED:
            return False
        if flag.status == FlagStatus.TIER_GATED:
            return tier in flag.allowed_tiers
        if flag.status == FlagStatus.PERCENTAGE:
            if not user_id:
                return False
            bucket = _hash_user_to_bucket(user_id, flag_name)
            return bucket < flag.percentage

        return False

    def get_flag(self, flag_name: str) -> FeatureFlag | None:
        return self._flags.get(flag_name)

    def list_flags(self) -> list[FeatureFlag]:
        return list(self._flags.values())

    def enabled_for_user(self, user_id: str, tier: str = "free") -> list[str]:
        """List all flags enabled for a specific user."""
        return [name for name in self._flags if self.is_enabled(name, user_id, tier)]

    def flag_summary(self) -> dict:
        """Summary of all flags."""
        statuses = [f.status for f in self._flags.values()]
        return {
            "total": len(statuses),
            "enabled": statuses.count(FlagStatus.ENABLED),
            "disabled": statuses.count(FlagStatus.DISABLED),
            "percentage": statuses.count(FlagStatus.PERCENTAGE),
            "tier_gated": statuses.count(FlagStatus.TIER_GATED),
        }


# Default flags for RedeemFlow
DEFAULT_FLAGS = [
    FeatureFlag("seasonal_pricing", "Seasonal pricing intelligence", FlagStatus.ENABLED),
    FeatureFlag("trip_sharing", "Trip sharing via links", FlagStatus.ENABLED),
    FeatureFlag("budget_planner", "Annual budget planner", FlagStatus.TIER_GATED, allowed_tiers=["premium", "pro"]),
    FeatureFlag("api_keys", "Programmatic API key access", FlagStatus.TIER_GATED, allowed_tiers=["pro"]),
    FeatureFlag("booking_optimizer", "Points vs cash optimizer", FlagStatus.ENABLED),
    FeatureFlag("program_health", "Program health scores", FlagStatus.PERCENTAGE, percentage=80),
    FeatureFlag("export_csv", "CSV portfolio export", FlagStatus.ENABLED),
    FeatureFlag(
        "multi_traveler", "Multi-traveler trip planning", FlagStatus.TIER_GATED, allowed_tiers=["premium", "pro"]
    ),
    FeatureFlag("webhook_retry", "Webhook delivery retry", FlagStatus.ENABLED),
    FeatureFlag("dark_mode", "Dark mode UI", FlagStatus.PERCENTAGE, percentage=50),
]

# Singleton
_REGISTRY = FlagRegistry()
for _f in DEFAULT_FLAGS:
    _REGISTRY.register(_f)


def get_flag_registry() -> FlagRegistry:
    return _REGISTRY


def reset_flag_registry() -> None:
    global _REGISTRY
    _REGISTRY = FlagRegistry()
    for f in DEFAULT_FLAGS:
        _REGISTRY.register(f)
