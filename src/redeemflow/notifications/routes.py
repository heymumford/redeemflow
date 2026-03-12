"""Notification preferences API."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from redeemflow.identity.auth import get_current_user
from redeemflow.identity.models import User
from redeemflow.notifications.expiration_alerts import check_portfolio_expirations
from redeemflow.notifications.preferences import (
    NotificationChannel,
    NotificationFrequency,
    get_notification_prefs,
    should_notify,
    update_alert_preference,
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
    prefs = get_notification_prefs(user.id)
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
    prefs = get_notification_prefs(user.id)

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


class ChannelToggle(BaseModel):
    enabled: bool


class AlertToggle(BaseModel):
    muted: bool = False
    channels: list[str] | None = None


@router.put("/api/notifications/preferences/channel/{channel_name}")
def update_channel(channel_name: str, body: ChannelToggle, user: User = Depends(get_current_user)):
    """Enable/disable a notification channel."""
    prefs = get_notification_prefs(user.id)
    if channel_name not in prefs.channels:
        return JSONResponse(status_code=400, content={"detail": f"Unknown channel: {channel_name}"})
    prefs.channels[channel_name].enabled = body.enabled
    cp = prefs.channels[channel_name]
    return {
        "channel": {
            "name": channel_name,
            "enabled": cp.enabled,
            "frequency": cp.frequency.value,
        }
    }


@router.put("/api/notifications/preferences/alert/{alert_type}")
def update_alert(alert_type: str, body: AlertToggle, user: User = Depends(get_current_user)):
    """Update preferences for a specific alert type."""
    prefs = get_notification_prefs(user.id)
    channels = None
    if body.channels is not None:
        channels = []
        for ch in body.channels:
            try:
                channels.append(NotificationChannel(ch))
            except ValueError:
                pass
    updated = update_alert_preference(prefs, alert_type, channels=channels, muted=body.muted)
    return {
        "alert": {
            "alert_type": updated.alert_type,
            "channels": [c.value for c in updated.channels],
            "muted": updated.muted,
        }
    }


@router.get("/api/notifications/expiration-alerts")
def expiration_alerts(user: User = Depends(get_current_user)):
    """Get expiration alerts for the user's portfolio."""
    from redeemflow.portfolio.awardwallet import FakeAwardWalletAdapter

    fetcher = FakeAwardWalletAdapter()
    balances = fetcher.fetch_balances(user.id)
    summary = check_portfolio_expirations(balances)
    return {
        "total_programs_at_risk": summary.total_programs_at_risk,
        "total_points_at_risk": summary.total_points_at_risk,
        "total_value_at_risk": str(summary.total_value_at_risk),
        "critical_count": summary.critical_count,
        "warning_count": summary.warning_count,
        "watch_count": summary.watch_count,
        "highest_priority": summary.highest_priority.value,
        "notifications": [
            {
                "notification_id": n.notification_id,
                "program_code": n.program_code,
                "points_at_risk": n.points_at_risk,
                "estimated_value": str(n.estimated_value),
                "days_remaining": n.days_remaining,
                "priority": n.priority.value,
                "title": n.title,
                "message": n.message,
                "actions": n.actions,
            }
            for n in summary.notifications
        ],
    }


@router.get("/api/notifications/check/{alert_type}/{channel}")
def check_notification(alert_type: str, channel: str, user: User = Depends(get_current_user)):
    """Check if a notification should be sent for this alert type on this channel."""
    prefs = get_notification_prefs(user.id)
    try:
        ch = NotificationChannel(channel)
    except ValueError:
        return JSONResponse(status_code=404, content={"detail": f"Unknown channel: {channel}"})

    result = should_notify(prefs, alert_type, ch)
    return {
        "alert_type": alert_type,
        "channel": channel,
        "should_notify": result,
    }
