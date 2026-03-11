"""Tests for saved searches."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from redeemflow.search.saved_searches import (
    SavedSearch,
    SavedSearchStore,
    SearchCriteria,
    reset_saved_search_store,
)


class TestSearchCriteria:
    def test_frozen(self):
        c = SearchCriteria(origin="SFO", destination="NRT")
        with pytest.raises(AttributeError):
            c.origin = "LAX"

    def test_defaults(self):
        c = SearchCriteria(origin="SFO", destination="NRT")
        assert c.cabin == "economy"
        assert c.programs == []
        assert c.max_points is None
        assert c.direct_only is False

    def test_full_criteria(self):
        c = SearchCriteria(
            origin="JFK",
            destination="LHR",
            cabin="business",
            programs=["united", "aa"],
            max_points=80000,
            direct_only=True,
        )
        assert c.origin == "JFK"
        assert len(c.programs) == 2
        assert c.max_points == 80000


class TestSavedSearchStore:
    def setup_method(self):
        self.store = SavedSearchStore()
        self.criteria = SearchCriteria(origin="SFO", destination="NRT", cabin="business")

    def test_save_search(self):
        s = self.store.save("user1", "SFO to Tokyo", self.criteria)
        assert isinstance(s, SavedSearch)
        assert s.search_id == "ss-1"
        assert s.user_id == "user1"
        assert s.name == "SFO to Tokyo"
        assert s.criteria == self.criteria
        assert s.is_active is True
        assert s.run_count == 0

    def test_list_searches(self):
        self.store.save("user1", "Search 1", self.criteria)
        self.store.save("user1", "Search 2", self.criteria)
        self.store.save("user2", "Other search", self.criteria)
        results = self.store.list_searches("user1")
        assert len(results) == 2

    def test_list_excludes_deleted(self):
        s = self.store.save("user1", "Search 1", self.criteria)
        self.store.delete(s.search_id, "user1")
        results = self.store.list_searches("user1")
        assert len(results) == 0

    def test_get_search(self):
        saved = self.store.save("user1", "My search", self.criteria)
        found = self.store.get(saved.search_id)
        assert found is not None
        assert found.name == "My search"

    def test_get_missing(self):
        assert self.store.get("ss-999") is None

    def test_record_run(self):
        saved = self.store.save("user1", "Recurring", self.criteria)
        updated = self.store.record_run(saved.search_id)
        assert updated is not None
        assert updated.run_count == 1
        assert updated.last_run_at != ""

    def test_record_run_increments(self):
        saved = self.store.save("user1", "Recurring", self.criteria)
        self.store.record_run(saved.search_id)
        updated = self.store.record_run(saved.search_id)
        assert updated is not None
        assert updated.run_count == 2

    def test_record_run_missing(self):
        assert self.store.record_run("ss-999") is None

    def test_delete_search(self):
        saved = self.store.save("user1", "To delete", self.criteria)
        deleted = self.store.delete(saved.search_id, "user1")
        assert deleted is not None
        assert deleted.is_active is False

    def test_delete_wrong_user(self):
        saved = self.store.save("user1", "Protected", self.criteria)
        assert self.store.delete(saved.search_id, "user2") is None

    def test_update_name(self):
        saved = self.store.save("user1", "Old name", self.criteria)
        renamed = self.store.update_name(saved.search_id, "user1", "New name")
        assert renamed is not None
        assert renamed.name == "New name"

    def test_update_name_wrong_user(self):
        saved = self.store.save("user1", "Protected", self.criteria)
        assert self.store.update_name(saved.search_id, "user2", "Stolen") is None

    def test_alert_searches(self):
        self.store.save("user1", "No alert", self.criteria)
        self.store.save("user1", "With alert", self.criteria, alert_on_change=True)
        alerts = self.store.alert_searches("user1")
        assert len(alerts) == 1
        assert alerts[0].alert_on_change is True

    def test_stats(self):
        s1 = self.store.save("user1", "S1", self.criteria)
        self.store.save("user1", "S2", self.criteria, alert_on_change=True)
        self.store.record_run(s1.search_id)
        self.store.record_run(s1.search_id)
        stats = self.store.stats("user1")
        assert stats["total_saved"] == 2
        assert stats["active"] == 2
        assert stats["total_runs"] == 2
        assert stats["alerts_enabled"] == 1

    def test_stats_empty_user(self):
        stats = self.store.stats("nobody")
        assert stats["total_saved"] == 0


class TestSavedSearchesAPI:
    AUTH_HEADERS = {"Authorization": "Bearer test-token-eric"}

    @pytest.fixture(autouse=True)
    def _reset(self):
        reset_saved_search_store()
        yield
        reset_saved_search_store()

    @pytest.fixture
    def client(self):
        from redeemflow.app import create_app
        from redeemflow.ports import PortBundle

        return TestClient(create_app(ports=PortBundle()))

    def test_save_search(self, client):
        resp = client.post(
            "/api/saved-searches",
            json={
                "name": "SFO to Tokyo",
                "origin": "SFO",
                "destination": "NRT",
                "cabin": "business",
            },
            headers=self.AUTH_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["search_id"].startswith("ss-")
        assert data["name"] == "SFO to Tokyo"

    def test_list_searches(self, client):
        client.post(
            "/api/saved-searches",
            json={"name": "S1", "origin": "SFO", "destination": "NRT"},
            headers=self.AUTH_HEADERS,
        )
        resp = client.get("/api/saved-searches", headers=self.AUTH_HEADERS)
        assert resp.status_code == 200
        assert len(resp.json()["searches"]) == 1

    def test_delete_search(self, client):
        r = client.post(
            "/api/saved-searches",
            json={"name": "Del", "origin": "JFK", "destination": "LHR"},
            headers=self.AUTH_HEADERS,
        )
        sid = r.json()["search_id"]
        resp = client.delete(f"/api/saved-searches/{sid}", headers=self.AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["search"]["is_active"] is False

    def test_requires_auth(self, client):
        resp = client.get("/api/saved-searches")
        assert resp.status_code == 401
