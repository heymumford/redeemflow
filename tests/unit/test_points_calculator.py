"""Tests for points calculator."""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from redeemflow.optimization.points_calculator import (
    break_even,
    get_earn_rate,
    points_needed_for_value,
    project_earnings,
    value_of_points,
)


class TestGetEarnRate:
    def test_known_category(self):
        assert get_earn_rate("chase-ur", "dining") == Decimal("3")

    def test_default_category(self):
        assert get_earn_rate("chase-ur", "other") == Decimal("1")

    def test_unknown_program(self):
        assert get_earn_rate("unknown", "dining") == Decimal("1")

    def test_amex_travel(self):
        assert get_earn_rate("amex-mr", "travel") == Decimal("5")


class TestProjectEarnings:
    def test_basic_projection(self):
        proj = project_earnings("chase-ur", Decimal("1000"), "dining")
        assert proj.monthly_points == 3000
        assert proj.annual_points == 36000

    def test_months_to_target(self):
        proj = project_earnings("chase-ur", Decimal("1000"), "dining", target_points=9000)
        assert proj.months_to_target == 3

    def test_with_existing_points(self):
        proj = project_earnings("chase-ur", Decimal("1000"), "dining", target_points=9000, existing_points=3000)
        assert proj.months_to_target == 2

    def test_target_already_met(self):
        proj = project_earnings("chase-ur", Decimal("1000"), "dining", target_points=1000, existing_points=5000)
        assert proj.months_to_target == 0

    def test_no_target(self):
        proj = project_earnings("chase-ur", Decimal("500"), "other")
        assert proj.months_to_target == 0


class TestBreakEven:
    def test_worth_it(self):
        result = break_even("chase-ur", Decimal("550"), Decimal("3000"), "dining", Decimal("1.5"))
        # 3000 * 3 = 9000 pts/month, 108000/year, value = 108000 * 1.5 / 100 = $1620
        assert result.is_worth_it is True
        assert result.net_value > 0

    def test_not_worth_it(self):
        result = break_even("chase-ur", Decimal("550"), Decimal("100"), "other", Decimal("1.0"))
        # 100 * 1 = 100 pts/month, 1200/year, value = 1200 * 1.0 / 100 = $12
        assert result.is_worth_it is False
        assert result.net_value < 0

    def test_break_even_spend(self):
        result = break_even("chase-ur", Decimal("550"), Decimal("1000"), "dining", Decimal("1.5"))
        # BE: 550 * 100 / (3 * 12 * 1.5) = 55000 / 54 ≈ 1018.52
        assert result.break_even_monthly_spend > Decimal("0")
        assert result.break_even_monthly_spend < Decimal("2000")

    def test_annual_fee_zero(self):
        result = break_even("chase-ur", Decimal("0"), Decimal("1000"), "dining", Decimal("1.5"))
        assert result.is_worth_it is True


class TestPointsNeeded:
    def test_basic(self):
        needed = points_needed_for_value(Decimal("150"), Decimal("1.5"))
        assert needed == 10000

    def test_zero_cpp(self):
        assert points_needed_for_value(Decimal("100"), Decimal("0")) == 0


class TestValueOfPoints:
    def test_basic(self):
        value = value_of_points(10000, Decimal("1.5"))
        assert value == Decimal("150.00")

    def test_zero_points(self):
        assert value_of_points(0, Decimal("1.5")) == Decimal("0.00")


class TestPointsCalculatorAPI:
    AUTH_HEADERS = {"Authorization": "Bearer test-token-eric"}

    @pytest.fixture
    def client(self):
        from redeemflow.app import create_app
        from redeemflow.ports import PortBundle

        return TestClient(create_app(ports=PortBundle()))

    def test_project_earnings(self, client):
        resp = client.post(
            "/api/calculator/earnings",
            json={
                "program_code": "chase-ur",
                "monthly_spend": "2000",
                "category": "dining",
                "target_points": 50000,
            },
            headers=self.AUTH_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["monthly_points"] == 6000
        assert data["months_to_target"] > 0

    def test_break_even(self, client):
        resp = client.post(
            "/api/calculator/break-even",
            json={
                "program_code": "chase-ur",
                "annual_fee": "550",
                "monthly_spend": "3000",
                "category": "dining",
            },
            headers=self.AUTH_HEADERS,
        )
        assert resp.status_code == 200
        assert "is_worth_it" in resp.json()

    def test_calculator_requires_auth(self, client):
        resp = client.post("/api/calculator/earnings", json={"program_code": "chase-ur", "monthly_spend": "1000"})
        assert resp.status_code == 401
