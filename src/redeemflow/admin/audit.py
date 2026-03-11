"""Audit log — immutable record of user actions for compliance.

Beck: Append-only log. No mutations, no deletions.
Fowler: Event Sourcing lite — actions are facts, not state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC
from enum import Enum


class AuditAction(str, Enum):
    """Categorized action types for audit trail."""

    # Portfolio
    PORTFOLIO_VIEW = "portfolio.view"
    PORTFOLIO_SYNC = "portfolio.sync"

    # Goals
    GOAL_CREATE = "goal.create"
    GOAL_UPDATE = "goal.update"

    # Trips
    TRIP_CREATE = "trip.create"
    TRIP_VIEW = "trip.view"

    # Billing
    SUBSCRIPTION_CREATE = "subscription.create"
    SUBSCRIPTION_CANCEL = "subscription.cancel"
    WEBHOOK_RECEIVED = "webhook.received"

    # Household
    HOUSEHOLD_MEMBER_ADD = "household.member_add"
    HOUSEHOLD_MEMBER_REMOVE = "household.member_remove"

    # Search
    AWARD_SEARCH = "search.award"
    CONFERENCE_PLAN = "search.conference_plan"

    # Admin
    ADMIN_METRICS_VIEW = "admin.metrics_view"

    # Donations
    DONATION_CREATE = "donation.create"

    # Auth
    AUTH_LOGIN = "auth.login"
    AUTH_FAILURE = "auth.failure"


@dataclass(frozen=True)
class AuditEntry:
    """A single audit record — immutable fact about what happened."""

    entry_id: str
    timestamp: str
    user_id: str
    action: AuditAction
    resource_type: str  # e.g. "goal", "trip", "subscription"
    resource_id: str  # e.g. "goal_1", "trip_3"
    detail: str = ""
    ip_address: str = ""
    user_agent: str = ""


@dataclass(frozen=True)
class AuditSummary:
    """Aggregate view of audit log."""

    total_entries: int
    unique_users: int
    action_counts: dict[str, int]
    recent_entries: list[AuditEntry]


@dataclass
class AuditLog:
    """Append-only audit log. Thread-safe for single-process use."""

    _entries: list[AuditEntry] = field(default_factory=list)
    _counter: int = 0

    def record(
        self,
        user_id: str,
        action: AuditAction,
        resource_type: str,
        resource_id: str,
        detail: str = "",
        ip_address: str = "",
        user_agent: str = "",
        timestamp: str = "",
    ) -> AuditEntry:
        """Append an audit entry. Returns the created entry."""
        from datetime import datetime

        self._counter += 1
        entry = AuditEntry(
            entry_id=f"audit_{self._counter}",
            timestamp=timestamp or datetime.now(UTC).isoformat(),
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            detail=detail,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self._entries.append(entry)
        return entry

    def query(
        self,
        user_id: str | None = None,
        action: AuditAction | None = None,
        resource_type: str | None = None,
        limit: int = 50,
    ) -> list[AuditEntry]:
        """Query audit entries with optional filters."""
        results = self._entries
        if user_id:
            results = [e for e in results if e.user_id == user_id]
        if action:
            results = [e for e in results if e.action == action]
        if resource_type:
            results = [e for e in results if e.resource_type == resource_type]
        # Most recent first
        return list(reversed(results[-limit:]))

    def summarize(self, limit: int = 20) -> AuditSummary:
        """Compute aggregate summary of audit log."""
        action_counts: dict[str, int] = {}
        users: set[str] = set()
        for e in self._entries:
            action_counts[e.action.value] = action_counts.get(e.action.value, 0) + 1
            users.add(e.user_id)

        recent = list(reversed(self._entries[-limit:]))
        return AuditSummary(
            total_entries=len(self._entries),
            unique_users=len(users),
            action_counts=action_counts,
            recent_entries=recent,
        )

    @property
    def size(self) -> int:
        return len(self._entries)


# Singleton audit log — shared across the application
_AUDIT_LOG = AuditLog()


def get_audit_log() -> AuditLog:
    """Get the global audit log instance."""
    return _AUDIT_LOG


def reset_audit_log() -> None:
    """Reset for testing only."""
    global _AUDIT_LOG
    _AUDIT_LOG = AuditLog()
