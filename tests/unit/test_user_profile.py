"""Tests for user profile management — preferences, linked accounts."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from redeemflow.identity.profile import (
    DisplayCurrency,
    DistanceUnit,
    LinkedAccount,
    UserPreferences,
    UserProfile,
)


class TestUserPreferences:
    def test_defaults(self):
        prefs = UserPreferences()
        assert prefs.display_currency == DisplayCurrency.USD
        assert prefs.distance_unit == DistanceUnit.MILES
        assert prefs.home_airport == ""
        assert prefs.show_cash_prices is True
        assert prefs.default_cabin == "economy"

    def test_frozen(self):
        prefs = UserPreferences()
        with pytest.raises(AttributeError):
            prefs.home_airport = "SFO"  # type: ignore[misc]


class TestUserProfile:
    def test_create_empty(self):
        profile = UserProfile(user_id="u1")
        assert profile.user_id == "u1"
        assert profile.display_name == ""
        assert profile.linked_accounts == []

    def test_update_preferences(self):
        profile = UserProfile(user_id="u1")
        prefs = profile.update_preferences(home_airport="SFO", display_currency=DisplayCurrency.EUR)
        assert prefs.home_airport == "SFO"
        assert prefs.display_currency == DisplayCurrency.EUR
        # Other fields unchanged
        assert prefs.distance_unit == DistanceUnit.MILES

    def test_update_preferences_ignores_none(self):
        profile = UserProfile(user_id="u1")
        profile.update_preferences(home_airport="SFO")
        profile.update_preferences(display_currency=DisplayCurrency.GBP)
        assert profile.preferences.home_airport == "SFO"
        assert profile.preferences.display_currency == DisplayCurrency.GBP

    def test_link_account(self):
        profile = UserProfile(user_id="u1")
        acct = LinkedAccount(
            provider="manual", program_code="united", account_id="UA123", display_name="United", linked_at="2025-01-01"
        )
        profile.link_account(acct)
        assert len(profile.linked_accounts) == 1
        assert profile.linked_accounts[0].program_code == "united"

    def test_link_duplicate_ignored(self):
        profile = UserProfile(user_id="u1")
        acct = LinkedAccount("manual", "united", "UA123", "United", "2025-01-01")
        profile.link_account(acct)
        profile.link_account(acct)
        assert len(profile.linked_accounts) == 1

    def test_unlink_account(self):
        profile = UserProfile(user_id="u1")
        profile.link_account(LinkedAccount("manual", "united", "UA123", "United", "2025-01-01"))
        profile.link_account(LinkedAccount("manual", "hyatt", "HY456", "Hyatt", "2025-01-02"))
        removed = profile.unlink_account("united", "UA123")
        assert removed is True
        assert len(profile.linked_accounts) == 1

    def test_unlink_nonexistent(self):
        profile = UserProfile(user_id="u1")
        assert profile.unlink_account("nope", "x") is False

    def test_summary(self):
        profile = UserProfile(user_id="u1", display_name="Eric")
        profile.update_preferences(home_airport="SFO", favorite_programs=["united", "hyatt"])
        s = profile.summary()
        assert s["user_id"] == "u1"
        assert s["display_name"] == "Eric"
        assert s["home_airport"] == "SFO"
        assert s["favorite_programs"] == ["united", "hyatt"]


class TestProfileAPI:
    AUTH_HEADERS = {"Authorization": "Bearer test-token-eric"}

    @pytest.fixture
    def client(self):
        from redeemflow.app import create_app
        from redeemflow.identity.profile import _PROFILES
        from redeemflow.ports import PortBundle

        _PROFILES.clear()
        return TestClient(create_app(ports=PortBundle()))

    def test_get_profile_creates_default(self, client):
        resp = client.get("/api/profile", headers=self.AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == "auth0|eric"
        assert data["preferences"]["display_currency"] == "usd"

    def test_update_profile(self, client):
        resp = client.put(
            "/api/profile",
            json={"display_name": "Eric M", "bio": "Points enthusiast"},
            headers=self.AUTH_HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["display_name"] == "Eric M"

    def test_update_preferences(self, client):
        resp = client.put(
            "/api/profile/preferences",
            json={"home_airport": "SFO", "display_currency": "eur", "default_cabin": "business"},
            headers=self.AUTH_HEADERS,
        )
        assert resp.status_code == 200
        prefs = resp.json()["preferences"]
        assert prefs["home_airport"] == "SFO"
        assert prefs["display_currency"] == "eur"
        assert prefs["default_cabin"] == "business"

    def test_invalid_currency(self, client):
        resp = client.put(
            "/api/profile/preferences",
            json={"display_currency": "btc"},
            headers=self.AUTH_HEADERS,
        )
        assert "error" in resp.json()

    def test_link_account(self, client):
        resp = client.post(
            "/api/profile/accounts",
            json={"program_code": "united", "account_id": "UA123", "display_name": "My United"},
            headers=self.AUTH_HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["linked_accounts_count"] == 1

    def test_link_and_get_profile(self, client):
        client.post(
            "/api/profile/accounts",
            json={"program_code": "united", "account_id": "UA123"},
            headers=self.AUTH_HEADERS,
        )
        resp = client.get("/api/profile", headers=self.AUTH_HEADERS)
        assert len(resp.json()["linked_accounts"]) == 1

    def test_unlink_account(self, client):
        client.post(
            "/api/profile/accounts",
            json={"program_code": "united", "account_id": "UA123"},
            headers=self.AUTH_HEADERS,
        )
        resp = client.delete("/api/profile/accounts/united/UA123", headers=self.AUTH_HEADERS)
        assert resp.json()["status"] == "unlinked"

    def test_profile_requires_auth(self, client):
        assert client.get("/api/profile").status_code == 401
        assert client.put("/api/profile", json={"display_name": "X"}).status_code == 401

    def test_favorite_programs(self, client):
        client.put(
            "/api/profile/preferences",
            json={"favorite_programs": ["united", "hyatt", "chase-ur"]},
            headers=self.AUTH_HEADERS,
        )
        resp = client.get("/api/profile", headers=self.AUTH_HEADERS)
        assert resp.json()["favorite_programs"] == ["united", "hyatt", "chase-ur"]
