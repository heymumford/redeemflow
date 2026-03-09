"""Tests for landing page server endpoints and behavior."""

from __future__ import annotations

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

# Ensure the landing module is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "landing"))

os.environ.setdefault("DB_PATH", "")
os.environ.setdefault("SESSION_SECRET", "test-secret-key-for-testing-only-32chars!")


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

    async def test_overlength_email_rejected(self, client):
        long_email = "a" * 250 + "@b.com"
        resp = await client.post("/api/signup", json={"email": long_email})
        assert resp.status_code == 400


class TestAdmin:
    async def test_signups_requires_auth(self, client):
        resp = await client.get("/api/signups")
        # Without ADMIN_TOKEN set, returns 403
        assert resp.status_code in (401, 403)

    async def test_users_requires_auth(self, client):
        resp = await client.get("/api/users")
        assert resp.status_code in (401, 403)

    async def test_signups_with_valid_token(self, client):
        import landing.server as srv

        orig = srv.ADMIN_TOKEN
        srv.ADMIN_TOKEN = "test-admin-token-12345"
        try:
            # Create a signup first
            await client.post("/api/signup", json={"email": "admin-test@example.com"})
            resp = await client.get(
                "/api/signups",
                headers={"Authorization": "Bearer test-admin-token-12345"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "count" in data
            assert "signups" in data
            assert data["count"] >= 1
            assert any(s["email"] == "admin-test@example.com" for s in data["signups"])
        finally:
            srv.ADMIN_TOKEN = orig

    async def test_users_with_valid_token(self, client):
        import landing.server as srv

        orig = srv.ADMIN_TOKEN
        srv.ADMIN_TOKEN = "test-admin-token-12345"
        try:
            resp = await client.get(
                "/api/users",
                headers={"Authorization": "Bearer test-admin-token-12345"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "count" in data
            assert "users" in data
        finally:
            srv.ADMIN_TOKEN = orig

    async def test_admin_wrong_token_returns_401(self, client):
        import landing.server as srv

        orig = srv.ADMIN_TOKEN
        srv.ADMIN_TOKEN = "correct-token"
        try:
            resp = await client.get(
                "/api/signups",
                headers={"Authorization": "Bearer wrong-token"},
            )
            assert resp.status_code == 401
        finally:
            srv.ADMIN_TOKEN = orig


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

    async def test_hsts_header_present(self, client):
        resp = await client.get("/health")
        hsts = resp.headers.get("strict-transport-security", "")
        assert "max-age=" in hsts
        assert "includeSubDomains" in hsts

    async def test_csp_no_unsafe_inline_script(self, client):
        resp = await client.get("/health")
        csp = resp.headers.get("content-security-policy", "")
        # script-src should NOT contain unsafe-inline
        script_src = [part for part in csp.split(";") if "script-src" in part]
        assert script_src, "script-src directive missing from CSP"
        assert "'unsafe-inline'" not in script_src[0]


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

    async def test_callback_error_is_html_escaped(self, client):
        resp = await client.get("/callback?error=test&error_description=<script>alert(1)</script>")
        assert resp.status_code == 400
        body = resp.text
        assert "<script>" not in body
        assert "&lt;script&gt;" in body

    async def test_callback_happy_path_sets_session(self, client, _temp_db):
        import landing.server as srv

        # Set up Auth0 config
        orig_domain = srv.AUTH0_DOMAIN
        orig_client_id = srv.AUTH0_CLIENT_ID
        orig_client_secret = srv.AUTH0_CLIENT_SECRET
        orig_callback_url = srv.AUTH0_CALLBACK_URL

        srv.AUTH0_DOMAIN = "test.auth0.com"
        srv.AUTH0_CLIENT_ID = "test-client-id"
        srv.AUTH0_CLIENT_SECRET = "test-secret"
        srv.AUTH0_CALLBACK_URL = "http://test/callback"

        # Plant a known state
        test_state = "test-state-abc123"
        srv._pending_states[test_state] = {"nonce": "test-nonce", "ts": __import__("time").time()}

        # Mock Auth0 token and userinfo responses
        # Use MagicMock (not AsyncMock) because server calls .json() synchronously
        mock_token_resp = MagicMock()
        mock_token_resp.status_code = 200
        mock_token_resp.json.return_value = {"access_token": "mock-access-token", "id_token": "mock-id-token"}

        mock_profile_resp = MagicMock()
        mock_profile_resp.status_code = 200
        mock_profile_resp.json.return_value = {
            "sub": "google-oauth2|12345",
            "email": "user@example.com",
            "name": "Test User",
            "picture": "https://example.com/photo.jpg",
        }

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_token_resp
        mock_client.get.return_value = mock_profile_resp

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_client)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        try:
            with patch("httpx.AsyncClient", return_value=mock_ctx):
                resp = await client.get(
                    f"/callback?code=test-auth-code&state={test_state}",
                    follow_redirects=False,
                )
            assert resp.status_code == 302
            assert resp.headers.get("location") == "/"
            # Session cookie should be set
            cookies = resp.headers.get_list("set-cookie")
            assert any("session=" in c for c in cookies)
        finally:
            srv.AUTH0_DOMAIN = orig_domain
            srv.AUTH0_CLIENT_ID = orig_client_id
            srv.AUTH0_CLIENT_SECRET = orig_client_secret
            srv.AUTH0_CALLBACK_URL = orig_callback_url


class TestRobotsSitemap:
    async def test_robots_txt(self, client):
        import landing.server as srv

        resp = await client.get("/robots.txt")
        assert resp.status_code == 200
        assert "User-agent" in resp.text
        assert "Sitemap" in resp.text
        assert srv.SITE_URL in resp.text

    async def test_sitemap_xml(self, client):
        import landing.server as srv

        resp = await client.get("/sitemap.xml")
        assert resp.status_code == 200
        assert "urlset" in resp.text
        assert "application/xml" in resp.headers.get("content-type", "")
        assert srv.SITE_URL in resp.text

    async def test_app_js_served(self, client):
        resp = await client.get("/app.js")
        assert resp.status_code == 200
        assert "javascript" in resp.headers.get("content-type", "")
        assert "addEventListener" in resp.text
