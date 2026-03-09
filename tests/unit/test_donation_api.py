"""Donation API endpoint tests — TDD: written before implementation.

Tests the REST API for donations and impact tracking.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from redeemflow.app import create_app


def _client() -> TestClient:
    return TestClient(create_app())


class TestDonateEndpoint:
    def test_donate_success(self):
        client = _client()
        resp = client.post(
            "/api/donate",
            json={
                "program_code": "chase-ur",
                "points": 10000,
                "charity_name": "Girl Scouts of the USA",
                "charity_state": "TX",
            },
            headers={"Authorization": "Bearer test-token-eric"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["donation"]["status"] == "completed"
        assert data["donation"]["charity_name"] == "Girl Scouts of the USA"
        assert data["donation"]["points_donated"] == 10000
        assert "dollar_value" in data["donation"]
        # Tax disclosure must be present
        assert "tax_notice" in data

    def test_donate_requires_auth(self):
        client = _client()
        resp = client.post(
            "/api/donate",
            json={
                "program_code": "chase-ur",
                "points": 10000,
                "charity_name": "Girl Scouts of the USA",
                "charity_state": "TX",
            },
        )
        assert resp.status_code == 401

    def test_donate_invalid_program(self):
        client = _client()
        resp = client.post(
            "/api/donate",
            json={
                "program_code": "nonexistent-program",
                "points": 10000,
                "charity_name": "Girl Scouts of the USA",
                "charity_state": "TX",
            },
            headers={"Authorization": "Bearer test-token-eric"},
        )
        assert resp.status_code == 400

    def test_donate_zero_points(self):
        client = _client()
        resp = client.post(
            "/api/donate",
            json={
                "program_code": "chase-ur",
                "points": 0,
                "charity_name": "Girl Scouts of the USA",
                "charity_state": "TX",
            },
            headers={"Authorization": "Bearer test-token-eric"},
        )
        assert resp.status_code == 400

    def test_donate_invalid_charity(self):
        client = _client()
        resp = client.post(
            "/api/donate",
            json={
                "program_code": "chase-ur",
                "points": 10000,
                "charity_name": "Nonexistent Charity XYZ",
                "charity_state": "TX",
            },
            headers={"Authorization": "Bearer test-token-eric"},
        )
        assert resp.status_code == 400


class TestDonationsHistoryEndpoint:
    def test_get_donations_returns_history(self):
        client = _client()
        # Make a donation first
        client.post(
            "/api/donate",
            json={
                "program_code": "chase-ur",
                "points": 10000,
                "charity_name": "Girl Scouts of the USA",
                "charity_state": "TX",
            },
            headers={"Authorization": "Bearer test-token-eric"},
        )
        resp = client.get(
            "/api/donations",
            headers={"Authorization": "Bearer test-token-eric"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["donations"]) >= 1

    def test_get_donations_requires_auth(self):
        client = _client()
        resp = client.get("/api/donations")
        assert resp.status_code == 401


class TestImpactEndpoints:
    def test_get_user_impact(self):
        client = _client()
        # Make a donation first
        client.post(
            "/api/donate",
            json={
                "program_code": "chase-ur",
                "points": 10000,
                "charity_name": "Girl Scouts of the USA",
                "charity_state": "TX",
            },
            headers={"Authorization": "Bearer test-token-eric"},
        )
        resp = client.get(
            "/api/impact",
            headers={"Authorization": "Bearer test-token-eric"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_donated" in data
        assert "donation_count" in data
        assert "charities_supported" in data

    def test_get_user_impact_requires_auth(self):
        client = _client()
        resp = client.get("/api/impact")
        assert resp.status_code == 401

    def test_get_community_impact_no_auth(self):
        client = _client()
        resp = client.get("/api/impact/community")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_donated" in data
        assert "total_donors" in data
        assert "total_donations" in data
