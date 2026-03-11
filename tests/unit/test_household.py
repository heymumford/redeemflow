"""Tests for household points pooling and multi-member optimization."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from redeemflow.portfolio.household import (
    Household,
    HouseholdMember,
    HouseholdSummary,
)


def _member(mid: str, name: str, programs: dict[str, int]) -> HouseholdMember:
    return HouseholdMember(member_id=mid, name=name, role="primary", programs=programs)


class TestHousehold:
    def test_add_member(self):
        h = Household(household_id="h1", name="Test")
        h.add_member(_member("m1", "Alice", {"chase-ur": 50000}))
        assert len(h.members) == 1

    def test_add_duplicate_member_ignored(self):
        h = Household(household_id="h1", name="Test")
        m = _member("m1", "Alice", {"chase-ur": 50000})
        h.add_member(m)
        h.add_member(m)
        assert len(h.members) == 1

    def test_remove_member(self):
        h = Household(household_id="h1", name="Test")
        h.add_member(_member("m1", "Alice", {}))
        assert h.remove_member("m1") is True
        assert len(h.members) == 0

    def test_remove_nonexistent_member(self):
        h = Household(household_id="h1", name="Test")
        assert h.remove_member("nonexistent") is False

    def test_pool_balances_single_member(self):
        h = Household(household_id="h1", name="Test")
        h.add_member(_member("m1", "Alice", {"chase-ur": 50000, "united": 30000}))
        pooled = h.pool_balances()
        assert len(pooled) == 2
        chase = next(p for p in pooled if p.program_code == "chase-ur")
        assert chase.total_points == 50000
        assert chase.member_count == 1

    def test_pool_balances_multiple_members(self):
        h = Household(household_id="h1", name="Test")
        h.add_member(_member("m1", "Alice", {"chase-ur": 50000}))
        h.add_member(_member("m2", "Bob", {"chase-ur": 30000}))
        pooled = h.pool_balances()
        chase = next(p for p in pooled if p.program_code == "chase-ur")
        assert chase.total_points == 80000
        assert chase.member_count == 2
        assert len(chase.contributors) == 2

    def test_pool_balances_sorted_desc(self):
        h = Household(household_id="h1", name="Test")
        h.add_member(_member("m1", "Alice", {"chase-ur": 50000, "united": 80000}))
        pooled = h.pool_balances()
        assert pooled[0].total_points >= pooled[1].total_points

    def test_pool_balances_zero_excluded(self):
        h = Household(household_id="h1", name="Test")
        h.add_member(_member("m1", "Alice", {"chase-ur": 50000, "united": 0}))
        pooled = h.pool_balances()
        assert len(pooled) == 1

    def test_find_threshold_unlock(self):
        h = Household(household_id="h1", name="Test")
        h.add_member(_member("m1", "Alice", {"chase-ur": 30000}))
        h.add_member(_member("m2", "Bob", {"chase-ur": 25000}))
        opps = h.find_optimization_opportunities()
        types = [o["type"] for o in opps]
        assert "threshold_unlock" in types

    def test_find_consolidation(self):
        h = Household(household_id="h1", name="Test")
        h.add_member(_member("m1", "Alice", {"united": 40000}))
        h.add_member(_member("m2", "Bob", {"united": 10000}))
        opps = h.find_optimization_opportunities()
        types = [o["type"] for o in opps]
        assert "consolidation" in types

    def test_no_opportunities_single_member(self):
        h = Household(household_id="h1", name="Test")
        h.add_member(_member("m1", "Alice", {"chase-ur": 100000}))
        opps = h.find_optimization_opportunities()
        assert len(opps) == 0

    def test_summarize(self):
        h = Household(household_id="h1", name="Test")
        h.add_member(_member("m1", "Alice", {"chase-ur": 50000}))
        h.add_member(_member("m2", "Bob", {"chase-ur": 30000, "united": 20000}))
        summary = h.summarize()
        assert isinstance(summary, HouseholdSummary)
        assert summary.member_count == 2
        assert summary.total_programs == 2
        assert summary.total_points == 100000
        assert "chase-ur" in summary.unique_programs

    def test_empty_household(self):
        h = Household(household_id="h1", name="Test")
        summary = h.summarize()
        assert summary.member_count == 0
        assert summary.total_points == 0


class TestHouseholdAPI:
    AUTH_HEADERS = {"Authorization": "Bearer test-token-eric"}

    @pytest.fixture
    def client(self):
        from redeemflow.app import create_app
        from redeemflow.portfolio.household import _HOUSEHOLDS
        from redeemflow.ports import PortBundle

        _HOUSEHOLDS.clear()
        return TestClient(create_app(ports=PortBundle()))

    def test_get_household_requires_auth(self, client):
        resp = client.get("/api/household")
        assert resp.status_code == 401

    def test_get_empty_household(self, client):
        resp = client.get("/api/household", headers=self.AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["member_count"] == 0

    def test_add_member(self, client):
        resp = client.post(
            "/api/household/member",
            json={"member_id": "spouse1", "name": "Partner", "role": "spouse", "programs": {"chase-ur": 40000}},
            headers=self.AUTH_HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "added"

    def test_add_member_and_get_summary(self, client):
        client.post(
            "/api/household/member",
            json={"member_id": "s1", "name": "Partner", "programs": {"chase-ur": 40000}},
            headers=self.AUTH_HEADERS,
        )
        resp = client.get("/api/household", headers=self.AUTH_HEADERS)
        data = resp.json()
        assert data["member_count"] == 1
        assert data["total_points"] == 40000

    def test_remove_member(self, client):
        client.post(
            "/api/household/member",
            json={"member_id": "rm1", "name": "Remove Me", "programs": {}},
            headers=self.AUTH_HEADERS,
        )
        resp = client.delete("/api/household/member/rm1", headers=self.AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["status"] == "removed"

    def test_remove_nonexistent_member(self, client):
        resp = client.delete("/api/household/member/nonexistent", headers=self.AUTH_HEADERS)
        assert resp.json()["status"] == "not_found"

    def test_pooled_balances_in_summary(self, client):
        client.post(
            "/api/household/member",
            json={"member_id": "a", "name": "Alice", "programs": {"united": 30000}},
            headers=self.AUTH_HEADERS,
        )
        client.post(
            "/api/household/member",
            json={"member_id": "b", "name": "Bob", "programs": {"united": 25000}},
            headers=self.AUTH_HEADERS,
        )
        resp = client.get("/api/household", headers=self.AUTH_HEADERS)
        data = resp.json()
        united = next(b for b in data["pooled_balances"] if b["program_code"] == "united")
        assert united["total_points"] == 55000
        assert united["member_count"] == 2
