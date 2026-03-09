"""E2E test: complete free-tier user journey.

Verifies the unauthenticated path through the API —
browse programs, calculate valuations, explore charities, check health.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from redeemflow.app import create_app


@pytest.fixture
def client():
    return TestClient(create_app())


@pytest.mark.e2e
class TestFreeTierFlow:
    """Walk a free-tier user through the complete unauthenticated journey."""

    def test_list_programs_returns_program_list(self, client):
        resp = client.get("/api/programs")
        assert resp.status_code == 200
        body = resp.json()
        assert "programs" in body
        assert isinstance(body["programs"], list)
        assert len(body["programs"]) > 0
        # Each program has required fields
        program = body["programs"][0]
        assert "code" in program
        assert "name" in program
        assert "median_cpp" in program

    def test_calculate_valuation_with_valid_payload(self, client):
        resp = client.post(
            "/api/calculate",
            json={"program": "chase-ur", "points": 50000},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["program"] == "chase-ur"
        assert body["points"] == 50000
        assert "min_value" in body
        assert "max_value" in body
        assert "median_value" in body
        assert "cash_back_value" in body
        assert "opportunity_cost" in body
        assert "valuations" in body

    def test_charities_filtered_by_state(self, client):
        resp = client.get("/api/charities?state=CA")
        assert resp.status_code == 200
        body = resp.json()
        assert "charities" in body
        assert isinstance(body["charities"], list)
        assert "total" in body
        assert "page" in body
        # All returned charities should be in CA
        for charity in body["charities"]:
            assert charity["state"] == "CA"

    def test_charity_categories_returns_list(self, client):
        resp = client.get("/api/charities/categories")
        assert resp.status_code == 200
        body = resp.json()
        assert "categories" in body
        assert isinstance(body["categories"], list)
        assert len(body["categories"]) > 0
        cat = body["categories"][0]
        assert "category" in cat
        assert "count" in cat

    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert "version" in body
