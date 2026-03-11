"""Tests for retail redemption analysis — value destruction detection."""

from __future__ import annotations

from decimal import Decimal

import pytest

from redeemflow.redemptions.retail import (
    RETAIL_REDEMPTIONS,
    analyze_retail_redemption,
    find_retail_redemptions,
    worst_retail_redemption,
)


class TestRetailData:
    def test_chase_ur_has_retail(self):
        redemptions = find_retail_redemptions("chase-ur")
        assert len(redemptions) >= 3

    def test_amex_mr_has_retail(self):
        redemptions = find_retail_redemptions("amex-mr")
        assert len(redemptions) >= 3

    def test_unknown_program_returns_empty(self):
        redemptions = find_retail_redemptions("nonexistent")
        assert redemptions == []

    def test_all_retail_have_positive_cpp(self):
        for r in RETAIL_REDEMPTIONS:
            assert r.cpp > Decimal("0")

    def test_value_rating_assignment(self):
        for r in RETAIL_REDEMPTIONS:
            assert r.value_rating in ("fair", "below_average", "poor")

    def test_worst_returns_lowest_cpp(self):
        worst = worst_retail_redemption("amex-mr")
        assert worst is not None
        all_amex = find_retail_redemptions("amex-mr")
        assert worst.cpp == min(r.cpp for r in all_amex)


class TestRetailAnalysis:
    def test_value_destruction_calculated(self):
        worst = worst_retail_redemption("amex-mr")
        analysis = analyze_retail_redemption(worst, 50000)
        assert analysis.value_destroyed > Decimal("0")
        assert analysis.destruction_pct > Decimal("0")

    def test_travel_value_higher_than_retail(self):
        worst = worst_retail_redemption("amex-mr")
        analysis = analyze_retail_redemption(worst, 50000, Decimal("2.0"))
        assert analysis.travel_value > analysis.retail_value

    def test_recommendation_valid(self):
        worst = worst_retail_redemption("chase-ur")
        analysis = analyze_retail_redemption(worst, 100000)
        assert analysis.recommendation in ("acceptable", "consider_travel", "avoid")
        assert len(analysis.rationale) > 0

    def test_high_cpp_retail_acceptable(self):
        # Statement credit at 1.0 CPP vs 1.0 CPP alternative → acceptable
        for r in find_retail_redemptions("chase-ur"):
            if r.cpp >= Decimal("1.0"):
                analysis = analyze_retail_redemption(r, 50000, Decimal("1.0"))
                assert analysis.recommendation == "acceptable"
                break


class TestAPIEndpoints:
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient

        from redeemflow.app import create_app
        from redeemflow.ports import PortBundle

        return TestClient(create_app(ports=PortBundle()))

    def test_list_retail_redemptions(self, client):
        resp = client.get("/api/retail-redemptions/chase-ur")
        assert resp.status_code == 200
        data = resp.json()
        assert data["program"] == "chase-ur"
        assert data["count"] >= 3

    def test_list_unknown_program(self, client):
        resp = client.get("/api/retail-redemptions/nonexistent")
        assert resp.status_code == 200
        assert resp.json()["count"] == 0

    def test_analyze_retail(self, client):
        resp = client.post(
            "/api/retail-redemptions/analyze",
            json={"program": "amex-mr", "points": 50000},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "value_destroyed" in data
        assert "recommendation" in data

    def test_analyze_unknown_program(self, client):
        resp = client.post(
            "/api/retail-redemptions/analyze",
            json={"program": "nonexistent", "points": 50000},
        )
        assert resp.status_code == 200
        assert "error" in resp.json()
