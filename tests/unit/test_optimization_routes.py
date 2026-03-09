"""Tests for Sprint 3 optimization and search API routes."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from redeemflow.app import create_app


@pytest.fixture()
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


AUTH_HEADER = {"Authorization": "Bearer test-token-eric"}


class TestOptimizeEndpoint:
    def test_requires_auth(self, client: TestClient) -> None:
        resp = client.post("/api/optimize")
        assert resp.status_code == 401

    def test_returns_actions_for_authenticated_user(self, client: TestClient) -> None:
        resp = client.post("/api/optimize", headers=AUTH_HEADER)
        assert resp.status_code == 200
        data = resp.json()
        assert "actions" in data
        assert isinstance(data["actions"], list)
        assert len(data["actions"]) > 0

    def test_action_fields(self, client: TestClient) -> None:
        resp = client.post("/api/optimize", headers=AUTH_HEADER)
        data = resp.json()
        action = data["actions"][0]
        assert "program_code" in action
        assert "action_type" in action
        assert "description" in action
        assert "estimated_value_gain" in action
        assert "urgency" in action
        assert "confidence" in action


class TestTimingAdviceEndpoint:
    def test_requires_auth(self, client: TestClient) -> None:
        resp = client.post("/api/timing-advice", json={"program_code": "chase-ur", "points": 95000})
        assert resp.status_code == 401

    def test_returns_advice_for_program(self, client: TestClient) -> None:
        resp = client.post(
            "/api/timing-advice",
            json={"program_code": "chase-ur", "points": 95000},
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "advice" in data
        assert data["advice"]["program_code"] == "chase-ur"
        assert data["advice"]["recommendation"] in ("burn", "bank", "transfer")


class TestAlertsEndpoint:
    def test_requires_auth(self, client: TestClient) -> None:
        resp = client.get("/api/alerts")
        assert resp.status_code == 401

    def test_returns_alerts_for_authenticated_user(self, client: TestClient) -> None:
        resp = client.get("/api/alerts", headers=AUTH_HEADER)
        assert resp.status_code == 200
        data = resp.json()
        assert "alerts" in data
        assert isinstance(data["alerts"], list)


class TestAwardSearchEndpoint:
    def test_requires_auth(self, client: TestClient) -> None:
        resp = client.post(
            "/api/award-search",
            json={"origin": "SFO", "destination": "NRT", "date": "2026-06-15", "cabin": "business"},
        )
        assert resp.status_code == 401

    def test_returns_results_for_known_route(self, client: TestClient) -> None:
        resp = client.post(
            "/api/award-search",
            json={"origin": "SFO", "destination": "NRT", "date": "2026-06-15", "cabin": "business"},
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert isinstance(data["results"], list)

    def test_unknown_route_returns_empty_results(self, client: TestClient) -> None:
        resp = client.post(
            "/api/award-search",
            json={"origin": "XXX", "destination": "YYY", "date": "2026-06-15", "cabin": "economy"},
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["results"] == []
