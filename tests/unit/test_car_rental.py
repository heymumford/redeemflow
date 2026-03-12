"""Tests for car rental redemption analysis."""

from __future__ import annotations

from decimal import Decimal

import pytest

from redeemflow.redemptions.car_rental import (
    CAR_RENTAL_REDEMPTIONS,
    analyze_car_rental,
    best_car_rental,
    find_car_rentals,
)


class TestCarRentalData:
    def test_chase_ur_has_rentals(self):
        rentals = find_car_rentals("chase-ur")
        assert len(rentals) >= 3

    def test_capital_one_has_rentals(self):
        rentals = find_car_rentals("capital-one")
        assert len(rentals) >= 2

    def test_unknown_program_returns_empty(self):
        rentals = find_car_rentals("nonexistent")
        assert rentals == []

    def test_all_rentals_have_positive_cpp(self):
        for rental in CAR_RENTAL_REDEMPTIONS:
            assert rental.cpp > Decimal("0")

    def test_best_rental_returns_highest_cpp(self):
        best = best_car_rental("chase-ur")
        assert best is not None
        all_chase = find_car_rentals("chase-ur")
        assert best.cpp == max(r.cpp for r in all_chase)


class TestAnalyzeCarRental:
    def test_analysis_returns_correct_totals(self):
        rentals = find_car_rentals("chase-ur")
        analysis = analyze_car_rental(rentals[0], days=5)
        assert analysis.total_points == rentals[0].points_per_day * 5
        assert analysis.total_cash_value == rentals[0].cash_equivalent_per_day * 5

    def test_recommendation_valid(self):
        best = best_car_rental("chase-ur")
        analysis = analyze_car_rental(best, days=3)
        assert analysis.recommendation in ("redeem_car", "acceptable", "use_elsewhere")
        assert len(analysis.rationale) > 0

    def test_high_alternative_cpp_recommends_elsewhere(self):
        best = best_car_rental("chase-ur")
        analysis = analyze_car_rental(best, days=3, alternative_cpp=Decimal("15.0"))
        assert analysis.recommendation == "use_elsewhere"

    def test_low_alternative_cpp_recommends_car(self):
        best = best_car_rental("chase-ur")
        analysis = analyze_car_rental(best, days=3, alternative_cpp=Decimal("0.5"))
        assert analysis.recommendation == "redeem_car"

    def test_value_ratio_computed(self):
        best = best_car_rental("amex-mr")
        analysis = analyze_car_rental(best, days=2)
        assert analysis.value_ratio > Decimal("0")


class TestAPIEndpoints:
    AUTH = {"Authorization": "Bearer test-token-eric"}

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient

        from redeemflow.app import create_app
        from redeemflow.ports import PortBundle

        return TestClient(create_app(ports=PortBundle()))

    def test_list_car_rentals(self, client):
        resp = client.get("/api/car-rentals/chase-ur", headers=self.AUTH)
        assert resp.status_code == 200
        data = resp.json()
        assert data["program"] == "chase-ur"
        assert data["count"] >= 3

    def test_list_unknown_program(self, client):
        resp = client.get("/api/car-rentals/nonexistent", headers=self.AUTH)
        assert resp.status_code == 200
        assert resp.json()["count"] == 0

    def test_analyze_car_rental(self, client):
        resp = client.post(
            "/api/car-rentals/analyze",
            json={"program": "chase-ur", "days": 5},
            headers=self.AUTH,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "recommendation" in data
        assert "total_points" in data

    def test_analyze_unknown_program(self, client):
        resp = client.post(
            "/api/car-rentals/analyze",
            json={"program": "nonexistent", "days": 3},
            headers=self.AUTH,
        )
        assert resp.status_code == 404
        assert "detail" in resp.json()

    def test_requires_auth(self, client):
        resp = client.get("/api/car-rentals/chase-ur")
        assert resp.status_code == 401
