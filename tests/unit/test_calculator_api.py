"""RED tests for the free-tier calculator API endpoints.

Beck: Test through the public API — that's the contract users depend on.
Fowler: Integration tests at the API boundary, unit tests in the domain.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from redeemflow.app import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


class TestPointsValueCalculator:
    def test_calculate_single_program(self, client):
        resp = client.post("/api/calculate", json={"program": "chase-ur", "points": 50000})
        assert resp.status_code == 200
        data = resp.json()
        assert "min_value" in data
        assert "max_value" in data
        assert "median_value" in data
        assert "cash_back_value" in data
        assert "opportunity_cost" in data
        assert float(data["median_value"]) > 0

    def test_calculate_unknown_program_returns_404(self, client):
        resp = client.post("/api/calculate", json={"program": "nonexistent", "points": 10000})
        assert resp.status_code == 404

    def test_calculate_zero_points(self, client):
        resp = client.post("/api/calculate", json={"program": "chase-ur", "points": 0})
        assert resp.status_code == 200
        data = resp.json()
        assert float(data["median_value"]) == 0

    def test_calculate_negative_points_rejected(self, client):
        resp = client.post("/api/calculate", json={"program": "chase-ur", "points": -100})
        assert resp.status_code == 422


class TestTransferExplorer:
    def test_get_transfers_for_chase_ur(self, client):
        resp = client.get("/api/transfers/chase-ur")
        assert resp.status_code == 200
        data = resp.json()
        assert "partners" in data
        assert len(data["partners"]) >= 5
        first = data["partners"][0]
        assert "target_program" in first
        assert "transfer_ratio" in first
        assert "effective_ratio" in first

    def test_get_transfers_for_unknown_program(self, client):
        resp = client.get("/api/transfers/nonexistent")
        assert resp.status_code == 404

    def test_get_all_programs(self, client):
        resp = client.get("/api/programs")
        assert resp.status_code == 200
        data = resp.json()
        assert "programs" in data
        codes = [p["code"] for p in data["programs"]]
        assert "chase-ur" in codes
        assert "amex-mr" in codes


class TestBestCardRecommender:
    def test_recommend_card_for_dining(self, client):
        resp = client.post("/api/recommend-card", json={"category": "dining", "monthly_spend": 500})
        assert resp.status_code == 200
        data = resp.json()
        assert "recommendations" in data
        assert len(data["recommendations"]) >= 1
        first = data["recommendations"][0]
        assert "card_name" in first
        assert "earn_rate" in first
        assert "monthly_points" in first
        assert "annual_value" in first

    def test_recommend_card_for_travel(self, client):
        resp = client.post("/api/recommend-card", json={"category": "travel", "monthly_spend": 1000})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["recommendations"]) >= 1


class TestSavingsDashboard:
    def test_savings_analysis(self, client):
        resp = client.post(
            "/api/savings",
            json={
                "balances": [
                    {"program": "chase-ur", "points": 50000},
                    {"program": "amex-mr", "points": 80000},
                ]
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_travel_value" in data
        assert "total_cash_back_value" in data
        assert "total_opportunity_cost" in data
        assert "programs" in data
        assert len(data["programs"]) == 2
        assert float(data["total_opportunity_cost"]) > 0

    def test_savings_empty_balances(self, client):
        resp = client.post("/api/savings", json={"balances": []})
        assert resp.status_code == 200
        data = resp.json()
        assert float(data["total_opportunity_cost"]) == 0


class TestFeeCalculator:
    def test_fee_analysis(self, client):
        resp = client.post(
            "/api/fee-analysis",
            json={
                "cards": ["chase-sapphire-reserve"],
                "annual_spend": {"travel": 5000, "dining": 6000, "other": 12000},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "cards" in data
        assert len(data["cards"]) == 1
        card = data["cards"][0]
        assert "card_name" in card
        assert "annual_fee" in card
        assert "credits_value" in card
        assert "points_earned" in card
        assert "points_value" in card
        assert "net_value" in card

    def test_fee_analysis_unknown_card(self, client):
        resp = client.post(
            "/api/fee-analysis",
            json={"cards": ["nonexistent-card"], "annual_spend": {"other": 10000}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["cards"]) == 0
