"""Tests for landing page server endpoints and behavior."""

from __future__ import annotations

import os
import sys

import pytest
from httpx import ASGITransport, AsyncClient

# Ensure the landing module is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "landing"))

os.environ.setdefault("DB_PATH", "")
os.environ.setdefault("SESSION_SECRET", "test-secret-key-for-testing-only")


@pytest.fixture()
def _temp_db(tmp_path):
    db_path = str(tmp_path / "test_signups.db")
    os.environ["DB_PATH"] = db_path
    import landing.server as srv

    srv.DB_PATH = db_path
    yield db_path


@pytest.fixture()
async def client(_temp_db):
    import landing.server as srv

    transport = ASGITransport(app=srv.app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHealth:
    async def test_health_returns_ok(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.text == "ok"


class TestVersion:
    async def test_version_returns_json(self, client):
        resp = await client.get("/api/version")
        assert resp.status_code == 200
        data = resp.json()
        assert "version" in data
        assert "otel" in data


class TestSignup:
    async def test_valid_email_signup(self, client):
        resp = await client.post("/api/signup", json={"email": "test@example.com"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "on the list" in data["message"].lower()

    async def test_duplicate_email_signup(self, client):
        await client.post("/api/signup", json={"email": "dupe@example.com"})
        resp = await client.post("/api/signup", json={"email": "dupe@example.com"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "already" in data["message"].lower()

    async def test_invalid_email_rejected(self, client):
        resp = await client.post("/api/signup", json={"email": "not-an-email"})
        assert resp.status_code == 400
        data = resp.json()
        assert "error" in data

    async def test_empty_email_rejected(self, client):
        resp = await client.post("/api/signup", json={"email": ""})
        assert resp.status_code == 400

    async def test_email_normalized_to_lowercase(self, client):
        resp = await client.post("/api/signup", json={"email": "Test@EXAMPLE.com"})
        assert resp.status_code == 200
        # Second signup with lowercase should be duplicate
        resp2 = await client.post("/api/signup", json={"email": "test@example.com"})
        assert "already" in resp2.json()["message"].lower()


class TestAdmin:
    async def test_signups_requires_auth(self, client):
        resp = await client.get("/api/signups")
        # Without ADMIN_TOKEN set, returns 403
        assert resp.status_code in (401, 403)

    async def test_users_requires_auth(self, client):
        resp = await client.get("/api/users")
        assert resp.status_code in (401, 403)


class TestIndex:
    async def test_index_returns_html(self, client):
        resp = await client.get("/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")


class TestSecurityHeaders:
    async def test_security_headers_present(self, client):
        resp = await client.get("/health")
        assert resp.headers.get("x-frame-options") == "DENY"
        assert resp.headers.get("x-content-type-options") == "nosniff"
        assert "content-security-policy" in resp.headers


class TestSessionHelpers:
    def test_sign_and_verify_roundtrip(self):
        import landing.server as srv

        user = {"sub": "test|123", "email": "a@b.com", "name": "Test", "picture": "", "provider": "test"}
        cookie = srv._make_session_cookie(user, max_age=3600)
        session = srv._verify(cookie)
        assert session is not None
        assert session["email"] == "a@b.com"
        assert session["sub"] == "test|123"

    def test_verify_rejects_tampered_token(self):
        import landing.server as srv

        user = {"sub": "test|123", "email": "a@b.com", "name": "Test", "picture": "", "provider": "test"}
        cookie = srv._make_session_cookie(user, max_age=3600)
        # Tamper with the signature
        parts = cookie.split(".")
        tampered = parts[0] + ".aaaa" + parts[1][4:]
        assert srv._verify(tampered) is None

    def test_verify_rejects_expired_token(self):
        import landing.server as srv

        user = {"sub": "test|123", "email": "a@b.com", "name": "Test", "picture": "", "provider": "test"}
        cookie = srv._make_session_cookie(user, max_age=-1)
        assert srv._verify(cookie) is None


class TestLoginFlow:
    async def test_login_without_config_returns_503(self, client):
        import landing.server as srv

        orig_domain = srv.AUTH0_DOMAIN
        srv.AUTH0_DOMAIN = ""
        try:
            resp = await client.get("/login", follow_redirects=False)
            assert resp.status_code == 503
        finally:
            srv.AUTH0_DOMAIN = orig_domain

    async def test_callback_without_code_returns_400(self, client):
        resp = await client.get("/callback")
        assert resp.status_code == 400

    async def test_me_without_session_returns_null_user(self, client):
        resp = await client.get("/api/me")
        assert resp.status_code == 200
        assert resp.json()["user"] is None
