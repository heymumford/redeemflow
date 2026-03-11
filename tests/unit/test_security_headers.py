"""Verify security headers are present on all responses."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from redeemflow.app import create_app
from redeemflow.ports import PortBundle


@pytest.fixture
def client():
    app = create_app(ports=PortBundle())
    return TestClient(app)


class TestSecurityHeaders:
    """OWASP-recommended security headers on every response."""

    def test_x_content_type_options(self, client):
        resp = client.get("/health")
        assert resp.headers.get("x-content-type-options") == "nosniff"

    def test_x_frame_options(self, client):
        resp = client.get("/health")
        assert resp.headers.get("x-frame-options") == "DENY"

    def test_referrer_policy(self, client):
        resp = client.get("/health")
        assert resp.headers.get("referrer-policy") == "strict-origin-when-cross-origin"

    def test_permissions_policy(self, client):
        resp = client.get("/health")
        policy = resp.headers.get("permissions-policy")
        assert "camera=()" in policy
        assert "microphone=()" in policy

    def test_server_header_stripped(self, client):
        resp = client.get("/health")
        # FastAPI/uvicorn may or may not set this, but our middleware strips it
        assert "server" not in {k.lower() for k in resp.headers}
