"""Tests for points valuation trend tracking."""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from redeemflow.valuations.trends import (
    TrendDirection,
    TrendTracker,
    ValuationSnapshot,
)


class TestTrendTracker:
    def test_record_creates_snapshot(self):
        tracker = TrendTracker()
        snap = tracker.record("united", Decimal("1.20"), "2025-01-01")
        assert isinstance(snap, ValuationSnapshot)
        assert snap.program_code == "united"
        assert snap.cpp == Decimal("1.20")

    def test_get_history(self):
        tracker = TrendTracker()
        tracker.record("united", Decimal("1.20"), "2025-01-01")
        tracker.record("united", Decimal("1.25"), "2025-02-01")
        history = tracker.get_history("united")
        assert len(history) == 2
        assert history[0].date == "2025-01-01"

    def test_get_history_empty(self):
        assert TrendTracker().get_history("nope") == []

    def test_tracked_programs(self):
        tracker = TrendTracker()
        tracker.record("united", Decimal("1.20"), "2025-01-01")
        tracker.record("hyatt", Decimal("1.70"), "2025-01-01")
        assert tracker.tracked_programs == ["hyatt", "united"]


class TestTrendAnalysis:
    def test_stable_single_snapshot(self):
        tracker = TrendTracker()
        tracker.record("united", Decimal("1.20"), "2025-01-01")
        analysis = tracker.analyze("united")
        assert analysis.direction == TrendDirection.STABLE
        assert analysis.change_pct == Decimal("0")

    def test_upward_trend(self):
        tracker = TrendTracker()
        tracker.record("united", Decimal("1.00"), "2025-01-01")
        tracker.record("united", Decimal("1.20"), "2025-03-01")
        analysis = tracker.analyze("united")
        assert analysis.direction == TrendDirection.UP
        assert analysis.change_pct == Decimal("20.0")
        assert analysis.period_days == 59

    def test_downward_trend(self):
        tracker = TrendTracker()
        tracker.record("hilton", Decimal("0.60"), "2025-01-01")
        tracker.record("hilton", Decimal("0.50"), "2025-02-01")
        analysis = tracker.analyze("hilton")
        assert analysis.direction == TrendDirection.DOWN
        assert analysis.change_pct < 0

    def test_devaluation_alert(self):
        tracker = TrendTracker()
        tracker.record("marriott", Decimal("0.80"), "2025-01-01")
        tracker.record("marriott", Decimal("0.60"), "2025-03-01")
        analysis = tracker.analyze("marriott")
        assert "devaluation" in analysis.alert.lower()

    def test_gain_alert(self):
        tracker = TrendTracker()
        tracker.record("hyatt", Decimal("1.50"), "2025-01-01")
        tracker.record("hyatt", Decimal("1.80"), "2025-03-01")
        analysis = tracker.analyze("hyatt")
        assert "increase" in analysis.alert.lower()

    def test_no_alert_for_small_change(self):
        tracker = TrendTracker()
        tracker.record("united", Decimal("1.20"), "2025-01-01")
        tracker.record("united", Decimal("1.21"), "2025-02-01")
        analysis = tracker.analyze("united")
        assert analysis.alert == ""

    def test_empty_program(self):
        analysis = TrendTracker().analyze("nope")
        assert analysis.direction == TrendDirection.STABLE
        assert analysis.current_cpp == Decimal("0")

    def test_program_name_passed_through(self):
        tracker = TrendTracker()
        tracker.record("united", Decimal("1.20"), "2025-01-01")
        analysis = tracker.analyze("united", "United MileagePlus")
        assert analysis.program_name == "United MileagePlus"


class TestMarketSummary:
    def test_market_summary(self):
        tracker = TrendTracker()
        tracker.record("united", Decimal("1.20"), "2025-01-01")
        tracker.record("united", Decimal("1.30"), "2025-03-01")
        tracker.record("hilton", Decimal("0.60"), "2025-01-01")
        tracker.record("hilton", Decimal("0.50"), "2025-03-01")
        tracker.record("hyatt", Decimal("1.70"), "2025-01-01")
        tracker.record("hyatt", Decimal("1.70"), "2025-03-01")

        summary = tracker.market_summary()
        assert summary.total_programs == 3
        assert summary.programs_up == 1
        assert summary.programs_down == 1
        assert summary.programs_stable == 1
        assert summary.biggest_gain.program_code == "united"
        assert summary.biggest_loss.program_code == "hilton"

    def test_market_summary_empty(self):
        summary = TrendTracker().market_summary()
        assert summary.total_programs == 0
        assert summary.biggest_gain is None

    def test_market_summary_all_up(self):
        tracker = TrendTracker()
        tracker.record("a", Decimal("1.00"), "2025-01-01")
        tracker.record("a", Decimal("1.50"), "2025-03-01")
        tracker.record("b", Decimal("2.00"), "2025-01-01")
        tracker.record("b", Decimal("2.20"), "2025-03-01")
        summary = tracker.market_summary()
        assert summary.programs_up == 2
        assert summary.programs_down == 0
        assert summary.biggest_loss is None


class TestTrendsAPI:
    @pytest.fixture
    def client(self):
        from redeemflow.app import create_app
        from redeemflow.ports import PortBundle
        from redeemflow.valuations.trends import reset_tracker

        reset_tracker()
        return TestClient(create_app(ports=PortBundle()))

    def test_market_trends(self, client):
        resp = client.get("/api/trends")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_programs" in data
        assert "trends" in data
        assert data["total_programs"] > 0

    def test_program_trend(self, client):
        resp = client.get("/api/trends/united")
        assert resp.status_code == 200
        data = resp.json()
        assert data["program_code"] == "united"
        assert "snapshots" in data
        assert "direction" in data

    def test_unknown_program_trend(self, client):
        resp = client.get("/api/trends/nonexistent")
        assert resp.status_code == 200
        data = resp.json()
        assert data["current_cpp"] == "0"
