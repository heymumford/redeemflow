"""Tests for notification preferences."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from redeemflow.notifications.preferences import (
    NotificationChannel,
    NotificationFrequency,
    default_preferences,
    get_notification_prefs,
    preferences_summary,
    should_notify,
    update_alert_preference,
)


class TestDefaultPreferences:
    def test_creates_with_all_channels(self):
        prefs = default_preferences("user1")
        assert "email" in prefs.channels
        assert "push" in prefs.channels
        assert "in_app" in prefs.channels

    def test_email_is_daily_digest(self):
        prefs = default_preferences("user1")
        assert prefs.channels["email"].frequency == NotificationFrequency.DAILY_DIGEST

    def test_push_is_immediate(self):
        prefs = default_preferences("user1")
        assert prefs.channels["push"].frequency == NotificationFrequency.IMMEDIATE

    def test_default_alert_types(self):
        prefs = default_preferences("user1")
        assert "devaluation" in prefs.alert_preferences
        assert "expiration" in prefs.alert_preferences
        assert "sweet_spot" in prefs.alert_preferences


class TestShouldNotify:
    def test_enabled_channel_and_alert(self):
        prefs = default_preferences("user1")
        assert should_notify(prefs, "devaluation", NotificationChannel.EMAIL) is True

    def test_disabled_channel(self):
        prefs = default_preferences("user1")
        prefs.channels["email"].enabled = False
        assert should_notify(prefs, "devaluation", NotificationChannel.EMAIL) is False

    def test_muted_alert(self):
        prefs = default_preferences("user1")
        prefs.alert_preferences["devaluation"].muted = True
        assert should_notify(prefs, "devaluation", NotificationChannel.EMAIL) is False

    def test_unknown_alert_type_defaults_in_app(self):
        prefs = default_preferences("user1")
        assert should_notify(prefs, "unknown_type", NotificationChannel.IN_APP) is True
        assert should_notify(prefs, "unknown_type", NotificationChannel.EMAIL) is False

    def test_channel_not_in_alert_prefs(self):
        prefs = default_preferences("user1")
        # sweet_spot only has IN_APP
        assert should_notify(prefs, "sweet_spot", NotificationChannel.EMAIL) is False
        assert should_notify(prefs, "sweet_spot", NotificationChannel.IN_APP) is True


class TestUpdateAlertPreference:
    def test_update_channels(self):
        prefs = default_preferences("user1")
        updated = update_alert_preference(
            prefs,
            "sweet_spot",
            channels=[NotificationChannel.EMAIL, NotificationChannel.IN_APP],
        )
        assert NotificationChannel.EMAIL in updated.channels

    def test_mute_alert(self):
        prefs = default_preferences("user1")
        updated = update_alert_preference(prefs, "devaluation", muted=True)
        assert updated.muted is True
        assert should_notify(prefs, "devaluation", NotificationChannel.EMAIL) is False

    def test_create_new_alert_type(self):
        prefs = default_preferences("user1")
        updated = update_alert_preference(
            prefs,
            "new_type",
            channels=[NotificationChannel.PUSH],
        )
        assert updated.alert_type == "new_type"
        assert NotificationChannel.PUSH in updated.channels


class TestPreferencesSummary:
    def test_summary_structure(self):
        prefs = default_preferences("user1")
        s = preferences_summary(prefs)
        assert s["user_id"] == "user1"
        assert len(s["enabled_channels"]) >= 3
        assert s["total_alert_types"] >= 5

    def test_muted_in_summary(self):
        prefs = default_preferences("user1")
        update_alert_preference(prefs, "devaluation", muted=True)
        s = preferences_summary(prefs)
        assert "devaluation" in s["muted_alert_types"]


class TestNotificationPrefsStore:
    def test_get_creates_default(self):
        from redeemflow.notifications.preferences import reset_notification_prefs

        reset_notification_prefs()
        prefs = get_notification_prefs("user1")
        assert prefs.user_id == "user1"
        assert "email" in prefs.channels

    def test_get_returns_same_instance(self):
        from redeemflow.notifications.preferences import reset_notification_prefs

        reset_notification_prefs()
        p1 = get_notification_prefs("user1")
        p2 = get_notification_prefs("user1")
        assert p1 is p2


class TestNotificationPrefsAPI:
    AUTH_HEADERS = {"Authorization": "Bearer test-token-eric"}

    @pytest.fixture
    def client(self):
        from redeemflow.app import create_app
        from redeemflow.notifications.preferences import reset_notification_prefs
        from redeemflow.ports import PortBundle

        reset_notification_prefs()
        return TestClient(create_app(ports=PortBundle()))

    def test_get_prefs(self, client):
        resp = client.get("/api/notifications/preferences", headers=self.AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "channels" in data
        assert "alert_preferences" in data

    def test_update_channel(self, client):
        resp = client.put(
            "/api/notifications/preferences/channel/email",
            json={"enabled": False},
            headers=self.AUTH_HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["channel"]["enabled"] is False

    def test_update_alert(self, client):
        resp = client.put(
            "/api/notifications/preferences/alert/devaluation",
            json={"muted": True},
            headers=self.AUTH_HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["alert"]["muted"] is True

    def test_prefs_require_auth(self, client):
        assert client.get("/api/notifications/preferences").status_code == 401
