"""Tests for achievement system — gamification milestones."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from redeemflow.community.achievements import (
    ACHIEVEMENTS,
    AchievementRarity,
    UserAchievements,
)


class TestAchievementCatalog:
    def test_achievements_defined(self):
        assert len(ACHIEVEMENTS) >= 10

    def test_all_have_required_fields(self):
        for a in ACHIEVEMENTS.values():
            assert a.achievement_id
            assert a.name
            assert a.description
            assert a.category
            assert a.rarity

    def test_rarities_distributed(self):
        rarities = [a.rarity for a in ACHIEVEMENTS.values()]
        assert AchievementRarity.COMMON in rarities
        assert AchievementRarity.RARE in rarities
        assert AchievementRarity.LEGENDARY in rarities


class TestUserAchievements:
    def test_grant(self):
        ua = UserAchievements(user_id="u1")
        assert ua.grant("first_sync") is True
        assert ua.has("first_sync") is True

    def test_grant_duplicate(self):
        ua = UserAchievements(user_id="u1")
        ua.grant("first_sync")
        assert ua.grant("first_sync") is False

    def test_total_reward_points(self):
        ua = UserAchievements(user_id="u1")
        ua.grant("first_sync")
        ua.grant("first_goal")
        assert ua.total_reward_points() == 200  # 100 + 100

    def test_progress_summary(self):
        ua = UserAchievements(user_id="u1")
        ua.grant("first_sync")
        s = ua.progress_summary()
        assert s["earned"] == 1
        assert s["total"] == len(ACHIEVEMENTS)
        assert s["completion_pct"] > 0

    def test_empty_progress(self):
        ua = UserAchievements(user_id="u1")
        s = ua.progress_summary()
        assert s["earned"] == 0
        assert s["reward_points"] == 0

    def test_grant_with_detail(self):
        ua = UserAchievements(user_id="u1")
        ua.grant("points_100k", detail="Reached 150K total")
        assert ua.earned[0].detail == "Reached 150K total"


class TestAchievementsAPI:
    AUTH_HEADERS = {"Authorization": "Bearer test-token-eric"}

    @pytest.fixture
    def client(self):
        from redeemflow.app import create_app
        from redeemflow.community.achievements import _USER_ACHIEVEMENTS
        from redeemflow.ports import PortBundle

        _USER_ACHIEVEMENTS.clear()
        return TestClient(create_app(ports=PortBundle()))

    def test_list_achievements(self, client):
        resp = client.get("/api/achievements")
        assert resp.status_code == 200
        assert len(resp.json()["achievements"]) >= 10

    def test_my_achievements_empty(self, client):
        resp = client.get("/api/achievements/me", headers=self.AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["earned"] == 0

    def test_my_achievements_with_data(self, client):
        from redeemflow.community.achievements import get_user_achievements

        ua = get_user_achievements("auth0|eric")
        ua.grant("first_sync")
        ua.grant("first_goal")

        resp = client.get("/api/achievements/me", headers=self.AUTH_HEADERS)
        data = resp.json()
        assert data["earned"] == 2
        assert data["reward_points"] == 200

    def test_achievements_require_auth_for_me(self, client):
        assert client.get("/api/achievements/me").status_code == 401

    def test_catalog_is_public(self, client):
        assert client.get("/api/achievements").status_code == 200
