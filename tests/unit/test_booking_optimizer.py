"""Tests for booking method optimizer — points vs cash decision engine."""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from redeemflow.optimization.booking_optimizer import (
    BookingAnalysis,
    PaymentMethod,
    analyze_booking,
)


class TestAnalyzeBooking:
    def test_cash_option_always_present(self):
        result = analyze_booking(
            cash_price=Decimal("500"),
            points_price=25000,
            program_code="united",
            program_cpp=Decimal("1.20"),
        )
        methods = [o.method for o in result.options]
        assert PaymentMethod.CASH_ONLY in methods

    def test_points_option_with_good_value(self):
        result = analyze_booking(
            cash_price=Decimal("3000"),
            points_price=60000,
            program_code="united",
            program_cpp=Decimal("1.20"),
            available_points=100000,
        )
        points_opt = next(o for o in result.options if o.method == PaymentMethod.POINTS_ONLY)
        assert points_opt.effective_cpp == Decimal("5.00")
        assert points_opt.value_score > Decimal("1.0")

    def test_recommends_points_when_good_value(self):
        result = analyze_booking(
            cash_price=Decimal("3000"),
            points_price=60000,
            program_code="united",
            program_cpp=Decimal("1.20"),
            available_points=100000,
        )
        assert result.recommended.method == PaymentMethod.POINTS_ONLY

    def test_recommends_cash_when_poor_value(self):
        result = analyze_booking(
            cash_price=Decimal("50"),
            points_price=25000,
            program_code="hilton",
            program_cpp=Decimal("0.50"),
            available_points=50000,
        )
        # 50/25000*100 = 0.20 cpp, baseline 0.50 = 0.40x value → cash recommended
        assert result.recommended.method == PaymentMethod.CASH_ONLY

    def test_mix_option_included(self):
        result = analyze_booking(
            cash_price=Decimal("1000"),
            points_price=50000,
            program_code="chase-ur",
            program_cpp=Decimal("1.80"),
        )
        methods = [o.method for o in result.options]
        assert PaymentMethod.POINTS_PLUS_CASH in methods

    def test_transfer_option(self):
        result = analyze_booking(
            cash_price=Decimal("2000"),
            points_price=50000,
            program_code="united",
            program_cpp=Decimal("1.20"),
            available_points=0,
            transfer_options=[{"source": "chase-ur", "ratio": 1, "source_cpp": "1.80"}],
        )
        xfer = next(o for o in result.options if o.method == PaymentMethod.TRANSFER_THEN_POINTS)
        assert xfer.program_code == "chase-ur"
        assert xfer.points_cost == 50000

    def test_multiple_transfer_options(self):
        result = analyze_booking(
            cash_price=Decimal("2000"),
            points_price=50000,
            program_code="united",
            program_cpp=Decimal("1.20"),
            transfer_options=[
                {"source": "chase-ur", "ratio": 1, "source_cpp": "1.80"},
                {"source": "amex-mr", "ratio": 1, "source_cpp": "1.80"},
            ],
        )
        xfer_opts = [o for o in result.options if o.method == PaymentMethod.TRANSFER_THEN_POINTS]
        assert len(xfer_opts) == 2

    def test_savings_vs_cash(self):
        result = analyze_booking(
            cash_price=Decimal("1000"),
            points_price=50000,
            program_code="hyatt",
            program_cpp=Decimal("1.70"),
            available_points=60000,
        )
        points_opt = next(o for o in result.options if o.method == PaymentMethod.POINTS_ONLY)
        assert points_opt.savings_vs_cash == Decimal("1000")

    def test_no_savings_if_insufficient_points(self):
        result = analyze_booking(
            cash_price=Decimal("1000"),
            points_price=50000,
            program_code="hyatt",
            program_cpp=Decimal("1.70"),
            available_points=10000,
        )
        points_opt = next(o for o in result.options if o.method == PaymentMethod.POINTS_ONLY)
        assert points_opt.savings_vs_cash == Decimal("0")

    def test_recommendation_has_reason(self):
        result = analyze_booking(
            cash_price=Decimal("500"),
            points_price=25000,
            program_code="united",
            program_cpp=Decimal("1.20"),
        )
        assert isinstance(result, BookingAnalysis)
        assert result.recommendation_reason != ""

    def test_zero_points_price(self):
        result = analyze_booking(
            cash_price=Decimal("500"),
            points_price=0,
            program_code="united",
            program_cpp=Decimal("1.20"),
        )
        # Only cash option
        assert len(result.options) == 1
        assert result.recommended.method == PaymentMethod.CASH_ONLY


class TestBookingAPI:
    AUTH_HEADERS = {"Authorization": "Bearer test-token-eric"}

    @pytest.fixture
    def client(self):
        from redeemflow.app import create_app
        from redeemflow.ports import PortBundle

        return TestClient(create_app(ports=PortBundle()))

    def test_booking_analysis(self, client):
        resp = client.post(
            "/api/booking-analysis",
            json={
                "cash_price": 3000,
                "points_price": 60000,
                "program_code": "united",
                "available_points": 100000,
            },
            headers=self.AUTH_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "recommendation" in data
        assert "options" in data
        assert len(data["options"]) >= 2

    def test_booking_with_transfers(self, client):
        resp = client.post(
            "/api/booking-analysis",
            json={
                "cash_price": 2000,
                "points_price": 50000,
                "program_code": "united",
                "transfers": [{"source": "chase-ur", "ratio": 1, "source_cpp": "1.80"}],
            },
            headers=self.AUTH_HEADERS,
        )
        data = resp.json()
        methods = [o["method"] for o in data["options"]]
        assert "transfer_then_points" in methods

    def test_unknown_program(self, client):
        resp = client.post(
            "/api/booking-analysis",
            json={"cash_price": 100, "points_price": 5000, "program_code": "nonexistent"},
            headers=self.AUTH_HEADERS,
        )
        assert resp.status_code == 404
        assert "detail" in resp.json()

    def test_requires_auth(self, client):
        resp = client.post(
            "/api/booking-analysis",
            json={"cash_price": 100, "points_price": 5000, "program_code": "united"},
        )
        assert resp.status_code == 401
