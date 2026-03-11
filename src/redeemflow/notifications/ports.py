"""Notifications domain — ports (Protocol interfaces).

AlertPort defines the contract for sending alerts and managing user preferences.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from redeemflow.notifications.models import Alert, AlertType


@dataclass(frozen=True)
class AlertPreferences:
    """User preferences for alert delivery."""

    user_id: str
    enabled_types: frozenset[AlertType] = field(default_factory=lambda: frozenset(AlertType))
    email_enabled: bool = True
    push_enabled: bool = False
    quiet_hours_start: int | None = None  # 0-23 hour
    quiet_hours_end: int | None = None


@runtime_checkable
class AlertPort(Protocol):
    """Port for sending alerts and managing alert preferences."""

    def send_alert(self, user_id: str, alert: Alert) -> bool: ...

    def get_preferences(self, user_id: str) -> AlertPreferences: ...
