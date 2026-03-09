"""RED tests for the charity directory API endpoints.

Beck: Test the interface, not the implementation.
Fowler: Thin routes delegate to domain objects.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from redeemflow.app import create_app

ALL_STATES = {
    "AL",
    "AK",
    "AZ",
    "AR",
    "CA",
    "CO",
    "CT",
    "DE",
    "FL",
    "GA",
    "HI",
    "ID",
    "IL",
    "IN",
    "IA",
    "KS",
    "KY",
    "LA",
    "ME",
    "MD",
    "MA",
    "MI",
    "MN",
    "MS",
    "MO",
    "MT",
    "NE",
    "NV",
    "NH",
    "NJ",
    "NM",
    "NY",
    "NC",
    "ND",
    "OH",
    "OK",
    "OR",
    "PA",
    "RI",
    "SC",
    "SD",
    "TN",
    "TX",
    "UT",
    "VT",
    "VA",
    "WA",
    "WV",
    "WI",
    "WY",
    "DC",
}


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


class TestCharityDirectoryAPI:
    def test_list_charities_returns_paginated(self, client: TestClient):
        resp = client.get("/api/charities")
        assert resp.status_code == 200
        data = resp.json()
        assert "charities" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert len(data["charities"]) <= 50  # default page size
        assert data["total"] >= 510

    def test_list_charities_pagination(self, client: TestClient):
        resp = client.get("/api/charities?page=2&per_page=10")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["charities"]) == 10
        assert data["page"] == 2
        assert data["per_page"] == 10

    def test_filter_by_state(self, client: TestClient):
        resp = client.get("/api/charities?state=OH")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 10
        for c in data["charities"]:
            assert c["state"] == "OH"

    def test_filter_by_category(self, client: TestClient):
        resp = client.get("/api/charities?category=youth")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        for c in data["charities"]:
            assert c["category"] == "youth"

    def test_filter_by_state_and_category(self, client: TestClient):
        resp = client.get("/api/charities?state=OH&category=youth")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        for c in data["charities"]:
            assert c["state"] == "OH"
            assert c["category"] == "youth"

    def test_list_states_with_counts(self, client: TestClient):
        resp = client.get("/api/charities/states")
        assert resp.status_code == 200
        data = resp.json()
        assert "states" in data
        states = {s["state"] for s in data["states"]}
        assert len(states) >= 51
        for entry in data["states"]:
            assert "state" in entry
            assert "count" in entry
            assert entry["count"] >= 10

    def test_list_categories_with_counts(self, client: TestClient):
        resp = client.get("/api/charities/categories")
        assert resp.status_code == 200
        data = resp.json()
        assert "categories" in data
        assert len(data["categories"]) >= 7
        for entry in data["categories"]:
            assert "category" in entry
            assert "count" in entry

    def test_search_charities(self, client: TestClient):
        resp = client.get("/api/charities/search?q=girl+scouts")
        assert resp.status_code == 200
        data = resp.json()
        assert "charities" in data
        assert data["total"] >= 1
        # All results should relate to "girl scouts"
        for c in data["charities"]:
            text = (c["name"] + " " + (c.get("chapter_name") or "") + " " + (c.get("description") or "")).lower()
            assert "girl scouts" in text or "girl" in text

    def test_unknown_state_returns_empty(self, client: TestClient):
        resp = client.get("/api/charities?state=ZZ")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["charities"] == []

    def test_all_50_states_plus_dc_have_charities(self, client: TestClient):
        """Fitness test: every state covered by the API."""
        resp = client.get("/api/charities/states")
        data = resp.json()
        api_states = {s["state"] for s in data["states"]}
        assert ALL_STATES.issubset(api_states)
