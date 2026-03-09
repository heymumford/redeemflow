"""Post-deploy smoke tests against a live URL.

Skipped by default unless SMOKE_BASE_URL is set.
Uses httpx for real HTTP calls (not FastAPI TestClient).
"""

from __future__ import annotations

import os

import httpx
import pytest

SMOKE_BASE_URL = os.environ.get("SMOKE_BASE_URL", "")

pytestmark = [
    pytest.mark.smoke,
    pytest.mark.skipif(not SMOKE_BASE_URL, reason="SMOKE_BASE_URL not set"),
]


@pytest.fixture
def smoke_client():
    return httpx.Client(base_url=SMOKE_BASE_URL, timeout=30.0)


class TestProductionSmoke:
    """Lightweight probes against the deployed service."""

    def test_health_returns_ok(self, smoke_client):
        resp = smoke_client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"

    def test_programs_returns_valid_json(self, smoke_client):
        resp = smoke_client.get("/api/programs")
        assert resp.status_code == 200
        body = resp.json()
        assert "programs" in body
        assert isinstance(body["programs"], list)

    def test_charity_states_returns_list(self, smoke_client):
        resp = smoke_client.get("/api/charities/states")
        assert resp.status_code == 200
        body = resp.json()
        assert "states" in body
        assert isinstance(body["states"], list)
        assert len(body["states"]) > 0
