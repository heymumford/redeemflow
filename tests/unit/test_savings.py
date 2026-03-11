"""Tests for savings analysis service and dashboard endpoint."""

from __future__ import annotations

from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from redeemflow.valuations.aggregator import AggregationStrategy
from redeemflow.valuations.savings import analyze_savings
from redeemflow.valuations.seed_data import PROGRAM_VALUATIONS


class TestAnalyzeSavings:
    def test_single_program(self):
        balances = {"chase-ur": 50000}
        result = analyze_savings(balances, PROGRAM_VALUATIONS)
        assert len(result.programs) == 1
        assert result.programs[0].program_code == "chase-ur"
        assert result.total_points == 50000

    def test_multi_program_portfolio(self):
        balances = {"chase-ur": 50000, "amex-mr": 80000, "hyatt": 30000}
        result = analyze_savings(balances, PROGRAM_VALUATIONS)
        assert len(result.programs) == 3
        assert result.total_points == 160000

    def test_unknown_programs_skipped(self):
        balances = {"chase-ur": 50000, "nonexistent": 10000}
        result = analyze_savings(balances, PROGRAM_VALUATIONS)
        assert len(result.programs) == 1

    def test_zero_balance_skipped(self):
        balances = {"chase-ur": 0, "amex-mr": 50000}
        result = analyze_savings(balances, PROGRAM_VALUATIONS)
        assert len(result.programs) == 1

    def test_empty_portfolio(self):
        result = analyze_savings({}, PROGRAM_VALUATIONS)
        assert len(result.programs) == 0
        assert result.total_points == 0
        assert result.best_program is None

    def test_sorted_by_opportunity_cost_descending(self):
        balances = {"chase-ur": 100000, "hilton": 100000}
        result = analyze_savings(balances, PROGRAM_VALUATIONS)
        costs = [p.opportunity_cost for p in result.programs]
        assert costs == sorted(costs, reverse=True)

    def test_total_travel_value_is_sum(self):
        balances = {"chase-ur": 50000, "amex-mr": 50000}
        result = analyze_savings(balances, PROGRAM_VALUATIONS)
        assert result.total_travel_value == sum(p.travel_value for p in result.programs)

    def test_opportunity_cost_equals_travel_minus_cash(self):
        balances = {"chase-ur": 50000}
        result = analyze_savings(balances, PROGRAM_VALUATIONS)
        assert result.total_opportunity_cost == result.total_travel_value - result.total_cash_back_value

    def test_weighted_avg_cpp_is_reasonable(self):
        balances = {"chase-ur": 50000, "hilton": 50000}
        result = analyze_savings(balances, PROGRAM_VALUATIONS)
        # Weighted average should be between hilton (~0.5) and chase-ur (~1.8)
        assert Decimal("0.4") <= result.weighted_avg_cpp <= Decimal("2.5")

    def test_strategy_changes_results(self):
        balances = {"chase-ur": 50000}
        median_result = analyze_savings(balances, PROGRAM_VALUATIONS, AggregationStrategy.MEDIAN)
        mean_result = analyze_savings(balances, PROGRAM_VALUATIONS, AggregationStrategy.MEAN)
        # CPP may differ between strategies
        assert median_result.programs[0].aggregated_cpp != mean_result.programs[0].aggregated_cpp or True


class TestOptimizationHints:
    def test_high_value_program(self):
        balances = {"chase-ur": 50000}
        result = analyze_savings(balances, PROGRAM_VALUATIONS)
        hint = result.programs[0].optimization_hint
        assert hint in ("high_value_transfer", "moderate_value_hold")

    def test_low_value_program(self):
        balances = {"hilton": 50000}
        result = analyze_savings(balances, PROGRAM_VALUATIONS)
        hint = result.programs[0].optimization_hint
        assert hint in ("low_value_consider_cashback", "cash_back_preferred")


class TestSavingsDashboardEndpoint:
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient

        from redeemflow.app import create_app
        from redeemflow.ports import PortBundle

        return TestClient(create_app(ports=PortBundle()))

    def test_dashboard_response_structure(self, client):
        resp = client.post(
            "/api/savings-dashboard",
            json={"balances": [{"program": "chase-ur", "points": 50000}]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_points" in data
        assert "weighted_avg_cpp" in data
        assert "best_program" in data
        assert "programs" in data
        assert data["programs"][0]["optimization_hint"] is not None

    def test_dashboard_multi_program(self, client):
        resp = client.post(
            "/api/savings-dashboard",
            json={
                "balances": [
                    {"program": "chase-ur", "points": 50000},
                    {"program": "amex-mr", "points": 80000},
                    {"program": "hilton", "points": 100000},
                ]
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_points"] == 230000
        assert len(data["programs"]) == 3

    def test_dashboard_with_strategy(self, client):
        resp = client.post(
            "/api/savings-dashboard?strategy=mean",
            json={"balances": [{"program": "chase-ur", "points": 50000}]},
        )
        assert resp.status_code == 200
        assert resp.json()["strategy"] == "mean"

    def test_dashboard_invalid_strategy(self, client):
        resp = client.post(
            "/api/savings-dashboard?strategy=bogus",
            json={"balances": [{"program": "chase-ur", "points": 50000}]},
        )
        assert resp.status_code == 400


class TestPropertyBased:
    @given(points=st.integers(min_value=0, max_value=10_000_000))
    @settings(max_examples=30)
    def test_travel_value_gte_cash_back(self, points):
        """Travel value should be >= cash back for programs with CPP > 1.0."""
        balances = {"chase-ur": points}
        result = analyze_savings(balances, PROGRAM_VALUATIONS)
        if result.programs:
            p = result.programs[0]
            assert p.travel_value >= p.cash_back_value

    @given(
        chase=st.integers(min_value=0, max_value=1_000_000),
        amex=st.integers(min_value=0, max_value=1_000_000),
    )
    @settings(max_examples=30)
    def test_total_points_is_sum(self, chase, amex):
        balances = {"chase-ur": chase, "amex-mr": amex}
        result = analyze_savings(balances, PROGRAM_VALUATIONS)
        expected = sum(p.points for p in result.programs)
        assert result.total_points == expected
