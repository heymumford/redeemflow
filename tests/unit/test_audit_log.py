"""Tests for audit logging — append-only action tracking."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from redeemflow.admin.audit import AuditAction, AuditLog, AuditSummary


class TestAuditLog:
    def test_record_creates_entry(self):
        log = AuditLog()
        entry = log.record(
            user_id="u1",
            action=AuditAction.GOAL_CREATE,
            resource_type="goal",
            resource_id="goal_1",
            detail="Created SFO-NRT goal",
        )
        assert entry.entry_id == "audit_1"
        assert entry.user_id == "u1"
        assert entry.action == AuditAction.GOAL_CREATE
        assert entry.resource_type == "goal"
        assert entry.resource_id == "goal_1"

    def test_record_auto_increments_id(self):
        log = AuditLog()
        e1 = log.record("u1", AuditAction.GOAL_CREATE, "goal", "g1")
        e2 = log.record("u1", AuditAction.GOAL_UPDATE, "goal", "g1")
        assert e1.entry_id == "audit_1"
        assert e2.entry_id == "audit_2"

    def test_record_auto_timestamps(self):
        log = AuditLog()
        entry = log.record("u1", AuditAction.PORTFOLIO_VIEW, "portfolio", "")
        assert entry.timestamp != ""
        assert "T" in entry.timestamp

    def test_record_explicit_timestamp(self):
        log = AuditLog()
        entry = log.record("u1", AuditAction.AUTH_LOGIN, "session", "s1", timestamp="2025-06-15T10:00:00Z")
        assert entry.timestamp == "2025-06-15T10:00:00Z"

    def test_entry_is_frozen(self):
        log = AuditLog()
        entry = log.record("u1", AuditAction.GOAL_CREATE, "goal", "g1")
        with pytest.raises(AttributeError):
            entry.user_id = "hacker"  # type: ignore[misc]

    def test_size(self):
        log = AuditLog()
        assert log.size == 0
        log.record("u1", AuditAction.GOAL_CREATE, "goal", "g1")
        log.record("u2", AuditAction.TRIP_CREATE, "trip", "t1")
        assert log.size == 2

    def test_record_with_ip_and_agent(self):
        log = AuditLog()
        entry = log.record(
            "u1", AuditAction.AUTH_LOGIN, "session", "s1", ip_address="1.2.3.4", user_agent="TestBrowser/1.0"
        )
        assert entry.ip_address == "1.2.3.4"
        assert entry.user_agent == "TestBrowser/1.0"


class TestAuditLogQuery:
    def _populated_log(self) -> AuditLog:
        log = AuditLog()
        log.record("u1", AuditAction.GOAL_CREATE, "goal", "g1")
        log.record("u1", AuditAction.GOAL_UPDATE, "goal", "g1")
        log.record("u2", AuditAction.TRIP_CREATE, "trip", "t1")
        log.record("u1", AuditAction.PORTFOLIO_VIEW, "portfolio", "")
        log.record("u2", AuditAction.AWARD_SEARCH, "search", "")
        return log

    def test_query_all(self):
        log = self._populated_log()
        results = log.query()
        assert len(results) == 5

    def test_query_by_user(self):
        log = self._populated_log()
        results = log.query(user_id="u1")
        assert len(results) == 3
        assert all(e.user_id == "u1" for e in results)

    def test_query_by_action(self):
        log = self._populated_log()
        results = log.query(action=AuditAction.GOAL_CREATE)
        assert len(results) == 1

    def test_query_by_resource_type(self):
        log = self._populated_log()
        results = log.query(resource_type="goal")
        assert len(results) == 2

    def test_query_combined_filters(self):
        log = self._populated_log()
        results = log.query(user_id="u1", resource_type="goal")
        assert len(results) == 2

    def test_query_limit(self):
        log = self._populated_log()
        results = log.query(limit=2)
        assert len(results) == 2
        # Most recent first
        assert results[0].entry_id == "audit_5"

    def test_query_returns_most_recent_first(self):
        log = self._populated_log()
        results = log.query()
        ids = [e.entry_id for e in results]
        assert ids == ["audit_5", "audit_4", "audit_3", "audit_2", "audit_1"]

    def test_query_empty_log(self):
        log = AuditLog()
        assert log.query() == []


class TestAuditLogSummary:
    def test_summary_basic(self):
        log = AuditLog()
        log.record("u1", AuditAction.GOAL_CREATE, "goal", "g1")
        log.record("u2", AuditAction.TRIP_CREATE, "trip", "t1")
        log.record("u1", AuditAction.GOAL_UPDATE, "goal", "g1")

        s = log.summarize()
        assert isinstance(s, AuditSummary)
        assert s.total_entries == 3
        assert s.unique_users == 2
        assert s.action_counts["goal.create"] == 1
        assert s.action_counts["trip.create"] == 1
        assert s.action_counts["goal.update"] == 1

    def test_summary_empty(self):
        s = AuditLog().summarize()
        assert s.total_entries == 0
        assert s.unique_users == 0
        assert s.action_counts == {}
        assert s.recent_entries == []

    def test_summary_recent_limit(self):
        log = AuditLog()
        for i in range(30):
            log.record("u1", AuditAction.PORTFOLIO_VIEW, "portfolio", "", timestamp=f"2025-01-{i + 1:02d}")
        s = log.summarize(limit=10)
        assert len(s.recent_entries) == 10
        assert s.total_entries == 30


class TestAuditAPI:
    AUTH_HEADERS = {"Authorization": "Bearer test-token-eric"}

    @pytest.fixture
    def client(self):
        from redeemflow.admin.audit import reset_audit_log
        from redeemflow.app import create_app
        from redeemflow.ports import PortBundle

        reset_audit_log()
        return TestClient(create_app(ports=PortBundle()))

    def test_audit_view_empty(self, client):
        resp = client.get("/api/admin/audit", headers=self.AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["count"] == 0

    def test_audit_summary_empty(self, client):
        resp = client.get("/api/admin/audit/summary", headers=self.AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["total_entries"] == 0

    def test_audit_invalid_action_filter(self, client):
        resp = client.get("/api/admin/audit?action=bogus", headers=self.AUTH_HEADERS)
        assert "error" in resp.json()

    def test_audit_requires_auth(self, client):
        assert client.get("/api/admin/audit").status_code == 401
        assert client.get("/api/admin/audit/summary").status_code == 401

    def test_audit_records_visible(self, client):
        from redeemflow.admin.audit import AuditAction, get_audit_log

        log = get_audit_log()
        log.record("auth0|eric", AuditAction.GOAL_CREATE, "goal", "g1", detail="Test goal")
        log.record("auth0|eric", AuditAction.TRIP_CREATE, "trip", "t1")

        resp = client.get("/api/admin/audit", headers=self.AUTH_HEADERS)
        data = resp.json()
        assert data["count"] == 2
        assert data["entries"][0]["action"] == "trip.create"

    def test_audit_filter_by_resource_type(self, client):
        from redeemflow.admin.audit import AuditAction, get_audit_log

        log = get_audit_log()
        log.record("auth0|eric", AuditAction.GOAL_CREATE, "goal", "g1")
        log.record("auth0|eric", AuditAction.TRIP_CREATE, "trip", "t1")

        resp = client.get("/api/admin/audit?resource_type=goal", headers=self.AUTH_HEADERS)
        assert resp.json()["count"] == 1

    def test_audit_summary_with_data(self, client):
        from redeemflow.admin.audit import AuditAction, get_audit_log

        log = get_audit_log()
        log.record("auth0|eric", AuditAction.GOAL_CREATE, "goal", "g1")
        log.record("auth0|other", AuditAction.TRIP_CREATE, "trip", "t1")

        resp = client.get("/api/admin/audit/summary", headers=self.AUTH_HEADERS)
        data = resp.json()
        assert data["total_entries"] == 2
        assert data["unique_users"] == 2
