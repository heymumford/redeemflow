"""Tests for points expiration calendar and timeline."""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from redeemflow.portfolio.calendar import (
    CalendarSummary,
    ExpirationUrgency,
    build_calendar,
)
from redeemflow.portfolio.expiration import EXPIRATION_POLICIES
from redeemflow.portfolio.models import PointBalance


def _balance(code: str, points: int) -> PointBalance:
    return PointBalance(program_code=code, points=points, cpp_baseline=Decimal("1.0"))


class TestBuildCalendar:
    def test_non_expiring_programs_marked_safe(self):
        balances = [_balance("chase-ur", 50000)]
        summary = build_calendar(balances, EXPIRATION_POLICIES)
        assert summary.programs_safe == 1
        assert summary.programs_with_expiry == 0
        assert summary.events[0].urgency == ExpirationUrgency.NEVER

    def test_expiring_program_generates_event(self):
        balances = [_balance("united", 80000)]
        summary = build_calendar(balances, EXPIRATION_POLICIES)
        assert summary.programs_with_expiry == 1
        united_events = [e for e in summary.events if e.program_code == "united"]
        assert len(united_events) == 1
        assert united_events[0].event_type == "expiration"

    def test_mixed_portfolio(self):
        balances = [
            _balance("chase-ur", 50000),
            _balance("united", 80000),
            _balance("marriott", 100000),
        ]
        summary = build_calendar(balances, EXPIRATION_POLICIES)
        assert summary.total_programs == 3
        assert summary.programs_safe >= 1
        assert summary.programs_with_expiry >= 1

    def test_zero_balance_excluded(self):
        balances = [_balance("united", 0)]
        summary = build_calendar(balances, EXPIRATION_POLICIES)
        assert summary.total_programs == 0

    def test_events_sorted_by_days_remaining(self):
        balances = [
            _balance("united", 80000),
            _balance("ihg", 50000),
            _balance("marriott", 100000),
        ]
        summary = build_calendar(balances, EXPIRATION_POLICIES)
        expiry_events = [e for e in summary.events if e.event_type == "expiration"]
        days = [e.days_remaining for e in expiry_events]
        assert days == sorted(days)

    def test_cpp_values_affect_value_at_risk(self):
        balances = [_balance("united", 100000)]
        cpp = {"united": Decimal("1.4")}
        summary = build_calendar(balances, EXPIRATION_POLICIES, cpp_values=cpp)
        united = [e for e in summary.events if e.program_code == "united"][0]
        assert united.value_at_risk == Decimal("1400.00")

    def test_default_cpp(self):
        balances = [_balance("united", 100000)]
        summary = build_calendar(balances, EXPIRATION_POLICIES)
        united = [e for e in summary.events if e.program_code == "united"][0]
        # Default 1.0 CPP: 100000 * 1.0 / 100 = 1000.00
        assert united.value_at_risk == Decimal("1000.00")

    def test_summary_counts(self):
        balances = [
            _balance("chase-ur", 50000),
            _balance("amex-mr", 30000),
            _balance("united", 80000),
        ]
        summary = build_calendar(balances, EXPIRATION_POLICIES)
        assert isinstance(summary, CalendarSummary)
        assert summary.total_programs == 3

    def test_unknown_program_treated_as_no_policy(self):
        balances = [_balance("unknown-prog", 10000)]
        summary = build_calendar(balances, EXPIRATION_POLICIES)
        assert summary.programs_safe == 1

    def test_action_text_present(self):
        balances = [_balance("united", 80000)]
        summary = build_calendar(balances, EXPIRATION_POLICIES)
        for event in summary.events:
            assert len(event.action) > 0

    def test_program_name_resolved(self):
        balances = [_balance("chase-ur", 50000)]
        summary = build_calendar(balances, EXPIRATION_POLICIES)
        assert summary.events[0].program_name == "Chase Ultimate Rewards"

    def test_empty_portfolio(self):
        summary = build_calendar([], EXPIRATION_POLICIES)
        assert summary.total_programs == 0
        assert summary.events == []
        assert summary.next_event is None


class TestCalendarAPI:
    AUTH_HEADERS = {"Authorization": "Bearer test-token-eric"}

    @pytest.fixture
    def client(self):
        from redeemflow.app import create_app
        from redeemflow.ports import PortBundle

        return TestClient(create_app(ports=PortBundle()))

    def test_calendar_requires_auth(self, client):
        resp = client.get("/api/portfolio/calendar")
        assert resp.status_code == 401

    def test_calendar_returns_data(self, client):
        resp = client.get("/api/portfolio/calendar", headers=self.AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_programs" in data
        assert "events" in data
        assert "programs_with_expiry" in data
        assert "programs_safe" in data

    def test_calendar_events_have_urgency(self, client):
        resp = client.get("/api/portfolio/calendar", headers=self.AUTH_HEADERS)
        data = resp.json()
        for event in data["events"]:
            assert "urgency" in event
            assert event["urgency"] in ["expired", "critical", "warning", "upcoming", "safe", "never"]

    def test_calendar_events_have_action(self, client):
        resp = client.get("/api/portfolio/calendar", headers=self.AUTH_HEADERS)
        data = resp.json()
        for event in data["events"]:
            assert "action" in event
            assert len(event["action"]) > 0
