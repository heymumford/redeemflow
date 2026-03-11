"""Tests for trip sharing."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from redeemflow.search.trip_sharing import SharePermission, TripShareStore


class TestTripShareStore:
    def test_create_share(self):
        store = TripShareStore()
        link = store.create_share("trip-1", "user1")
        assert link.trip_id == "trip-1"
        assert link.owner_id == "user1"
        assert link.permission == SharePermission.VIEW
        assert link.is_active is True
        assert len(link.token) > 10

    def test_create_edit_share(self):
        store = TripShareStore()
        link = store.create_share("trip-1", "user1", SharePermission.EDIT)
        assert link.permission == SharePermission.EDIT

    def test_get_by_token(self):
        store = TripShareStore()
        link = store.create_share("trip-1", "user1")
        found = store.get_by_token(link.token)
        assert found is not None
        assert found.share_id == link.share_id

    def test_get_invalid_token(self):
        store = TripShareStore()
        assert store.get_by_token("bogus") is None

    def test_get_expired_token(self):
        store = TripShareStore()
        link = store.create_share("trip-1", "user1", expires_at="2020-01-01T00:00:00+00:00")
        assert store.get_by_token(link.token) is None

    def test_record_view(self):
        store = TripShareStore()
        link = store.create_share("trip-1", "user1")
        updated = store.record_view(link.token)
        assert updated is not None
        assert updated.view_count == 1
        assert updated.last_viewed_at != ""

    def test_multiple_views(self):
        store = TripShareStore()
        link = store.create_share("trip-1", "user1")
        store.record_view(link.token)
        store.record_view(link.token)
        updated = store.record_view(link.token)
        assert updated is not None
        assert updated.view_count == 3

    def test_list_shares(self):
        store = TripShareStore()
        store.create_share("trip-1", "user1")
        store.create_share("trip-2", "user1")
        store.create_share("trip-3", "user2")
        assert len(store.list_shares("user1")) == 2
        assert len(store.list_shares("user2")) == 1

    def test_revoke_share(self):
        store = TripShareStore()
        link = store.create_share("trip-1", "user1")
        revoked = store.revoke_share(link.share_id, "user1")
        assert revoked is not None
        assert revoked.is_active is False
        assert store.get_by_token(link.token) is None

    def test_revoke_wrong_user(self):
        store = TripShareStore()
        link = store.create_share("trip-1", "user1")
        assert store.revoke_share(link.share_id, "user2") is None

    def test_revoke_nonexistent(self):
        store = TripShareStore()
        assert store.revoke_share("nope", "user1") is None

    def test_sharing_stats(self):
        store = TripShareStore()
        link1 = store.create_share("trip-1", "user1")
        store.create_share("trip-2", "user1")
        store.record_view(link1.token)
        store.record_view(link1.token)
        stats = store.sharing_stats("user1")
        assert stats["total_shares"] == 2
        assert stats["active_shares"] == 2
        assert stats["total_views"] == 2
        assert stats["most_viewed"] == link1.share_id

    def test_empty_stats(self):
        store = TripShareStore()
        stats = store.sharing_stats("user1")
        assert stats["total_shares"] == 0
        assert stats["most_viewed"] is None


class TestTripSharingAPI:
    AUTH_HEADERS = {"Authorization": "Bearer test-token-eric"}

    @pytest.fixture
    def client(self):
        from redeemflow.app import create_app
        from redeemflow.ports import PortBundle
        from redeemflow.search.trip_sharing import reset_trip_share_store

        reset_trip_share_store()
        return TestClient(create_app(ports=PortBundle()))

    def test_create_share(self, client):
        resp = client.post(
            "/api/trips/trip-1/share",
            json={"permission": "view"},
            headers=self.AUTH_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        assert data["share"]["permission"] == "view"

    def test_view_shared_trip(self, client):
        create_resp = client.post(
            "/api/trips/trip-1/share",
            json={},
            headers=self.AUTH_HEADERS,
        )
        token = create_resp.json()["token"]
        resp = client.get(f"/api/shared/{token}")
        assert resp.status_code == 200
        assert resp.json()["trip_id"] == "trip-1"

    def test_list_shares(self, client):
        client.post("/api/trips/trip-1/share", json={}, headers=self.AUTH_HEADERS)
        client.post("/api/trips/trip-2/share", json={}, headers=self.AUTH_HEADERS)
        resp = client.get("/api/shares", headers=self.AUTH_HEADERS)
        assert resp.status_code == 200
        assert len(resp.json()["shares"]) == 2

    def test_revoke_share(self, client):
        create_resp = client.post(
            "/api/trips/trip-1/share",
            json={},
            headers=self.AUTH_HEADERS,
        )
        share_id = create_resp.json()["share"]["share_id"]
        resp = client.delete(f"/api/shares/{share_id}", headers=self.AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["share"]["is_active"] is False

    def test_share_requires_auth(self, client):
        resp = client.post("/api/trips/trip-1/share", json={})
        assert resp.status_code == 401

    def test_shared_view_is_public(self, client):
        create_resp = client.post(
            "/api/trips/trip-1/share",
            json={},
            headers=self.AUTH_HEADERS,
        )
        token = create_resp.json()["token"]
        # No auth needed for viewing shared trips
        resp = client.get(f"/api/shared/{token}")
        assert resp.status_code == 200
