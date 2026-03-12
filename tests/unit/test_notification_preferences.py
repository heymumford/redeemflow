"""Tests for notification preferences and email templates."""

from __future__ import annotations

import pytest

from redeemflow.notifications.email_templates import render_alert_email
from redeemflow.notifications.preferences import (
    NotificationChannel,
    default_preferences,
    should_notify,
)


class TestDefaultPreferences:
    def test_creates_with_all_channels(self):
        prefs = default_preferences("user-1")
        assert "email" in prefs.channels
        assert "push" in prefs.channels
        assert "in_app" in prefs.channels

    def test_all_channels_enabled(self):
        prefs = default_preferences("user-1")
        for cp in prefs.channels.values():
            assert cp.enabled is True

    def test_devaluation_alert_on_all_channels(self):
        prefs = default_preferences("user-1")
        deval = prefs.alert_preferences["devaluation"]
        assert NotificationChannel.EMAIL in deval.channels
        assert NotificationChannel.PUSH in deval.channels
        assert NotificationChannel.IN_APP in deval.channels

    def test_sweet_spot_in_app_only(self):
        prefs = default_preferences("user-1")
        sweet = prefs.alert_preferences["sweet_spot"]
        assert sweet.channels == [NotificationChannel.IN_APP]


class TestShouldNotify:
    def test_devaluation_email_enabled(self):
        prefs = default_preferences("user-1")
        assert should_notify(prefs, "devaluation", NotificationChannel.EMAIL) is True

    def test_sweet_spot_email_disabled(self):
        prefs = default_preferences("user-1")
        assert should_notify(prefs, "sweet_spot", NotificationChannel.EMAIL) is False

    def test_sweet_spot_in_app_enabled(self):
        prefs = default_preferences("user-1")
        assert should_notify(prefs, "sweet_spot", NotificationChannel.IN_APP) is True

    def test_muted_alert_type(self):
        prefs = default_preferences("user-1")
        prefs.alert_preferences["devaluation"].muted = True
        assert should_notify(prefs, "devaluation", NotificationChannel.EMAIL) is False

    def test_disabled_channel(self):
        prefs = default_preferences("user-1")
        prefs.channels["email"].enabled = False
        assert should_notify(prefs, "devaluation", NotificationChannel.EMAIL) is False

    def test_unknown_alert_type_defaults_to_in_app(self):
        prefs = default_preferences("user-1")
        assert should_notify(prefs, "unknown_type", NotificationChannel.IN_APP) is True
        assert should_notify(prefs, "unknown_type", NotificationChannel.EMAIL) is False


class TestEmailTemplates:
    def test_render_devaluation_email(self):
        email = render_alert_email(
            alert_type="devaluation",
            priority="critical",
            title="Hilton Points Devaluation",
            message="Hilton Honors is increasing award chart prices by 30%.",
            program="hilton",
        )
        assert "hilton" in email.subject
        assert "devaluation" in email.subject
        assert "Hilton Points Devaluation" in email.body_html
        assert "Hilton Points Devaluation" in email.body_text

    def test_render_with_all_priorities(self):
        for priority in ["critical", "high", "medium", "low"]:
            email = render_alert_email(
                alert_type="expiration",
                priority=priority,
                title="Points Expiring",
                message="Your points will expire.",
                program="united",
            )
            assert len(email.subject) > 0
            assert len(email.body_html) > 100
            assert len(email.body_text) > 50

    def test_text_body_contains_all_fields(self):
        email = render_alert_email(
            alert_type="transfer_bonus",
            priority="medium",
            title="Transfer Bonus",
            message="20% bonus on Chase UR to Hyatt.",
            program="chase-ur",
        )
        assert "Transfer Bonus" in email.body_text
        assert "chase-ur" in email.body_text
        assert "medium" in email.body_text

    def test_html_contains_priority_color(self):
        email = render_alert_email(
            alert_type="devaluation",
            priority="critical",
            title="Devaluation",
            message="Critical alert.",
            program="hilton",
        )
        assert "#dc2626" in email.body_html  # Red for critical


class TestAPIEndpoints:
    AUTH_HEADERS = {"Authorization": "Bearer test-token-eric"}

    @pytest.fixture(autouse=True)
    def _reset_prefs(self):
        """Reset global notification preferences between tests."""
        from redeemflow.notifications.preferences import reset_notification_prefs

        reset_notification_prefs()
        yield
        reset_notification_prefs()

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient

        from redeemflow.app import create_app
        from redeemflow.ports import PortBundle

        return TestClient(create_app(ports=PortBundle()))

    def test_get_preferences(self, client):
        resp = client.get("/api/notifications/preferences", headers=self.AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "channels" in data
        assert "alert_preferences" in data
        assert "email" in data["channels"]

    def test_update_preferences(self, client):
        resp = client.post(
            "/api/notifications/preferences",
            json={
                "channels": [{"channel": "email", "enabled": False, "frequency": "weekly_digest"}],
                "timezone": "America/New_York",
            },
            headers=self.AUTH_HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "updated"

    def test_check_notification(self, client):
        resp = client.get("/api/notifications/check/devaluation/email", headers=self.AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["should_notify"] is True

    def test_check_unknown_channel(self, client):
        resp = client.get("/api/notifications/check/devaluation/carrier_pigeon", headers=self.AUTH_HEADERS)
        assert resp.status_code == 404
        assert "detail" in resp.json()

    def test_unauthenticated_returns_401(self, client):
        resp = client.get("/api/notifications/preferences")
        assert resp.status_code == 401
