"""Community pool API route tests — TDD: written before implementation.

Tests the community pool REST endpoints via the FastAPI test client.
"""

from __future__ import annotations


import pytest
from fastapi.testclient import TestClient

from redeemflow.app import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


@pytest.fixture
def pro_headers():
    return {"Authorization": "Bearer test-token-eric"}


@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test-token-steve"}


class TestCreatePool:
    def test_create_pool_success(self, client, pro_headers):
        resp = client.post(
            "/api/pools",
            json={
                "name": "Girl Scout Drive",
                "target_charity_name": "Girl Scouts of the USA",
                "target_charity_state": "TX",
                "goal_amount": "500.00",
            },
            headers=pro_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["pool"]["name"] == "Girl Scout Drive"
        assert data["pool"]["status"] == "open"

    def test_create_pool_requires_auth(self, client):
        resp = client.post(
            "/api/pools",
            json={
                "name": "Girl Scout Drive",
                "target_charity_name": "Girl Scouts of the USA",
                "target_charity_state": "TX",
                "goal_amount": "500.00",
            },
        )
        assert resp.status_code == 401


class TestPledgeToPool:
    def test_pledge_success(self, client, pro_headers, auth_headers):
        # Create pool first
        resp = client.post(
            "/api/pools",
            json={
                "name": "Girl Scout Drive",
                "target_charity_name": "Girl Scouts of the USA",
                "target_charity_state": "TX",
                "goal_amount": "500.00",
            },
            headers=pro_headers,
        )
        pool_id = resp.json()["pool"]["id"]

        # Pledge to pool
        resp = client.post(
            f"/api/pools/{pool_id}/pledge",
            json={"program_code": "chase-ur", "points": 10000},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["pledge"]["points_pledged"] == 10000

    def test_pledge_requires_auth(self, client):
        resp = client.post(
            "/api/pools/some-pool-id/pledge",
            json={"program_code": "chase-ur", "points": 10000},
        )
        assert resp.status_code == 401


class TestListPools:
    def test_list_pools_no_auth(self, client):
        resp = client.get("/api/pools")
        assert resp.status_code == 200
        assert "pools" in resp.json()

    def test_list_pools_after_creation(self, client, pro_headers):
        client.post(
            "/api/pools",
            json={
                "name": "Pool A",
                "target_charity_name": "Girl Scouts of the USA",
                "target_charity_state": "TX",
                "goal_amount": "100.00",
            },
            headers=pro_headers,
        )
        resp = client.get("/api/pools")
        assert resp.status_code == 200
        assert len(resp.json()["pools"]) >= 1


class TestGetPool:
    def test_get_pool_detail(self, client, pro_headers):
        resp = client.post(
            "/api/pools",
            json={
                "name": "Pool A",
                "target_charity_name": "Girl Scouts of the USA",
                "target_charity_state": "TX",
                "goal_amount": "100.00",
            },
            headers=pro_headers,
        )
        pool_id = resp.json()["pool"]["id"]

        resp = client.get(f"/api/pools/{pool_id}")
        assert resp.status_code == 200
        assert resp.json()["pool"]["id"] == pool_id

    def test_get_pool_not_found(self, client):
        resp = client.get("/api/pools/nonexistent-id")
        assert resp.status_code == 404


class TestCompletePool:
    def test_complete_pool_goal_not_met(self, client, pro_headers):
        resp = client.post(
            "/api/pools",
            json={
                "name": "Big Pool",
                "target_charity_name": "Girl Scouts of the USA",
                "target_charity_state": "TX",
                "goal_amount": "999999.00",
            },
            headers=pro_headers,
        )
        pool_id = resp.json()["pool"]["id"]

        resp = client.post(f"/api/pools/{pool_id}/complete", headers=pro_headers)
        assert resp.status_code == 400

    def test_complete_pool_requires_auth(self, client):
        resp = client.post("/api/pools/some-pool-id/complete")
        assert resp.status_code == 401
