"""Notification preferences API."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from redeemflow.identity.auth import get_current_user
from redeemflow.identity.models import User
from redeemflow.notifications.preferences import (
    NotificationChannel,
    NotificationFrequency,
    default_preferences,
    should_notify,
)

router = APIRouter()

# In-memory store for preferences (replaced by DB in production)
_PREFERENCES: dict[str, dict] = {}


class ChannelUpdate(BaseModel):
    channel: str
    enabled: bool
    frequency: str = "immediate"


class AlertPreferenceUpdate(BaseModel):
    alert_type: str
    channels: list[str]
    muted: bool = False


class PreferencesUpdate(BaseModel):
    channels: list[ChannelUpdate] | None = None
    alert_preferences: list[AlertPreferenceUpdate] | None = None
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    timezone: str | None = None


@router.get("/api/notifications/preferences")
def get_preferences(user: User = Depends(get_current_user)):
    """Get user's notification preferences."""
    prefs = default_preferences(user.id)
    return {
        "user_id": prefs.user_id,
        "channels": {
            name: {
                "channel": cp.channel.value,
                "enabled": cp.enabled,
                "frequency": cp.frequency.value,
            }
            for name, cp in prefs.channels.items()
        },
        "alert_preferences": {
            name: {
                "alert_type": ap.alert_type,
                "channels": [c.value for c in ap.channels],
                "muted": ap.muted,
            }
            for name, ap in prefs.alert_preferences.items()
        },
        "quiet_hours_start": prefs.quiet_hours_start,
        "quiet_hours_end": prefs.quiet_hours_end,
        "timezone": prefs.timezone,
    }


@router.post("/api/notifications/preferences")
def update_preferences(update: PreferencesUpdate, user: User = Depends(get_current_user)):
    """Update user's notification preferences."""
    prefs = default_preferences(user.id)

    if update.channels:
        for ch in update.channels:
            if ch.channel in prefs.channels:
                prefs.channels[ch.channel].enabled = ch.enabled
                try:
                    prefs.channels[ch.channel].frequency = NotificationFrequency(ch.frequency)
                except ValueError:
                    pass

    if update.quiet_hours_start is not None:
        prefs.quiet_hours_start = update.quiet_hours_start
    if update.quiet_hours_end is not None:
        prefs.quiet_hours_end = update.quiet_hours_end
    if update.timezone is not None:
        prefs.timezone = update.timezone

    return {"status": "updated", "user_id": user.id}


@router.get("/api/notifications/check/{alert_type}/{channel}")
def check_notification(alert_type: str, channel: str, user: User = Depends(get_current_user)):
    """Check if a notification should be sent for this alert type on this channel."""
    prefs = default_preferences(user.id)
    try:
        ch = NotificationChannel(channel)
    except ValueError:
        return {"error": f"Unknown channel: {channel}"}

    result = should_notify(prefs, alert_type, ch)
    return {
        "alert_type": alert_type,
        "channel": channel,
        "should_notify": result,
    }
