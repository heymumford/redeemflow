"""Points expiration calendar — timeline views and date-based alerts.

Builds on ExpirationTracker to provide calendar events, timeline data,
and urgency-classified summaries for UI consumption.

Beck: Composition over inheritance — calendar wraps tracker, doesn't extend it.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from redeemflow.portfolio.expiration import ExpirationPolicy, ExpirationTracker
from redeemflow.portfolio.models import PointBalance


class ExpirationUrgency(str, Enum):
    EXPIRED = "expired"
    CRITICAL = "critical"  # <=30 days
    WARNING = "warning"  # 31-90 days
    UPCOMING = "upcoming"  # 91-180 days
    SAFE = "safe"  # >180 days
    NEVER = "never"  # No expiration


@dataclass(frozen=True)
class CalendarEvent:
    """A date-anchored event for the expiration timeline."""

    program_code: str
    program_name: str
    event_type: str  # "expiration", "30d_warning", "60d_warning", "90d_warning"
    days_remaining: int
    points_at_risk: int
    value_at_risk: Decimal
    urgency: ExpirationUrgency
    description: str
    action: str


@dataclass(frozen=True)
class CalendarSummary:
    """Aggregated expiration calendar data."""

    total_programs: int
    programs_with_expiry: int
    programs_safe: int
    critical_count: int
    warning_count: int
    total_points_at_risk: int
    total_value_at_risk: Decimal
    events: list[CalendarEvent]
    next_event: CalendarEvent | None


def _classify_urgency(days: int) -> ExpirationUrgency:
    if days < 0:
        return ExpirationUrgency.EXPIRED
    if days <= 30:
        return ExpirationUrgency.CRITICAL
    if days <= 90:
        return ExpirationUrgency.WARNING
    if days <= 180:
        return ExpirationUrgency.UPCOMING
    return ExpirationUrgency.SAFE


def _action_text(urgency: ExpirationUrgency) -> str:
    return {
        ExpirationUrgency.EXPIRED: "Contact program about reinstatement options",
        ExpirationUrgency.CRITICAL: "Redeem or transfer points immediately",
        ExpirationUrgency.WARNING: "Plan a redemption or qualifying activity",
        ExpirationUrgency.UPCOMING: "Monitor and consider a small transaction to reset",
        ExpirationUrgency.SAFE: "No immediate action needed",
        ExpirationUrgency.NEVER: "Points do not expire",
    }[urgency]


def _program_name_from_code(code: str) -> str:
    """Simple code-to-name mapping."""
    names = {
        "chase-ur": "Chase Ultimate Rewards",
        "amex-mr": "Amex Membership Rewards",
        "citi-ty": "Citi ThankYou",
        "capital-one": "Capital One Miles",
        "bilt": "Bilt Rewards",
        "wells-fargo": "Wells Fargo Rewards",
        "united": "United MileagePlus",
        "delta": "Delta SkyMiles",
        "american": "American AAdvantage",
        "southwest": "Southwest Rapid Rewards",
        "alaska": "Alaska Mileage Plan",
        "jetblue": "JetBlue TrueBlue",
        "british-airways": "British Airways Avios",
        "virgin-atlantic": "Virgin Atlantic Flying Club",
        "air-france-klm": "Air France/KLM Flying Blue",
        "singapore": "Singapore KrisFlyer",
        "turkish": "Turkish Miles&Smiles",
        "ana": "ANA Mileage Club",
        "air-canada": "Air Canada Aeroplan",
        "hyatt": "World of Hyatt",
        "marriott": "Marriott Bonvoy",
        "hilton": "Hilton Honors",
        "ihg": "IHG One Rewards",
    }
    return names.get(code, code.replace("-", " ").title())


def build_calendar(
    balances: list[PointBalance],
    policies: list[ExpirationPolicy],
    cpp_values: dict[str, Decimal] | None = None,
) -> CalendarSummary:
    """Build expiration calendar from balances and policies."""
    tracker = ExpirationTracker()
    alerts = tracker.check_expirations(balances, policies)

    cpp = cpp_values or {}
    policy_map = {p.program_code: p for p in policies}
    alert_map = {a.program_code: a for a in alerts}
    events: list[CalendarEvent] = []

    programs_with_expiry = 0
    programs_safe = 0

    for balance in balances:
        if balance.points == 0:
            continue

        policy = policy_map.get(balance.program_code)
        program_name = _program_name_from_code(balance.program_code)
        point_cpp = cpp.get(balance.program_code, Decimal("1.0"))
        value = (Decimal(str(balance.points)) * point_cpp / 100).quantize(Decimal("0.01"))

        alert = alert_map.get(balance.program_code)

        if policy is None or not policy.expires:
            programs_safe += 1
            events.append(
                CalendarEvent(
                    program_code=balance.program_code,
                    program_name=program_name,
                    event_type="no_expiry",
                    days_remaining=999,
                    points_at_risk=0,
                    value_at_risk=Decimal("0"),
                    urgency=ExpirationUrgency.NEVER,
                    description=f"{program_name}: Points do not expire",
                    action=_action_text(ExpirationUrgency.NEVER),
                )
            )
            continue

        programs_with_expiry += 1
        days = alert.days_until_expiry if alert else 365
        urgency = _classify_urgency(days)

        events.append(
            CalendarEvent(
                program_code=balance.program_code,
                program_name=program_name,
                event_type="expiration",
                days_remaining=days,
                points_at_risk=balance.points,
                value_at_risk=value,
                urgency=urgency,
                description=f"{program_name}: {balance.points:,} points — {days} days remaining",
                action=_action_text(urgency),
            )
        )

    # Sort by days remaining (most urgent first)
    events.sort(key=lambda e: e.days_remaining)

    critical = [e for e in events if e.urgency == ExpirationUrgency.CRITICAL]
    warning = [e for e in events if e.urgency == ExpirationUrgency.WARNING]
    at_risk = critical + warning
    next_event = events[0] if events and events[0].urgency != ExpirationUrgency.NEVER else None

    return CalendarSummary(
        total_programs=len([b for b in balances if b.points > 0]),
        programs_with_expiry=programs_with_expiry,
        programs_safe=programs_safe,
        critical_count=len(critical),
        warning_count=len(warning),
        total_points_at_risk=sum(e.points_at_risk for e in at_risk),
        total_value_at_risk=sum((e.value_at_risk for e in at_risk), Decimal("0")),
        events=events,
        next_event=next_event,
    )
