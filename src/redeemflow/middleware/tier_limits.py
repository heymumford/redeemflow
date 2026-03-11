"""Tier-based rate limiting — different limits per subscription tier.

Beck: Simple lookup table. No complexity needed.
Fowler: Policy pattern — rate limits are policies attached to tiers.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class TierPolicy:
    """Rate limit policy for a subscription tier."""

    tier: str
    requests_per_minute: int
    requests_per_hour: int
    daily_searches: int
    concurrent_exports: int
    api_key_allowed: bool


# Tier policies
TIER_POLICIES: dict[str, TierPolicy] = {
    "free": TierPolicy(
        tier="free",
        requests_per_minute=20,
        requests_per_hour=200,
        daily_searches=10,
        concurrent_exports=1,
        api_key_allowed=False,
    ),
    "premium": TierPolicy(
        tier="premium",
        requests_per_minute=60,
        requests_per_hour=1000,
        daily_searches=100,
        concurrent_exports=3,
        api_key_allowed=False,
    ),
    "pro": TierPolicy(
        tier="pro",
        requests_per_minute=200,
        requests_per_hour=5000,
        daily_searches=1000,
        concurrent_exports=10,
        api_key_allowed=True,
    ),
}


@dataclass(frozen=True)
class UsageSnapshot:
    """Current usage for a user."""

    user_id: str
    tier: str
    requests_this_minute: int
    requests_this_hour: int
    searches_today: int
    policy: TierPolicy
    minute_remaining: int
    hour_remaining: int
    searches_remaining: int
    utilization_pct: Decimal


def get_policy(tier: str) -> TierPolicy:
    """Get rate limit policy for a tier."""
    return TIER_POLICIES.get(tier, TIER_POLICIES["free"])


def check_limit(
    tier: str,
    requests_this_minute: int = 0,
    requests_this_hour: int = 0,
    searches_today: int = 0,
) -> dict:
    """Check if a request is within limits.

    Returns dict with 'allowed' bool and 'reason' if blocked.
    """
    policy = get_policy(tier)

    if requests_this_minute >= policy.requests_per_minute:
        return {
            "allowed": False,
            "reason": f"Rate limit exceeded: {policy.requests_per_minute}/minute for {tier} tier",
            "retry_after_seconds": 60,
        }

    if requests_this_hour >= policy.requests_per_hour:
        return {
            "allowed": False,
            "reason": f"Hourly limit exceeded: {policy.requests_per_hour}/hour for {tier} tier",
            "retry_after_seconds": 3600,
        }

    if searches_today >= policy.daily_searches:
        return {
            "allowed": False,
            "reason": f"Daily search limit exceeded: {policy.daily_searches}/day for {tier} tier",
            "upgrade_url": "/api/billing/subscribe",
        }

    return {"allowed": True}


def usage_snapshot(
    user_id: str,
    tier: str,
    requests_this_minute: int = 0,
    requests_this_hour: int = 0,
    searches_today: int = 0,
) -> UsageSnapshot:
    """Build a usage snapshot for API response."""
    policy = get_policy(tier)
    minute_rem = max(0, policy.requests_per_minute - requests_this_minute)
    hour_rem = max(0, policy.requests_per_hour - requests_this_hour)
    search_rem = max(0, policy.daily_searches - searches_today)

    # Utilization: highest ratio across all dimensions
    ratios = []
    if policy.requests_per_minute > 0:
        ratios.append(Decimal(requests_this_minute) / Decimal(policy.requests_per_minute))
    if policy.requests_per_hour > 0:
        ratios.append(Decimal(requests_this_hour) / Decimal(policy.requests_per_hour))
    if policy.daily_searches > 0:
        ratios.append(Decimal(searches_today) / Decimal(policy.daily_searches))

    utilization = (max(ratios) * 100).quantize(Decimal("0.1")) if ratios else Decimal("0")

    return UsageSnapshot(
        user_id=user_id,
        tier=tier,
        requests_this_minute=requests_this_minute,
        requests_this_hour=requests_this_hour,
        searches_today=searches_today,
        policy=policy,
        minute_remaining=minute_rem,
        hour_remaining=hour_rem,
        searches_remaining=search_rem,
        utilization_pct=utilization,
    )
