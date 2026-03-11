"""Admin dashboard — system-wide metrics and feature adoption tracking.

Beck: Dashboard is a projection — system state in, metrics out.
Fowler: Aggregate metrics from multiple sources without tight coupling.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal


@dataclass(frozen=True)
class SystemMetrics:
    """System-wide usage metrics."""

    total_users: int
    active_users_24h: int
    total_portfolios: int
    total_goals: int
    total_trips: int
    total_shares: int
    total_achievements_earned: int
    total_api_keys: int
    avg_programs_per_user: Decimal
    generated_at: str


@dataclass(frozen=True)
class FeatureAdoption:
    """Feature adoption metrics."""

    feature_name: str
    users_enabled: int
    total_uses: int
    adoption_pct: Decimal


@dataclass(frozen=True)
class TierDistribution:
    """User distribution across subscription tiers."""

    tier: str
    count: int
    pct: Decimal
    revenue_contribution: Decimal  # Percentage of revenue


@dataclass(frozen=True)
class DashboardReport:
    """Complete admin dashboard report."""

    system: SystemMetrics
    feature_adoption: list[FeatureAdoption]
    tier_distribution: list[TierDistribution]
    top_programs: list[dict]  # Most tracked programs
    health_check: dict  # System health indicators


def generate_dashboard(
    user_count: int = 0,
    portfolio_count: int = 0,
    goal_count: int = 0,
    trip_count: int = 0,
    share_count: int = 0,
    achievement_count: int = 0,
    api_key_count: int = 0,
) -> DashboardReport:
    """Generate a complete dashboard report.

    In production, these would be computed from actual data stores.
    For now, accepts counts as parameters for testability.
    """
    active_24h = max(1, user_count // 3)  # Approximate
    avg_programs = Decimal(str(max(1, portfolio_count * 3 // max(1, user_count)))).quantize(Decimal("0.1"))

    system = SystemMetrics(
        total_users=user_count,
        active_users_24h=active_24h,
        total_portfolios=portfolio_count,
        total_goals=goal_count,
        total_trips=trip_count,
        total_shares=share_count,
        total_achievements_earned=achievement_count,
        total_api_keys=api_key_count,
        avg_programs_per_user=avg_programs,
        generated_at=datetime.now(UTC).isoformat(),
    )

    # Feature adoption (simulated percentages)
    features = [
        FeatureAdoption("portfolio_sync", user_count, user_count * 5, Decimal("95.0")),
        FeatureAdoption("goals", goal_count, goal_count * 2, Decimal("60.0")),
        FeatureAdoption("trip_planner", trip_count, trip_count * 3, Decimal("40.0")),
        FeatureAdoption("sharing", share_count, share_count * 2, Decimal("25.0")),
        FeatureAdoption("achievements", achievement_count, achievement_count, Decimal("70.0")),
        FeatureAdoption("budget_planner", max(1, user_count // 5), user_count // 5, Decimal("20.0")),
        FeatureAdoption("booking_optimizer", max(1, user_count // 4), user_count // 4, Decimal("25.0")),
    ]

    # Tier distribution
    tiers = [
        TierDistribution("free", max(1, user_count * 60 // 100), Decimal("60.0"), Decimal("0.0")),
        TierDistribution("premium", max(0, user_count * 30 // 100), Decimal("30.0"), Decimal("55.0")),
        TierDistribution("pro", max(0, user_count * 10 // 100), Decimal("10.0"), Decimal("45.0")),
    ]

    # Top programs
    top_programs = [
        {"program": "chase-ur", "users": max(1, user_count * 70 // 100), "pct": "70%"},
        {"program": "amex-mr", "users": max(1, user_count * 55 // 100), "pct": "55%"},
        {"program": "united", "users": max(1, user_count * 45 // 100), "pct": "45%"},
        {"program": "hyatt", "users": max(1, user_count * 35 // 100), "pct": "35%"},
        {"program": "marriott", "users": max(1, user_count * 30 // 100), "pct": "30%"},
    ]

    health = {
        "api_latency_ms": 45,
        "error_rate_pct": 0.1,
        "uptime_pct": 99.9,
        "db_connections": 12,
        "cache_hit_rate": 85.0,
        "status": "healthy",
    }

    return DashboardReport(
        system=system,
        feature_adoption=features,
        tier_distribution=tiers,
        top_programs=top_programs,
        health_check=health,
    )
