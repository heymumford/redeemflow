"""Tests for API key management."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from redeemflow.identity.api_keys import APIKeyStore


class TestAPIKeyStore:
    def test_create_key(self):
        store = APIKeyStore()
        raw, key = store.create_key("user1", "My Key")
        assert raw.startswith("rf_")
        assert key.name == "My Key"
        assert key.user_id == "user1"
        assert key.is_active is True
        assert key.prefix == raw[:11]

    def test_raw_key_not_stored(self):
        store = APIKeyStore()
        raw, key = store.create_key("user1", "Key")
        assert raw not in str(key)

    def test_list_keys(self):
        store = APIKeyStore()
        store.create_key("user1", "Key A")
        store.create_key("user1", "Key B")
        store.create_key("user2", "Key C")
        assert len(store.list_keys("user1")) == 2
        assert len(store.list_keys("user2")) == 1

    def test_revoke_key(self):
        store = APIKeyStore()
        _, key = store.create_key("user1", "Key")
        revoked = store.revoke_key(key.key_id, "user1")
        assert revoked is not None
        assert revoked.is_active is False

    def test_revoke_wrong_user(self):
        store = APIKeyStore()
        _, key = store.create_key("user1", "Key")
        assert store.revoke_key(key.key_id, "user2") is None

    def test_revoke_nonexistent(self):
        store = APIKeyStore()
        assert store.revoke_key("nope", "user1") is None

    def test_validate_key(self):
        store = APIKeyStore()
        raw, _ = store.create_key("user1", "Key")
        validated = store.validate_key(raw)
        assert validated is not None
        assert validated.user_id == "user1"
        assert validated.last_used_at != ""

    def test_validate_revoked(self):
        store = APIKeyStore()
        raw, key = store.create_key("user1", "Key")
        store.revoke_key(key.key_id, "user1")
        assert store.validate_key(raw) is None

    def test_validate_invalid(self):
        store = APIKeyStore()
        assert store.validate_key("rf_bogus") is None

    def test_validate_expired(self):
        store = APIKeyStore()
        raw, _ = store.create_key("user1", "Key", expires_at="2020-01-01T00:00:00+00:00")
        assert store.validate_key(raw) is None

    def test_active_count(self):
        store = APIKeyStore()
        store.create_key("user1", "A")
        _, key_b = store.create_key("user1", "B")
        store.create_key("user1", "C")
        store.revoke_key(key_b.key_id, "user1")
        assert store.active_count("user1") == 2

    def test_scopes_default(self):
        store = APIKeyStore()
        _, key = store.create_key("user1", "Key")
        assert key.scopes == ["read"]

    def test_scopes_custom(self):
        store = APIKeyStore()
        _, key = store.create_key("user1", "Key", scopes=["read", "write", "admin"])
        assert key.scopes == ["read", "write", "admin"]

    def test_key_id_sequential(self):
        store = APIKeyStore()
        _, k1 = store.create_key("user1", "A")
        _, k2 = store.create_key("user1", "B")
        assert k1.key_id == "key-1"
        assert k2.key_id == "key-2"


class TestAPIKeysAPI:
    AUTH_HEADERS = {"Authorization": "Bearer test-token-eric"}

    @pytest.fixture
    def client(self):
        from redeemflow.app import create_app
        from redeemflow.identity.api_keys import reset_api_key_store
        from redeemflow.ports import PortBundle

        reset_api_key_store()
        return TestClient(create_app(ports=PortBundle()))

    def test_create_api_key(self, client):
        resp = client.post(
            "/api/keys",
            json={"name": "CI Pipeline"},
            headers=self.AUTH_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["raw_key"].startswith("rf_")
        assert data["key"]["name"] == "CI Pipeline"

    def test_list_keys(self, client):
        client.post("/api/keys", json={"name": "Key 1"}, headers=self.AUTH_HEADERS)
        client.post("/api/keys", json={"name": "Key 2"}, headers=self.AUTH_HEADERS)
        resp = client.get("/api/keys", headers=self.AUTH_HEADERS)
        assert resp.status_code == 200
        assert len(resp.json()["keys"]) == 2

    def test_revoke_key(self, client):
        create_resp = client.post("/api/keys", json={"name": "Temp"}, headers=self.AUTH_HEADERS)
        key_id = create_resp.json()["key"]["key_id"]
        resp = client.delete(f"/api/keys/{key_id}", headers=self.AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["key"]["is_active"] is False

    def test_keys_require_auth(self, client):
        assert client.get("/api/keys").status_code == 401
        assert client.post("/api/keys", json={"name": "X"}).status_code == 401
