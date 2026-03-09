"""API integration tests for community forum endpoints.

TDD: These tests define the HTTP contract for forum routes.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from redeemflow.app import create_app


class TestForumAPI:
    def setup_method(self):
        app = create_app()
        self.client = TestClient(app)
        self.auth_headers = {"Authorization": "Bearer test-token-eric"}

    def test_create_post(self):
        resp = self.client.post(
            "/api/forum/posts",
            json={
                "category": "strategies",
                "title": "Best Transfer Partners",
                "content": "Amex to ANA is the best value.",
            },
            headers=self.auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "post" in data
        assert data["post"]["title"] == "Best Transfer Partners"
        assert data["post"]["author_name"] == "Eric"
        assert data["post"]["category"] == "strategies"
        assert data["post"]["id"].startswith("post-")

    def test_create_post_requires_auth(self):
        resp = self.client.post(
            "/api/forum/posts",
            json={
                "category": "strategies",
                "title": "Test",
                "content": "Test",
            },
        )
        assert resp.status_code == 401

    def test_list_posts(self):
        # Create two posts
        self.client.post(
            "/api/forum/posts",
            json={"category": "strategies", "title": "Post 1", "content": "Content 1"},
            headers=self.auth_headers,
        )
        self.client.post(
            "/api/forum/posts",
            json={"category": "deals", "title": "Post 2", "content": "Content 2"},
            headers=self.auth_headers,
        )
        resp = self.client.get("/api/forum/posts")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["posts"]) == 2

    def test_list_posts_with_category_filter(self):
        self.client.post(
            "/api/forum/posts",
            json={"category": "strategies", "title": "Post 1", "content": "Content 1"},
            headers=self.auth_headers,
        )
        self.client.post(
            "/api/forum/posts",
            json={"category": "deals", "title": "Post 2", "content": "Content 2"},
            headers=self.auth_headers,
        )
        resp = self.client.get("/api/forum/posts?category=strategies")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["posts"]) == 1
        assert data["posts"][0]["category"] == "strategies"

    def test_list_posts_invalid_category_returns_400(self):
        resp = self.client.get("/api/forum/posts?category=invalid_category")
        assert resp.status_code == 400
        assert "Invalid category" in resp.json()["detail"]

    def test_get_post_detail(self):
        create_resp = self.client.post(
            "/api/forum/posts",
            json={"category": "general", "title": "Hello", "content": "World"},
            headers=self.auth_headers,
        )
        post_id = create_resp.json()["post"]["id"]

        # Add a reply
        self.client.post(
            f"/api/forum/posts/{post_id}/reply",
            json={"content": "Great post!"},
            headers={"Authorization": "Bearer test-token-steve"},
        )

        resp = self.client.get(f"/api/forum/posts/{post_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["post"]["id"] == post_id
        assert data["post"]["reply_count"] == 1
        assert len(data["post"]["replies"]) == 1

    def test_get_post_not_found(self):
        resp = self.client.get("/api/forum/posts/nonexistent")
        assert resp.status_code == 404

    def test_reply_to_post(self):
        create_resp = self.client.post(
            "/api/forum/posts",
            json={"category": "general", "title": "Hello", "content": "World"},
            headers=self.auth_headers,
        )
        post_id = create_resp.json()["post"]["id"]

        resp = self.client.post(
            f"/api/forum/posts/{post_id}/reply",
            json={"content": "Nice discussion!"},
            headers={"Authorization": "Bearer test-token-steve"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["reply"]["author_name"] == "Steve"
        assert data["reply"]["content"] == "Nice discussion!"

    def test_reply_requires_auth(self):
        resp = self.client.post(
            "/api/forum/posts/some-id/reply",
            json={"content": "test"},
        )
        assert resp.status_code == 401

    def test_upvote_post(self):
        create_resp = self.client.post(
            "/api/forum/posts",
            json={"category": "general", "title": "Hello", "content": "World"},
            headers=self.auth_headers,
        )
        post_id = create_resp.json()["post"]["id"]

        resp = self.client.post(
            f"/api/forum/posts/{post_id}/upvote",
            headers=self.auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["post"]["upvotes"] == 1

    def test_upvote_requires_auth(self):
        resp = self.client.post("/api/forum/posts/some-id/upvote")
        assert resp.status_code == 401

    def test_search_posts(self):
        self.client.post(
            "/api/forum/posts",
            json={"category": "strategies", "title": "Amex Transfer Tips", "content": "Content"},
            headers=self.auth_headers,
        )
        self.client.post(
            "/api/forum/posts",
            json={"category": "deals", "title": "Chase Deals", "content": "Other content"},
            headers=self.auth_headers,
        )

        resp = self.client.get("/api/forum/search?q=Amex")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["posts"]) == 1
        assert data["posts"][0]["title"] == "Amex Transfer Tips"

    def test_search_posts_empty_query(self):
        resp = self.client.get("/api/forum/search?q=")
        assert resp.status_code == 200
        assert resp.json()["posts"] == []
