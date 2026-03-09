"""Slice 3+4: API integration — portfolio and recommendations endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from redeemflow.app import create_app


class TestPortfolioEndpoint:
    def setup_method(self):
        self.client = TestClient(create_app())

    def test_portfolio_requires_auth(self):
        response = self.client.get("/api/portfolio")
        assert response.status_code == 401

    def test_portfolio_returns_balances_with_valid_token(self):
        response = self.client.get(
            "/api/portfolio",
            headers={"Authorization": "Bearer test-token-eric"},
        )
        assert response.status_code == 200
        body = response.json()
        assert "balances" in body
        assert "total_value_dollars" in body

    def test_portfolio_balances_have_required_fields(self):
        response = self.client.get(
            "/api/portfolio",
            headers={"Authorization": "Bearer test-token-eric"},
        )
        body = response.json()
        for balance in body["balances"]:
            assert "program_code" in balance
            assert "points" in balance
            assert "estimated_value_dollars" in balance


class TestRecommendationsEndpoint:
    def setup_method(self):
        self.client = TestClient(create_app())

    def test_recommendations_requires_auth(self):
        response = self.client.get("/api/recommendations")
        assert response.status_code == 401

    def test_recommendations_returns_list(self):
        response = self.client.get(
            "/api/recommendations",
            headers={"Authorization": "Bearer test-token-eric"},
        )
        assert response.status_code == 200
        body = response.json()
        assert "recommendations" in body
        assert isinstance(body["recommendations"], list)

    def test_recommendations_have_required_fields(self):
        response = self.client.get(
            "/api/recommendations",
            headers={"Authorization": "Bearer test-token-eric"},
        )
        body = response.json()
        for rec in body["recommendations"]:
            assert "program_code" in rec
            assert "action" in rec
            assert "rationale" in rec
            assert "cpp_gain" in rec
