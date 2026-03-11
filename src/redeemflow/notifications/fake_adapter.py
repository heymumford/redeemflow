"""Notifications domain — fake adapter for testing.

In-memory AlertPort implementation with deterministic behavior.
Zero network calls. Tracks sent alerts for verification.
"""

from __future__ import annotations

from redeemflow.notifications.models import Alert, AlertType
from redeemflow.notifications.ports import AlertPreferences

_DEFAULT_PREFERENCES = AlertPreferences(
    user_id="default",
    enabled_types=frozenset(AlertType),
    email_enabled=True,
    push_enabled=False,
)


class FakeAlertAdapter:
    """In-memory alert adapter for testing."""

    def __init__(self, simulate_error: str | None = None) -> None:
        self._simulate_error = simulate_error
        self._sent_alerts: list[tuple[str, Alert]] = []
        self._preferences: dict[str, AlertPreferences] = {}

    def send_alert(self, user_id: str, alert: Alert) -> bool:
        if self._simulate_error == "delivery_failed":
            return False
        self._sent_alerts.append((user_id, alert))
        return True

    def get_preferences(self, user_id: str) -> AlertPreferences:
        if user_id in self._preferences:
            return self._preferences[user_id]
        return AlertPreferences(
            user_id=user_id,
            enabled_types=frozenset(AlertType),
            email_enabled=True,
            push_enabled=False,
        )

    def set_preferences(self, prefs: AlertPreferences) -> None:
        """Test helper: set preferences for a user."""
        self._preferences[prefs.user_id] = prefs

    @property
    def sent_alerts(self) -> list[tuple[str, Alert]]:
        """Test inspection: all alerts sent."""
        return list(self._sent_alerts)

    @property
    def alert_count(self) -> int:
        """Number of alerts sent (test inspection)."""
        return len(self._sent_alerts)
