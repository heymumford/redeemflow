"""Tests for production hardening middleware — CORS, rate limiting, logging, error boundary.

Beck: Test the behavior at the HTTP boundary, not internal wiring.
Fowler: Each middleware is independently verifiable.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from redeemflow.app import create_app


@pytest.fixture()
def client():
    return TestClient(create_app())


@pytest.fixture()
def auth_headers():
    return {"Authorization": "Bearer test-token-eric"}


class TestCORS:
    """PH-01: CORS middleware allows configured origins."""

    def test_preflight_returns_cors_headers(self, client):
        resp = client.options(
            "/api/programs",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.status_code == 200
        assert "access-control-allow-origin" in resp.headers

    def test_cors_allows_localhost_3000(self, client):
        resp = client.get("/api/programs", headers={"Origin": "http://localhost:3000"})
        assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"

    def test_cors_rejects_unknown_origin(self, client):
        resp = client.get("/api/programs", headers={"Origin": "http://evil.com"})
        # FastAPI CORS middleware doesn't set the header for disallowed origins
        assert resp.headers.get("access-control-allow-origin") is None

    def test_cors_exposes_request_id(self, client):
        resp = client.get("/health", headers={"Origin": "http://localhost:3000"})
        assert "x-request-id" in resp.headers.get("access-control-expose-headers", "").lower()


class TestDeepHealthCheck:
    """PH-05: Health check probes dependencies."""

    def test_health_returns_version(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["version"] == "0.2.0"

    def test_health_includes_dependencies(self, client):
        resp = client.get("/health")
        body = resp.json()
        assert "dependencies" in body
        assert "database" in body["dependencies"]

    def test_health_status_ok_without_database(self, client):
        resp = client.get("/health")
        body = resp.json()
        assert body["status"] == "ok"
        assert body["dependencies"]["database"] == "not_configured"


class TestGlobalErrorBoundary:
    """PH-06: Unhandled exceptions return structured JSON."""

    def test_auth_error_returns_401(self, client):
        resp = client.get("/api/portfolio")
        assert resp.status_code == 401
        body = resp.json()
        assert "detail" in body

    def test_auth_error_is_json(self, client):
        resp = client.get("/api/portfolio")
        assert resp.headers["content-type"] == "application/json"


class TestRequestIdPropagation:
    """PH-03: Request ID flows through middleware to response."""

    def test_response_contains_request_id(self, client):
        resp = client.get("/health")
        assert "x-request-id" in resp.headers

    def test_custom_request_id_preserved(self, client):
        resp = client.get("/health", headers={"X-Request-Id": "test-req-42"})
        assert resp.headers["x-request-id"] == "test-req-42"


class TestAdapterFactory:
    """IP-05: Env-based adapter dispatch — fakes by default."""

    def test_default_adapters_are_fakes(self, client, auth_headers):
        # Portfolio works with FakeBalanceFetcher (no env vars needed)
        resp = client.get("/api/portfolio", headers=auth_headers)
        assert resp.status_code == 200

    def test_donation_works_with_fake_provider(self, client, auth_headers):
        resp = client.post(
            "/api/donate",
            json={
                "program_code": "chase-ur",
                "points": 5000,
                "charity_name": "Girl Scouts of the USA",
                "charity_state": "TX",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_billing_works_with_fake_provider(self, client, auth_headers):
        resp = client.get("/api/billing/subscription", headers=auth_headers)
        # Returns subscription or null — either way, 200
        assert resp.status_code == 200


class TestStructuredLogging:
    """PH-03: Verify structured logging module is importable and functional."""

    def test_configure_logging_succeeds(self):
        from redeemflow.middleware.logging import configure_logging

        # Should not raise
        configure_logging()

    def test_get_logger_returns_bound_logger(self):
        from redeemflow.middleware.logging import get_logger

        logger = get_logger("test")
        assert logger is not None

    def test_logger_with_no_name(self):
        from redeemflow.middleware.logging import get_logger

        logger = get_logger()
        assert logger is not None
