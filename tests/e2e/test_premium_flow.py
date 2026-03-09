"""E2E test: authenticated premium user journey.

Verifies portfolio, recommendations, optimization, alerts,
donation, and donation history for a logged-in user.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from redeemflow.app import create_app


@pytest.fixture
def client():
    return TestClient(create_app())


@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test-token-eric"}


@pytest.mark.e2e
class TestPremiumFlow:
    """Walk an authenticated user through the premium feature set."""

    def test_portfolio_returns_balances(self, client, auth_headers):
        resp = client.get("/api/portfolio", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "balances" in body
        assert isinstance(body["balances"], list)
        assert len(body["balances"]) > 0
        balance = body["balances"][0]
        assert "program_code" in balance
        assert "points" in balance
        assert "estimated_value_dollars" in balance
        assert "total_value_dollars" in body

    def test_recommendations_returns_list(self, client, auth_headers):
        resp = client.get("/api/recommendations", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "recommendations" in body
        assert isinstance(body["recommendations"], list)
        for rec in body["recommendations"]:
            assert "program_code" in rec
            assert "action" in rec
            assert "rationale" in rec
            assert "cpp_gain" in rec
            assert "points_involved" in rec

    def test_optimize_returns_actions(self, client, auth_headers):
        resp = client.post("/api/optimize", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "actions" in body
        assert isinstance(body["actions"], list)
        for action in body["actions"]:
            assert "program_code" in action
            assert "action_type" in action
            assert "description" in action
            assert "estimated_value_gain" in action

    def test_alerts_returns_list(self, client, auth_headers):
        resp = client.get("/api/alerts", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "alerts" in body
        assert isinstance(body["alerts"], list)
        for alert in body["alerts"]:
            assert "id" in alert
            assert "alert_type" in alert
            assert "priority" in alert
            assert "title" in alert
            assert "message" in alert

    def test_donate_creates_donation(self, client, auth_headers):
        resp = client.post(
            "/api/donate",
            json={
                "program_code": "chase-ur",
                "points": 5000,
                "charity_name": "Girl Scouts of the USA",
                "charity_state": "TX",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "donation" in body
        donation = body["donation"]
        assert donation["program_code"] == "chase-ur"
        assert donation["points_donated"] == 5000
        assert donation["charity_name"] == "Girl Scouts of the USA"
        assert "dollar_value" in donation
        assert "tax_notice" in body

    def test_donations_list_after_donate(self, client, auth_headers):
        # Create a donation first
        client.post(
            "/api/donate",
            json={
                "program_code": "chase-ur",
                "points": 1000,
                "charity_name": "Girl Scouts of the USA",
                "charity_state": "TX",
            },
            headers=auth_headers,
        )

        resp = client.get("/api/donations", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "donations" in body
        assert isinstance(body["donations"], list)
        assert len(body["donations"]) >= 1
        assert "tax_notice" in body
