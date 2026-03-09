"""Slice 1: Walking skeleton — health endpoint proves the app boots."""

from __future__ import annotations

from fastapi.testclient import TestClient

from redeemflow.app import create_app


class TestHealthEndpoint:
    def test_health_returns_200(self):
        client = TestClient(create_app())
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_status_ok(self):
        client = TestClient(create_app())
        body = client.get("/health").json()
        assert body["status"] == "ok"

    def test_health_returns_version(self):
        client = TestClient(create_app())
        body = client.get("/health").json()
        assert "version" in body
