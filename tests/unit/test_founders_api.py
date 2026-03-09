"""API integration tests for Women Founders Travel Network endpoints.

TDD: These tests define the HTTP contract for founders network routes.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from redeemflow.app import create_app


class TestFoundersAPI:
    def setup_method(self):
        app = create_app()
        self.client = TestClient(app)
        self.auth_headers = {"Authorization": "Bearer test-token-eric"}
        self.steve_headers = {"Authorization": "Bearer test-token-steve"}

    def test_apply_for_membership(self):
        resp = self.client.post(
            "/api/founders/apply",
            json={
                "company_name": "TravelCo",
                "verification_source": "NAWBO",
                "bio": "Passionate about travel rewards.",
                "travel_interests": ["Tokyo", "Paris"],
            },
            headers=self.auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["profile"]["user_id"] == "auth0|eric"
        assert data["profile"]["status"] == "pending"
        assert data["profile"]["company_name"] == "TravelCo"

    def test_apply_requires_auth(self):
        resp = self.client.post(
            "/api/founders/apply",
            json={
                "company_name": "TravelCo",
                "verification_source": "NAWBO",
                "bio": "Bio",
                "travel_interests": [],
            },
        )
        assert resp.status_code == 401

    def test_list_members(self):
        # Apply and verify a member
        self.client.post(
            "/api/founders/apply",
            json={
                "company_name": "Co1",
                "verification_source": "NAWBO",
                "bio": "Bio1",
                "travel_interests": ["Tokyo"],
            },
            headers=self.auth_headers,
        )
        self.client.post("/api/founders/verify/auth0|eric", headers=self.auth_headers)

        resp = self.client.get("/api/founders/members")
        assert resp.status_code == 200
        data = resp.json()
        # Only verified/active members shown by default
        assert len(data["members"]) == 1
        assert data["members"][0]["status"] == "active"

    def test_get_member_profile(self):
        self.client.post(
            "/api/founders/apply",
            json={
                "company_name": "TravelCo",
                "verification_source": "WBENC",
                "bio": "Builder",
                "travel_interests": ["Berlin"],
            },
            headers=self.auth_headers,
        )

        resp = self.client.get("/api/founders/members/auth0|eric")
        assert resp.status_code == 200
        data = resp.json()
        assert data["profile"]["name"] == "Eric"
        assert data["profile"]["company_name"] == "TravelCo"

    def test_get_member_profile_not_found(self):
        resp = self.client.get("/api/founders/members/nonexistent")
        assert resp.status_code == 404

    def test_verify_member(self):
        self.client.post(
            "/api/founders/apply",
            json={
                "company_name": "Co1",
                "verification_source": "SBA",
                "bio": "Bio",
                "travel_interests": [],
            },
            headers=self.auth_headers,
        )

        resp = self.client.post("/api/founders/verify/auth0|eric", headers=self.auth_headers)
        assert resp.status_code == 200
        assert resp.json()["profile"]["status"] == "active"

    def test_verify_requires_auth(self):
        resp = self.client.post("/api/founders/verify/auth0|eric")
        assert resp.status_code == 401

    def test_find_companions(self):
        self.client.post(
            "/api/founders/apply",
            json={
                "company_name": "Co1",
                "verification_source": "NAWBO",
                "bio": "Bio",
                "travel_interests": ["Tokyo", "Paris"],
            },
            headers=self.auth_headers,
        )
        self.client.post(
            "/api/founders/apply",
            json={
                "company_name": "Co2",
                "verification_source": "WBENC",
                "bio": "Bio",
                "travel_interests": ["London"],
            },
            headers=self.steve_headers,
        )

        resp = self.client.get("/api/founders/companions/Tokyo")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["companions"]) == 1
        assert data["companions"][0]["name"] == "Eric"

    def test_find_mentors(self):
        # Apply and set up mentor
        self.client.post(
            "/api/founders/apply",
            json={
                "company_name": "Co1",
                "verification_source": "NAWBO",
                "bio": "Bio",
                "travel_interests": ["Tokyo"],
                "is_mentor": True,
                "mentor_topics": ["fundraising", "travel hacking"],
            },
            headers=self.auth_headers,
        )

        resp = self.client.get("/api/founders/mentors/fundraising")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["mentors"]) == 1
        assert data["mentors"][0]["name"] == "Eric"
