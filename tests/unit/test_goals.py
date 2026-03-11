"""Tests for savings goals and progress tracking."""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from redeemflow.portfolio.goals import (
    GoalCategory,
    GoalsSummary,
    GoalStatus,
    SavingsGoal,
    compute_progress,
    summarize_goals,
)


def _goal(target: int = 80000, current: int = 40000, status: GoalStatus = GoalStatus.ACTIVE) -> SavingsGoal:
    return SavingsGoal(
        goal_id="g1",
        name="SFO-NRT Business",
        category=GoalCategory.FLIGHT,
        program_code="united",
        target_points=target,
        current_points=current,
        status=status,
        target_redemption="SFO-NRT business class",
    )


class TestComputeProgress:
    def test_halfway(self):
        p = compute_progress(_goal(target=80000, current=40000))
        assert p.percent_complete == Decimal("50.0")
        assert p.points_remaining == 40000
        assert p.is_achievable is False

    def test_complete(self):
        p = compute_progress(_goal(target=80000, current=80000))
        assert p.percent_complete == Decimal("100.0")
        assert p.points_remaining == 0
        assert p.is_achievable is True

    def test_over_target(self):
        p = compute_progress(_goal(target=80000, current=100000))
        assert p.percent_complete == Decimal("100.0")
        assert p.points_remaining == 0

    def test_zero_target(self):
        p = compute_progress(_goal(target=0, current=0))
        assert p.percent_complete == Decimal("0")

    def test_earning_rate_small_remaining(self):
        p = compute_progress(_goal(target=50000, current=45000))
        assert "1-2 months" in p.earning_rate_needed

    def test_earning_rate_large_remaining(self):
        p = compute_progress(_goal(target=100000, current=10000))
        assert "months" in p.earning_rate_needed


class TestSummarizeGoals:
    def test_mixed_goals(self):
        goals = [
            _goal(target=80000, current=40000),
            _goal(target=50000, current=50000, status=GoalStatus.COMPLETED),
        ]
        # Override goal_ids
        goals = [
            SavingsGoal(
                goal_id="g1",
                name="Flight",
                category=GoalCategory.FLIGHT,
                program_code="united",
                target_points=80000,
                current_points=40000,
            ),
            SavingsGoal(
                goal_id="g2",
                name="Hotel",
                category=GoalCategory.HOTEL,
                program_code="hyatt",
                target_points=50000,
                current_points=50000,
                status=GoalStatus.COMPLETED,
            ),
        ]
        summary = summarize_goals(goals)
        assert isinstance(summary, GoalsSummary)
        assert summary.total_goals == 2
        assert summary.active_goals == 1
        assert summary.completed_goals == 1

    def test_empty_goals(self):
        summary = summarize_goals([])
        assert summary.total_goals == 0
        assert summary.overall_progress == Decimal("0")

    def test_overall_progress(self):
        goals = [
            SavingsGoal(
                goal_id="g1",
                name="A",
                category=GoalCategory.CUSTOM,
                program_code="chase-ur",
                target_points=100000,
                current_points=50000,
            ),
        ]
        summary = summarize_goals(goals)
        assert summary.overall_progress == Decimal("50.0")


class TestGoalsAPI:
    AUTH_HEADERS = {"Authorization": "Bearer test-token-eric"}

    @pytest.fixture
    def client(self):
        from redeemflow.app import create_app
        from redeemflow.portfolio.goals import _GOAL_COUNTER, _GOALS
        from redeemflow.ports import PortBundle

        _GOALS.clear()
        _GOAL_COUNTER.clear()
        return TestClient(create_app(ports=PortBundle()))

    def test_list_goals_empty(self, client):
        resp = client.get("/api/goals", headers=self.AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["total_goals"] == 0

    def test_create_goal(self, client):
        resp = client.post(
            "/api/goals",
            json={
                "name": "SFO-NRT Business",
                "category": "flight",
                "program_code": "united",
                "target_points": 80000,
                "current_points": 20000,
                "target_redemption": "SFO-NRT business class",
            },
            headers=self.AUTH_HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "created"

    def test_create_and_list_goal(self, client):
        client.post(
            "/api/goals",
            json={"name": "Goal 1", "program_code": "chase-ur", "target_points": 50000},
            headers=self.AUTH_HEADERS,
        )
        resp = client.get("/api/goals", headers=self.AUTH_HEADERS)
        data = resp.json()
        assert data["total_goals"] == 1
        assert data["goals"][0]["program_code"] == "chase-ur"

    def test_update_goal_points(self, client):
        create_resp = client.post(
            "/api/goals",
            json={"name": "Goal", "program_code": "united", "target_points": 80000, "current_points": 10000},
            headers=self.AUTH_HEADERS,
        )
        goal_id = create_resp.json()["goal_id"]
        resp = client.put(
            f"/api/goals/{goal_id}/points",
            json={"current_points": 50000},
            headers=self.AUTH_HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["current_points"] == 50000

    def test_update_auto_completes(self, client):
        create_resp = client.post(
            "/api/goals",
            json={"name": "Goal", "program_code": "united", "target_points": 50000},
            headers=self.AUTH_HEADERS,
        )
        goal_id = create_resp.json()["goal_id"]
        resp = client.put(
            f"/api/goals/{goal_id}/points",
            json={"current_points": 55000},
            headers=self.AUTH_HEADERS,
        )
        assert resp.json()["goal_status"] == "completed"

    def test_update_nonexistent_goal(self, client):
        resp = client.put(
            "/api/goals/nonexistent/points",
            json={"current_points": 1000},
            headers=self.AUTH_HEADERS,
        )
        assert "error" in resp.json()

    def test_goals_require_auth(self, client):
        assert client.get("/api/goals").status_code == 401
        assert client.post("/api/goals", json={"name": "X", "program_code": "y", "target_points": 1}).status_code == 401

    def test_progress_in_response(self, client):
        client.post(
            "/api/goals",
            json={"name": "G", "program_code": "chase-ur", "target_points": 100000, "current_points": 75000},
            headers=self.AUTH_HEADERS,
        )
        resp = client.get("/api/goals", headers=self.AUTH_HEADERS)
        goal = resp.json()["goals"][0]
        assert "percent_complete" in goal
        assert "earning_rate_needed" in goal
        assert Decimal(goal["percent_complete"]) == Decimal("75.0")
