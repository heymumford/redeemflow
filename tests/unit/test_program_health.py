"""Tests for program health scores — reliability and devaluation risk."""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from redeemflow.valuations.program_health import (
    DevalRisk,
    HealthGrade,
    ProgramHealthScore,
    assess_program_health,
)


class TestAssessProgramHealth:
    def test_strong_program(self):
        score = assess_program_health(
            program_code="hyatt",
            program_name="World of Hyatt",
            cpp_values={"tpg": Decimal("1.7"), "omaat": Decimal("1.8"), "nw": Decimal("1.6")},
            transfer_partner_count=5,
            sweet_spot_count=3,
            trend_direction="stable",
        )
        assert isinstance(score, ProgramHealthScore)
        assert score.grade in (HealthGrade.EXCELLENT, HealthGrade.GOOD)
        assert score.devaluation_risk == DevalRisk.LOW

    def test_weak_program(self):
        score = assess_program_health(
            program_code="test",
            program_name="Test Program",
            cpp_values={"a": Decimal("0.3"), "b": Decimal("0.8")},
            transfer_partner_count=0,
            sweet_spot_count=0,
            trend_direction="down",
        )
        assert score.overall_score < 50
        assert score.devaluation_risk in (DevalRisk.HIGH, DevalRisk.IMMINENT)

    def test_downtrend_reduces_score(self):
        base = assess_program_health("x", "X", {"a": Decimal("1.5")}, trend_direction="stable")
        down = assess_program_health("x", "X", {"a": Decimal("1.5")}, trend_direction="down")
        assert down.overall_score < base.overall_score

    def test_uptrend_boosts_score(self):
        base = assess_program_health("x", "X", {"a": Decimal("1.5")}, trend_direction="stable")
        up = assess_program_health("x", "X", {"a": Decimal("1.5")}, trend_direction="up")
        assert up.overall_score >= base.overall_score

    def test_liquidity_from_partners(self):
        few = assess_program_health("x", "X", {"a": Decimal("1.0")}, transfer_partner_count=1)
        many = assess_program_health("x", "X", {"a": Decimal("1.0")}, transfer_partner_count=8)
        assert many.liquidity_score > few.liquidity_score

    def test_redemption_from_sweet_spots(self):
        none = assess_program_health("x", "X", {"a": Decimal("1.0")}, sweet_spot_count=0)
        some = assess_program_health("x", "X", {"a": Decimal("1.0")}, sweet_spot_count=3)
        assert some.redemption_score > none.redemption_score

    def test_stability_from_cpp_variance(self):
        stable = assess_program_health("x", "X", {"a": Decimal("1.50"), "b": Decimal("1.52"), "c": Decimal("1.48")})
        volatile = assess_program_health("x", "X", {"a": Decimal("0.50"), "b": Decimal("2.50"), "c": Decimal("1.00")})
        assert stable.stability_score > volatile.stability_score

    def test_single_source_defaults_stability(self):
        score = assess_program_health("x", "X", {"a": Decimal("1.5")})
        assert score.stability_score == 50

    def test_empty_cpp_values(self):
        score = assess_program_health("x", "X", {})
        assert score.stability_score == 50
        assert score.value_score == 50

    def test_grade_boundaries(self):
        # High score
        high = assess_program_health(
            "x",
            "X",
            {"a": Decimal("2.0"), "b": Decimal("2.0")},
            transfer_partner_count=8,
            sweet_spot_count=5,
        )
        assert high.grade in (HealthGrade.EXCELLENT, HealthGrade.GOOD)

    def test_recommendation_text(self):
        score = assess_program_health(
            "x",
            "X",
            {"a": Decimal("1.5"), "b": Decimal("1.6")},
            transfer_partner_count=4,
            sweet_spot_count=2,
        )
        assert score.recommendation != ""

    def test_imminent_deval_risk(self):
        score = assess_program_health(
            "x",
            "X",
            {"a": Decimal("0.5"), "b": Decimal("2.0")},  # Very high variance
            trend_direction="down",
        )
        assert score.devaluation_risk in (DevalRisk.HIGH, DevalRisk.IMMINENT)


class TestHealthAPI:
    @pytest.fixture
    def client(self):
        from redeemflow.app import create_app
        from redeemflow.ports import PortBundle

        return TestClient(create_app(ports=PortBundle()))

    def test_program_health_endpoint(self, client):
        resp = client.get("/api/program-health")
        assert resp.status_code == 200
        data = resp.json()
        assert "programs" in data
        assert len(data["programs"]) > 0

        first = data["programs"][0]
        assert "overall_score" in first
        assert "grade" in first
        assert "devaluation_risk" in first
        assert "recommendation" in first

    def test_programs_sorted_by_score(self, client):
        resp = client.get("/api/program-health")
        programs = resp.json()["programs"]
        scores = [p["overall_score"] for p in programs]
        assert scores == sorted(scores, reverse=True)
