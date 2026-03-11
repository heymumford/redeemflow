"""Tests for admin dashboard metrics."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from redeemflow.admin.dashboard import DashboardReport, generate_dashboard


class TestGenerateDashboard:
    def test_basic_report(self):
        report = generate_dashboard(user_count=100, portfolio_count=80, goal_count=50)
        assert isinstance(report, DashboardReport)
        assert report.system.total_users == 100
        assert report.system.total_portfolios == 80

    def test_feature_adoption_present(self):
        report = generate_dashboard(user_count=100)
        assert len(report.feature_adoption) >= 5
        names = [f.feature_name for f in report.feature_adoption]
        assert "portfolio_sync" in names
        assert "goals" in names

    def test_tier_distribution(self):
        report = generate_dashboard(user_count=100)
        tiers = {t.tier for t in report.tier_distribution}
        assert "free" in tiers
        assert "premium" in tiers
        assert "pro" in tiers

    def test_top_programs(self):
        report = generate_dashboard(user_count=100)
        assert len(report.top_programs) >= 5
        assert report.top_programs[0]["program"] == "chase-ur"

    def test_health_check(self):
        report = generate_dashboard()
        assert report.health_check["status"] == "healthy"
        assert report.health_check["uptime_pct"] > 99

    def test_zero_users(self):
        report = generate_dashboard(user_count=0)
        assert report.system.total_users == 0

    def test_generated_at_set(self):
        report = generate_dashboard()
        assert report.system.generated_at != ""

    def test_avg_programs_per_user(self):
        report = generate_dashboard(user_count=100, portfolio_count=300)
        assert report.system.avg_programs_per_user > 0


class TestAdminDashboardAPI:
    AUTH_HEADERS = {"Authorization": "Bearer test-token-eric"}

    @pytest.fixture
    def client(self):
        from redeemflow.app import create_app
        from redeemflow.ports import PortBundle

        return TestClient(create_app(ports=PortBundle()))

    def test_dashboard_endpoint(self, client):
        resp = client.get("/api/admin/dashboard", headers=self.AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "system" in data
        assert "feature_adoption" in data
        assert "health_check" in data

    def test_dashboard_requires_auth(self, client):
        resp = client.get("/api/admin/dashboard")
        assert resp.status_code == 401
