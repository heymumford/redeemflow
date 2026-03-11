"""Notification preferences — user-configurable alert delivery channels.

Fowler: Separate configuration from mechanism.
Beck: Explicit is better than implicit — every channel has a toggle.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class NotificationChannel(str, Enum):
    EMAIL = "email"
    PUSH = "push"
    SMS = "sms"
    IN_APP = "in_app"


class NotificationFrequency(str, Enum):
    IMMEDIATE = "immediate"
    DAILY_DIGEST = "daily_digest"
    WEEKLY_DIGEST = "weekly_digest"


@dataclass
class ChannelPreference:
    """Per-channel notification preference."""

    channel: NotificationChannel
    enabled: bool = True
    frequency: NotificationFrequency = NotificationFrequency.IMMEDIATE


@dataclass
class AlertTypePreference:
    """Per-alert-type preference — which channels to use."""

    alert_type: str
    channels: list[NotificationChannel] = field(default_factory=lambda: [NotificationChannel.IN_APP])
    muted: bool = False


@dataclass
class NotificationPreferences:
    """Complete notification preferences for a user."""

    user_id: str
    channels: dict[str, ChannelPreference] = field(default_factory=dict)
    alert_preferences: dict[str, AlertTypePreference] = field(default_factory=dict)
    quiet_hours_start: str | None = None  # "22:00"
    quiet_hours_end: str | None = None  # "07:00"
    timezone: str = "UTC"

    def __post_init__(self) -> None:
        if not self.channels:
            self.channels = {
                "email": ChannelPreference(channel=NotificationChannel.EMAIL, enabled=True),
                "push": ChannelPreference(channel=NotificationChannel.PUSH, enabled=True),
                "in_app": ChannelPreference(channel=NotificationChannel.IN_APP, enabled=True),
            }


def default_preferences(user_id: str) -> NotificationPreferences:
    """Create default notification preferences for a new user."""
    return NotificationPreferences(
        user_id=user_id,
        channels={
            "email": ChannelPreference(
                channel=NotificationChannel.EMAIL,
                enabled=True,
                frequency=NotificationFrequency.DAILY_DIGEST,
            ),
            "push": ChannelPreference(
                channel=NotificationChannel.PUSH,
                enabled=True,
                frequency=NotificationFrequency.IMMEDIATE,
            ),
            "in_app": ChannelPreference(
                channel=NotificationChannel.IN_APP,
                enabled=True,
                frequency=NotificationFrequency.IMMEDIATE,
            ),
        },
        alert_preferences={
            "devaluation": AlertTypePreference(
                alert_type="devaluation",
                channels=[NotificationChannel.EMAIL, NotificationChannel.PUSH, NotificationChannel.IN_APP],
            ),
            "transfer_bonus": AlertTypePreference(
                alert_type="transfer_bonus",
                channels=[NotificationChannel.EMAIL, NotificationChannel.IN_APP],
            ),
            "expiration": AlertTypePreference(
                alert_type="expiration",
                channels=[NotificationChannel.EMAIL, NotificationChannel.PUSH, NotificationChannel.IN_APP],
            ),
            "sweet_spot": AlertTypePreference(
                alert_type="sweet_spot",
                channels=[NotificationChannel.IN_APP],
            ),
            "price_drop": AlertTypePreference(
                alert_type="price_drop",
                channels=[NotificationChannel.IN_APP],
            ),
        },
    )


def should_notify(
    preferences: NotificationPreferences,
    alert_type: str,
    channel: NotificationChannel,
) -> bool:
    """Determine if a notification should be sent for this alert type on this channel."""
    # Check if channel is globally enabled
    channel_pref = preferences.channels.get(channel.value)
    if channel_pref is None or not channel_pref.enabled:
        return False

    # Check alert-type-specific preferences
    alert_pref = preferences.alert_preferences.get(alert_type)
    if alert_pref is None:
        # Default: in-app only for unknown alert types
        return channel == NotificationChannel.IN_APP

    if alert_pref.muted:
        return False

    return channel in alert_pref.channels


def update_alert_preference(
    preferences: NotificationPreferences,
    alert_type: str,
    channels: list[NotificationChannel] | None = None,
    muted: bool | None = None,
) -> AlertTypePreference:
    """Update preferences for a specific alert type."""
    current = preferences.alert_preferences.get(
        alert_type,
        AlertTypePreference(alert_type=alert_type),
    )
    updated = AlertTypePreference(
        alert_type=alert_type,
        channels=channels if channels is not None else current.channels,
        muted=muted if muted is not None else current.muted,
    )
    preferences.alert_preferences[alert_type] = updated
    return updated


def preferences_summary(preferences: NotificationPreferences) -> dict:
    """Summarize notification preferences."""
    enabled_channels = [name for name, cp in preferences.channels.items() if cp.enabled]
    muted_alerts = [name for name, ap in preferences.alert_preferences.items() if ap.muted]
    return {
        "user_id": preferences.user_id,
        "enabled_channels": enabled_channels,
        "muted_alert_types": muted_alerts,
        "total_alert_types": len(preferences.alert_preferences),
        "quiet_hours": (
            f"{preferences.quiet_hours_start}-{preferences.quiet_hours_end}" if preferences.quiet_hours_start else ""
        ),
        "timezone": preferences.timezone,
    }


# In-memory store
_NOTIFICATION_PREFS: dict[str, NotificationPreferences] = {}


def get_notification_prefs(user_id: str) -> NotificationPreferences:
    """Get or create notification preferences for a user."""
    if user_id not in _NOTIFICATION_PREFS:
        _NOTIFICATION_PREFS[user_id] = default_preferences(user_id)
    return _NOTIFICATION_PREFS[user_id]


def reset_notification_prefs() -> None:
    """Reset store — testing only."""
    _NOTIFICATION_PREFS.clear()
