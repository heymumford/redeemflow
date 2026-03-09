"""E2E test: community features journey.

Verifies pool creation, pledging, forum posting,
and founders network application flow end-to-end.
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
class TestCommunityFlow:
    """Walk through community features: pools, forum, founders network."""

    def test_create_pool(self, client, auth_headers):
        resp = client.post(
            "/api/pools",
            json={
                "name": "E2E Test Pool",
                "target_charity_name": "Girl Scouts of the USA",
                "target_charity_state": "TX",
                "goal_amount": "250.00",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "pool" in body
        pool = body["pool"]
        assert pool["name"] == "E2E Test Pool"
        assert pool["status"] == "open"
        assert pool["goal_amount"] == "250.00"
        assert "id" in pool

    def test_pool_appears_in_list(self, client, auth_headers):
        # Create a pool
        create_resp = client.post(
            "/api/pools",
            json={
                "name": "Visible Pool",
                "target_charity_name": "Girl Scouts of the USA",
                "target_charity_state": "TX",
                "goal_amount": "100.00",
            },
            headers=auth_headers,
        )
        pool_id = create_resp.json()["pool"]["id"]

        # Verify it appears in the list
        resp = client.get("/api/pools")
        assert resp.status_code == 200
        body = resp.json()
        assert "pools" in body
        pool_ids = [p["id"] for p in body["pools"]]
        assert pool_id in pool_ids

    def test_pledge_to_pool(self, client, auth_headers):
        # Create a pool first
        create_resp = client.post(
            "/api/pools",
            json={
                "name": "Pledge Target",
                "target_charity_name": "Girl Scouts of the USA",
                "target_charity_state": "TX",
                "goal_amount": "500.00",
            },
            headers=auth_headers,
        )
        pool_id = create_resp.json()["pool"]["id"]

        # Pledge to it
        resp = client.post(
            f"/api/pools/{pool_id}/pledge",
            json={"program_code": "chase-ur", "points": 10000},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "pledge" in body
        pledge = body["pledge"]
        assert pledge["pool_id"] == pool_id
        assert pledge["points_pledged"] == 10000
        assert pledge["program_code"] == "chase-ur"
        assert "dollar_value" in pledge

    def test_create_forum_post(self, client, auth_headers):
        resp = client.post(
            "/api/forum/posts",
            json={
                "category": "strategies",
                "title": "E2E Forum Test",
                "content": "Testing the community forum flow.",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "post" in body
        post = body["post"]
        assert post["title"] == "E2E Forum Test"
        assert post["category"] == "strategies"
        assert post["author_name"] == "Eric"
        assert "id" in post

    def test_forum_post_appears_in_list(self, client, auth_headers):
        # Create a post
        create_resp = client.post(
            "/api/forum/posts",
            json={
                "category": "deals",
                "title": "Visible Post",
                "content": "Should appear in listing.",
            },
            headers=auth_headers,
        )
        post_id = create_resp.json()["post"]["id"]

        # Verify it appears
        resp = client.get("/api/forum/posts")
        assert resp.status_code == 200
        body = resp.json()
        assert "posts" in body
        post_ids = [p["id"] for p in body["posts"]]
        assert post_id in post_ids

    def test_founders_apply(self, client, auth_headers):
        resp = client.post(
            "/api/founders/apply",
            json={
                "company_name": "E2E Corp",
                "verification_source": "NAWBO",
                "bio": "E2E test founder.",
                "travel_interests": ["Tokyo", "Berlin"],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "profile" in body
        profile = body["profile"]
        assert profile["user_id"] == "auth0|eric"
        assert profile["company_name"] == "E2E Corp"
        assert profile["status"] == "pending"

    def test_founders_member_appears_after_verify(self, client, auth_headers):
        # Apply
        client.post(
            "/api/founders/apply",
            json={
                "company_name": "Verified Corp",
                "verification_source": "WBENC",
                "bio": "Will be verified.",
                "travel_interests": ["London"],
            },
            headers=auth_headers,
        )

        # Verify
        client.post("/api/founders/verify/auth0|eric", headers=auth_headers)

        # Check member list
        resp = client.get("/api/founders/members")
        assert resp.status_code == 200
        body = resp.json()
        assert "members" in body
        assert len(body["members"]) >= 1
        user_ids = [m["user_id"] for m in body["members"]]
        assert "auth0|eric" in user_ids
