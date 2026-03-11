"""Tests for expiration alerts notification bridge."""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from redeemflow.notifications.expiration_alerts import (
    ExpirationNotification,
    check_portfolio_expirations,
)
from redeemflow.notifications.models import AlertPriority
from redeemflow.portfolio.expiration import ExpirationPolicy
from redeemflow.portfolio.models import PointBalance


def _balance(code: str, points: int) -> PointBalance:
    return PointBalance(program_code=code, points=points, cpp_baseline=Decimal("1.0"))


def _policy(code: str, months: int) -> ExpirationPolicy:
    return ExpirationPolicy(program_code=code, expires=True, months_inactivity=months, activity_types=["earn"])


class TestCheckPortfolioExpirations:
    def test_no_balances(self):
        summary = check_portfolio_expirations([], [])
        assert summary.total_programs_at_risk == 0
        assert summary.total_points_at_risk == 0

    def test_non_expiring_program(self):
        balances = [_balance("chase-ur", 50000)]
        policies = [ExpirationPolicy(program_code="chase-ur", expires=False, months_inactivity=None)]
        summary = check_portfolio_expirations(balances, policies)
        assert summary.total_programs_at_risk == 0

    def test_expiring_program_generates_notification(self):
        balances = [_balance("hilton", 100000)]
        policies = [_policy("hilton", 12)]
        summary = check_portfolio_expirations(balances, policies)
        assert summary.total_programs_at_risk == 1
        assert summary.total_points_at_risk == 100000
        assert len(summary.notifications) == 1

    def test_notification_has_actions(self):
        balances = [_balance("hyatt", 30000)]
        policies = [_policy("hyatt", 24)]
        summary = check_portfolio_expirations(balances, policies)
        n = summary.notifications[0]
        assert len(n.actions) >= 2
        assert isinstance(n, ExpirationNotification)

    def test_critical_priority_short_inactivity(self):
        balances = [_balance("ihg", 50000)]
        policies = [_policy("ihg", 1)]  # 1 month → 15 days → critical
        summary = check_portfolio_expirations(balances, policies)
        assert summary.critical_count == 1
        assert summary.highest_priority == AlertPriority.CRITICAL

    def test_high_priority_medium_inactivity(self):
        balances = [_balance("hilton", 50000)]
        policies = [_policy("hilton", 3)]  # 3 months → 45 days → high
        summary = check_portfolio_expirations(balances, policies)
        assert summary.warning_count == 1
        assert summary.highest_priority == AlertPriority.HIGH

    def test_medium_priority_long_inactivity(self):
        balances = [_balance("marriott", 80000)]
        policies = [_policy("marriott", 24)]  # 24 months → 360 days → medium (90+ cap)
        summary = check_portfolio_expirations(balances, policies)
        assert summary.watch_count == 1
        assert summary.highest_priority == AlertPriority.MEDIUM

    def test_value_estimation(self):
        balances = [_balance("hyatt", 50000)]
        policies = [_policy("hyatt", 2)]  # short window
        summary = check_portfolio_expirations(balances, policies)
        assert summary.total_value_at_risk > Decimal("0")

    def test_multiple_programs(self):
        balances = [
            _balance("hilton", 100000),
            _balance("marriott", 50000),
            _balance("hyatt", 30000),
        ]
        policies = [
            _policy("hilton", 12),
            _policy("marriott", 24),
            _policy("hyatt", 24),
        ]
        summary = check_portfolio_expirations(balances, policies)
        assert summary.total_programs_at_risk == 3
        assert summary.total_points_at_risk == 180000

    def test_zero_balance_excluded(self):
        balances = [_balance("hilton", 0)]
        policies = [_policy("hilton", 12)]
        summary = check_portfolio_expirations(balances, policies)
        assert summary.total_programs_at_risk == 0

    def test_uses_default_policies_when_none(self):
        balances = [_balance("hilton", 50000)]
        summary = check_portfolio_expirations(balances)
        assert summary.total_programs_at_risk == 1

    def test_sorted_by_priority(self):
        balances = [
            _balance("marriott", 50000),
            _balance("ihg", 40000),
        ]
        policies = [
            _policy("marriott", 24),
            _policy("ihg", 1),  # critical
        ]
        summary = check_portfolio_expirations(balances, policies)
        assert summary.notifications[0].program_code == "ihg"
        assert summary.notifications[0].priority == AlertPriority.CRITICAL

    def test_notification_message_contains_value(self):
        balances = [_balance("hyatt", 25000)]
        policies = [_policy("hyatt", 4)]
        summary = check_portfolio_expirations(balances, policies)
        assert "$" in summary.notifications[0].message

    def test_summary_is_frozen(self):
        summary = check_portfolio_expirations([], [])
        with pytest.raises(AttributeError):
            summary.total_programs_at_risk = 5

    def test_notification_is_frozen(self):
        balances = [_balance("hilton", 10000)]
        policies = [_policy("hilton", 12)]
        summary = check_portfolio_expirations(balances, policies)
        with pytest.raises(AttributeError):
            summary.notifications[0].priority = AlertPriority.LOW


class TestExpirationAlertsAPI:
    AUTH_HEADERS = {"Authorization": "Bearer test-token-eric"}

    @pytest.fixture
    def client(self):
        from redeemflow.app import create_app
        from redeemflow.ports import PortBundle

        return TestClient(create_app(ports=PortBundle()))

    def test_expiration_alerts_endpoint(self, client):
        resp = client.get("/api/notifications/expiration-alerts", headers=self.AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_programs_at_risk" in data
        assert "notifications" in data
        assert "highest_priority" in data

    def test_expiration_alerts_requires_auth(self, client):
        resp = client.get("/api/notifications/expiration-alerts")
        assert resp.status_code == 401

    def test_notifications_have_actions(self, client):
        resp = client.get("/api/notifications/expiration-alerts", headers=self.AUTH_HEADERS)
        data = resp.json()
        for n in data["notifications"]:
            assert "actions" in n
            assert len(n["actions"]) >= 1
