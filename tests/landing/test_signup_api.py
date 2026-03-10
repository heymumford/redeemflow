"""API tests for the beta signup flow — no browser required.

Covers: valid signup, duplicate handling, validation errors, admin list, admin auth.
Run with: uv run pytest tests/landing/test_signup_api.py -x --tb=short -q
"""

from __future__ import annotations

import os
import sys

import pytest
from httpx import ASGITransport, AsyncClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "landing"))

os.environ.setdefault("DB_PATH", "")
os.environ.setdefault("SESSION_SECRET", "test-secret-key-for-testing-only-32chars!")
os.environ.setdefault("ADMIN_TOKEN", "test-admin-token-e2e")

ADMIN_TOKEN = "test-admin-token-e2e"


@pytest.fixture()
def _temp_db(tmp_path):
    db_path = str(tmp_path / "test_signups.db")
    os.environ["DB_PATH"] = db_path
    os.environ["ADMIN_TOKEN"] = ADMIN_TOKEN
    import landing.server as srv

    srv.DB_PATH = db_path
    srv.ADMIN_TOKEN = ADMIN_TOKEN
    yield db_path


@pytest.fixture()
async def client(_temp_db):
    import landing.server as srv

    transport = ASGITransport(app=srv.app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ── Signup Endpoint ───────────────────────────────────────────────────


@pytest.mark.asyncio
class TestSignupAPI:
    """POST /api/signup — email beta signup."""

    async def test_valid_email_returns_ok(self, client):
        resp = await client.post("/api/signup", json={"email": "user@example.com"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert "on the list" in body["message"].lower()

    async def test_duplicate_email_returns_ok_with_already_message(self, client):
        await client.post("/api/signup", json={"email": "dupe@example.com"})
        resp = await client.post("/api/signup", json={"email": "dupe@example.com"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert "already" in body["message"].lower()

    async def test_empty_email_returns_400(self, client):
        resp = await client.post("/api/signup", json={"email": ""})
        assert resp.status_code == 400
        body = resp.json()
        assert "error" in body

    async def test_invalid_email_no_at_returns_400(self, client):
        resp = await client.post("/api/signup", json={"email": "not-an-email"})
        assert resp.status_code == 400

    async def test_invalid_email_no_domain_returns_400(self, client):
        resp = await client.post("/api/signup", json={"email": "user@"})
        assert resp.status_code == 400

    async def test_email_too_long_returns_400(self, client):
        long_email = "a" * 250 + "@b.com"
        resp = await client.post("/api/signup", json={"email": long_email})
        assert resp.status_code == 400

    async def test_email_is_case_normalized(self, client):
        resp = await client.post("/api/signup", json={"email": "MiXeD@Example.COM"})
        assert resp.status_code == 200
        admin_resp = await client.get("/api/signups", headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
        emails = [s["email"] for s in admin_resp.json()["signups"]]
        assert "mixed@example.com" in emails

    async def test_email_is_whitespace_stripped(self, client):
        resp = await client.post("/api/signup", json={"email": "  padded@test.com  "})
        assert resp.status_code == 200
        admin_resp = await client.get("/api/signups", headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
        emails = [s["email"] for s in admin_resp.json()["signups"]]
        assert "padded@test.com" in emails

    async def test_signup_records_user_agent(self, client):
        await client.post(
            "/api/signup",
            json={"email": "ua@test.com"},
            headers={"User-Agent": "TestBrowser/1.0"},
        )
        admin_resp = await client.get("/api/signups", headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
        signup = next(s for s in admin_resp.json()["signups"] if s["email"] == "ua@test.com")
        assert "TestBrowser" in signup["user_agent"]

    async def test_signup_records_ip(self, client):
        await client.post("/api/signup", json={"email": "ip@test.com"})
        admin_resp = await client.get("/api/signups", headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
        signup = next(s for s in admin_resp.json()["signups"] if s["email"] == "ip@test.com")
        assert signup["ip"]


# ── Admin Endpoints ───────────────────────────────────────────────────


@pytest.mark.asyncio
class TestAdminAPI:
    """GET /api/signups, GET /api/users, GET /admin — admin access."""

    async def test_signups_without_token_returns_401(self, client):
        resp = await client.get("/api/signups")
        assert resp.status_code == 401

    async def test_signups_with_wrong_token_returns_401(self, client):
        resp = await client.get("/api/signups", headers={"Authorization": "Bearer wrong-token"})
        assert resp.status_code == 401

    async def test_signups_with_valid_token_returns_list(self, client):
        await client.post("/api/signup", json={"email": "listed@test.com"})
        resp = await client.get("/api/signups", headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] >= 1
        assert "signups" in body
        signup = body["signups"][0]
        assert "email" in signup
        assert "created_at" in signup
        assert "ip" in signup
        assert "user_agent" in signup

    async def test_signups_ordered_newest_first(self, client):
        await client.post("/api/signup", json={"email": "first@test.com"})
        await client.post("/api/signup", json={"email": "second@test.com"})
        resp = await client.get("/api/signups", headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
        signups = resp.json()["signups"]
        assert signups[0]["email"] == "second@test.com"
        assert signups[1]["email"] == "first@test.com"

    async def test_users_without_token_returns_401(self, client):
        resp = await client.get("/api/users")
        assert resp.status_code == 401

    async def test_users_with_valid_token_returns_list(self, client):
        resp = await client.get("/api/users", headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
        assert resp.status_code == 200
        body = resp.json()
        assert "count" in body
        assert "users" in body

    async def test_admin_dashboard_without_token_returns_401(self, client):
        resp = await client.get("/admin")
        assert resp.status_code == 401

    async def test_admin_dashboard_with_query_token_returns_200(self, client):
        resp = await client.get(f"/admin?token={ADMIN_TOKEN}")
        assert resp.status_code == 200
        text = resp.text
        assert "RedeemFlow Admin" in text
        assert "Email Signups" in text
        assert "Export CSV" in text

    async def test_admin_dashboard_with_header_token_returns_200(self, client):
        resp = await client.get("/admin", headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
        assert resp.status_code == 200


# ── Admin with no token configured ────────────────────────────────────


@pytest.mark.asyncio
class TestAdminNotConfigured:
    """Admin endpoints when ADMIN_TOKEN env var is empty."""

    @pytest.fixture(autouse=True)
    def _no_admin_token(self, _temp_db):
        import landing.server as srv

        original = srv.ADMIN_TOKEN
        srv.ADMIN_TOKEN = ""
        yield
        srv.ADMIN_TOKEN = original

    async def test_signups_returns_403_when_not_configured(self, client):
        resp = await client.get("/api/signups", headers={"Authorization": "Bearer anything"})
        assert resp.status_code == 403
        assert "not configured" in resp.json()["error"].lower()

    async def test_admin_dashboard_returns_401_when_not_configured(self, client):
        resp = await client.get("/admin?token=anything")
        assert resp.status_code == 401
