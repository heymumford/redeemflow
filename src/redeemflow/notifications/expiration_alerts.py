"""Expiration alerts — bridge portfolio expiration tracking to notification delivery.

Beck: Pure function — expiration data in, actionable alerts out.
Fowler: Anti-corruption layer between portfolio and notification domains.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from redeemflow.notifications.models import AlertPriority
from redeemflow.portfolio.expiration import (
    EXPIRATION_POLICIES,
    ExpirationPolicy,
    ExpirationTracker,
)
from redeemflow.portfolio.models import PointBalance


@dataclass(frozen=True)
class ExpirationNotification:
    """A user-facing notification about expiring points."""

    notification_id: str
    program_code: str
    points_at_risk: int
    estimated_value: Decimal
    days_remaining: int
    priority: AlertPriority
    title: str
    message: str
    actions: list[str]
    created_at: str


@dataclass(frozen=True)
class ExpirationSummary:
    """Aggregated expiration risk across a portfolio."""

    total_programs_at_risk: int
    total_points_at_risk: int
    total_value_at_risk: Decimal
    critical_count: int  # <= 30 days
    warning_count: int  # <= 60 days
    watch_count: int  # <= 90 days
    notifications: list[ExpirationNotification]
    highest_priority: AlertPriority


def _priority_from_days(days: int) -> AlertPriority:
    """Map days remaining to alert priority."""
    if days <= 30:
        return AlertPriority.CRITICAL
    if days <= 60:
        return AlertPriority.HIGH
    if days <= 90:
        return AlertPriority.MEDIUM
    return AlertPriority.LOW


def _suggested_actions(program_code: str, days: int, points: int) -> list[str]:
    """Generate actionable suggestions based on urgency."""
    actions = []
    if days <= 30:
        actions.append(f"URGENT: Use or transfer {points:,} {program_code} points immediately")
        actions.append("Consider a points redemption at any value to avoid total loss")
    elif days <= 60:
        actions.append(f"Plan to use {points:,} {program_code} points within {days} days")
        actions.append("Check for transfer partner bonuses to maximize value")
    else:
        actions.append(f"Monitor {program_code} — {days} days until expiration risk")
        actions.append("Any earning or redemption activity resets the clock")
    actions.append("Make a small purchase or earn transaction to reset inactivity timer")
    return actions


def _estimate_value(points: int, program_code: str) -> Decimal:
    """Estimate dollar value of points at risk using baseline CPP."""
    # Conservative CPP estimates by program type
    cpp_map: dict[str, Decimal] = {
        "united": Decimal("1.3"),
        "american": Decimal("1.4"),
        "delta": Decimal("1.2"),
        "southwest": Decimal("1.4"),
        "alaska": Decimal("1.5"),
        "jetblue": Decimal("1.3"),
        "british-airways": Decimal("1.2"),
        "virgin-atlantic": Decimal("1.4"),
        "air-france-klm": Decimal("1.2"),
        "singapore": Decimal("1.5"),
        "turkish": Decimal("1.5"),
        "ana": Decimal("1.5"),
        "hyatt": Decimal("1.7"),
        "marriott": Decimal("0.7"),
        "hilton": Decimal("0.5"),
        "ihg": Decimal("0.5"),
    }
    cpp = cpp_map.get(program_code, Decimal("1.0"))
    return (Decimal(str(points)) * cpp / Decimal("100")).quantize(Decimal("0.01"))


def check_portfolio_expirations(
    balances: list[PointBalance],
    policies: list[ExpirationPolicy] | None = None,
) -> ExpirationSummary:
    """Check all portfolio balances for expiration risk.

    Returns a summary with prioritized notifications and suggested actions.
    """
    if policies is None:
        policies = EXPIRATION_POLICIES

    tracker = ExpirationTracker()
    raw_alerts = tracker.check_expirations(balances, policies)

    notifications: list[ExpirationNotification] = []
    counter = 0
    critical = 0
    warning = 0
    watch = 0
    total_points = 0
    total_value = Decimal("0")

    for alert in raw_alerts:
        counter += 1
        priority = _priority_from_days(alert.days_until_expiry)
        value = _estimate_value(alert.points_at_risk, alert.program_code)
        actions = _suggested_actions(alert.program_code, alert.days_until_expiry, alert.points_at_risk)

        if alert.days_until_expiry <= 30:
            critical += 1
        elif alert.days_until_expiry <= 60:
            warning += 1
        else:
            watch += 1

        total_points += alert.points_at_risk
        total_value += value

        notifications.append(
            ExpirationNotification(
                notification_id=f"exp-{counter}",
                program_code=alert.program_code,
                points_at_risk=alert.points_at_risk,
                estimated_value=value,
                days_remaining=alert.days_until_expiry,
                priority=priority,
                title=(
                    f"{alert.program_code}: {alert.points_at_risk:,} points expiring in ~{alert.days_until_expiry} days"
                ),
                message=(
                    f"Your {alert.points_at_risk:,} {alert.program_code} points "
                    f"(~${value}) are at risk of expiration due to inactivity. "
                    f"Estimated {alert.days_until_expiry} days remaining."
                ),
                actions=actions,
                created_at=datetime.now(UTC).isoformat(),
            )
        )

    # Sort by priority (critical first)
    priority_order = {
        AlertPriority.CRITICAL: 0,
        AlertPriority.HIGH: 1,
        AlertPriority.MEDIUM: 2,
        AlertPriority.LOW: 3,
    }
    notifications.sort(key=lambda n: priority_order.get(n.priority, 99))

    highest = AlertPriority.LOW
    if critical > 0:
        highest = AlertPriority.CRITICAL
    elif warning > 0:
        highest = AlertPriority.HIGH
    elif watch > 0:
        highest = AlertPriority.MEDIUM

    return ExpirationSummary(
        total_programs_at_risk=len(notifications),
        total_points_at_risk=total_points,
        total_value_at_risk=total_value,
        critical_count=critical,
        warning_count=warning,
        watch_count=watch,
        notifications=notifications,
        highest_priority=highest,
    )
