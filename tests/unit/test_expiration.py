"""Sprint 2: Points expiration tracker — alert users before points expire."""

from __future__ import annotations

import pytest

from redeemflow.portfolio.expiration import (
    EXPIRATION_POLICIES,
    ExpirationAlert,
    ExpirationPolicy,
    ExpirationTracker,
)
from redeemflow.portfolio.models import PointBalance
from decimal import Decimal


class TestExpirationPolicy:
    def test_policy_is_frozen(self):
        policy = ExpirationPolicy(
            program_code="united",
            expires=True,
            months_inactivity=18,
            activity_types=["flight", "earn", "redeem"],
        )
        with pytest.raises(AttributeError):
            policy.expires = False

    def test_expiring_program(self):
        policy = ExpirationPolicy(
            program_code="united",
            expires=True,
            months_inactivity=18,
            activity_types=["flight", "earn", "redeem"],
        )
        assert policy.expires is True
        assert policy.months_inactivity == 18

    def test_non_expiring_program(self):
        policy = ExpirationPolicy(
            program_code="delta",
            expires=False,
            months_inactivity=None,
            activity_types=[],
        )
        assert policy.expires is False
        assert policy.months_inactivity is None

    def test_policy_has_activity_types(self):
        policy = ExpirationPolicy(
            program_code="hilton",
            expires=True,
            months_inactivity=12,
            activity_types=["stay", "earn", "redeem"],
        )
        assert "stay" in policy.activity_types

    def test_seed_policies_exist(self):
        assert len(EXPIRATION_POLICIES) > 0

    def test_seed_policies_cover_known_programs(self):
        codes = {p.program_code for p in EXPIRATION_POLICIES}
        # At minimum, the major programs from Sprint 1
        assert "united" in codes
        assert "delta" in codes
        assert "hyatt" in codes
        assert "marriott" in codes
        assert "hilton" in codes


class TestExpirationAlert:
    def test_alert_is_frozen(self):
        alert = ExpirationAlert(
            program_code="united",
            points_at_risk=50000,
            days_until_expiry=30,
            alert_level=30,
        )
        with pytest.raises(AttributeError):
            alert.alert_level = 90

    def test_alert_90_day(self):
        alert = ExpirationAlert(
            program_code="united",
            points_at_risk=50000,
            days_until_expiry=85,
            alert_level=90,
        )
        assert alert.alert_level == 90

    def test_alert_60_day(self):
        alert = ExpirationAlert(
            program_code="marriott",
            points_at_risk=120000,
            days_until_expiry=55,
            alert_level=60,
        )
        assert alert.alert_level == 60

    def test_alert_30_day(self):
        alert = ExpirationAlert(
            program_code="hilton",
            points_at_risk=200000,
            days_until_expiry=25,
            alert_level=30,
        )
        assert alert.alert_level == 30

    def test_alert_has_points_at_risk(self):
        alert = ExpirationAlert(
            program_code="united",
            points_at_risk=75000,
            days_until_expiry=45,
            alert_level=60,
        )
        assert alert.points_at_risk == 75000


class TestExpirationTracker:
    @pytest.fixture
    def tracker(self):
        return ExpirationTracker()

    @pytest.fixture
    def expiring_policies(self):
        return [
            ExpirationPolicy(
                program_code="united",
                expires=True,
                months_inactivity=18,
                activity_types=["flight", "earn", "redeem"],
            ),
            ExpirationPolicy(
                program_code="delta",
                expires=False,
                months_inactivity=None,
                activity_types=[],
            ),
            ExpirationPolicy(
                program_code="hilton",
                expires=True,
                months_inactivity=12,
                activity_types=["stay", "earn", "redeem"],
            ),
        ]

    @pytest.fixture
    def sample_balances(self):
        return [
            PointBalance(program_code="united", points=50000, cpp_baseline=Decimal("1.2")),
            PointBalance(program_code="delta", points=30000, cpp_baseline=Decimal("1.1")),
            PointBalance(program_code="hilton", points=200000, cpp_baseline=Decimal("0.5")),
        ]

    def test_check_expirations_returns_alerts(self, tracker, sample_balances, expiring_policies):
        alerts = tracker.check_expirations(sample_balances, expiring_policies)
        assert isinstance(alerts, list)
        assert all(isinstance(a, ExpirationAlert) for a in alerts)

    def test_non_expiring_programs_produce_no_alerts(self, tracker, expiring_policies):
        balances = [PointBalance(program_code="delta", points=30000, cpp_baseline=Decimal("1.1"))]
        alerts = tracker.check_expirations(balances, expiring_policies)
        assert len(alerts) == 0

    def test_expiring_programs_produce_alerts(self, tracker, expiring_policies):
        balances = [PointBalance(program_code="united", points=50000, cpp_baseline=Decimal("1.2"))]
        alerts = tracker.check_expirations(balances, expiring_policies)
        assert len(alerts) > 0
        assert alerts[0].program_code == "united"

    def test_zero_point_balance_no_alert(self, tracker, expiring_policies):
        balances = [PointBalance(program_code="united", points=0, cpp_baseline=Decimal("1.2"))]
        alerts = tracker.check_expirations(balances, expiring_policies)
        assert len(alerts) == 0

    def test_program_without_policy_no_alert(self, tracker):
        balances = [PointBalance(program_code="unknown-program", points=50000, cpp_baseline=Decimal("1.0"))]
        policies = [
            ExpirationPolicy(
                program_code="united",
                expires=True,
                months_inactivity=18,
                activity_types=["flight"],
            ),
        ]
        alerts = tracker.check_expirations(balances, policies)
        assert len(alerts) == 0

    def test_alert_includes_points_at_risk(self, tracker, expiring_policies):
        balances = [PointBalance(program_code="hilton", points=200000, cpp_baseline=Decimal("0.5"))]
        alerts = tracker.check_expirations(balances, expiring_policies)
        assert len(alerts) > 0
        assert alerts[0].points_at_risk == 200000

    def test_mixed_policies_filter_correctly(self, tracker, sample_balances, expiring_policies):
        alerts = tracker.check_expirations(sample_balances, expiring_policies)
        alert_codes = {a.program_code for a in alerts}
        # Delta never expires, so no alert
        assert "delta" not in alert_codes
        # United and Hilton expire, so they should have alerts
        assert "united" in alert_codes
        assert "hilton" in alert_codes

    def test_alert_level_based_on_inactivity_months(self, tracker):
        policies = [
            ExpirationPolicy(
                program_code="short-expire",
                expires=True,
                months_inactivity=2,
                activity_types=["earn"],
            ),
        ]
        balances = [PointBalance(program_code="short-expire", points=10000, cpp_baseline=Decimal("1.0"))]
        alerts = tracker.check_expirations(balances, policies)
        assert len(alerts) > 0
        assert alerts[0].alert_level in (30, 60, 90)

    def test_check_expirations_with_seed_policies(self, tracker):
        balances = [
            PointBalance(program_code="united", points=50000, cpp_baseline=Decimal("1.2")),
            PointBalance(program_code="hyatt", points=30000, cpp_baseline=Decimal("1.8")),
        ]
        alerts = tracker.check_expirations(balances, EXPIRATION_POLICIES)
        assert isinstance(alerts, list)
