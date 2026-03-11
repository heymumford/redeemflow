"""Tests for tier-based rate limiting policies."""

from __future__ import annotations

from decimal import Decimal

from redeemflow.middleware.tier_limits import (
    TIER_POLICIES,
    check_limit,
    get_policy,
    usage_snapshot,
)


class TestTierPolicies:
    def test_all_tiers_defined(self):
        assert "free" in TIER_POLICIES
        assert "premium" in TIER_POLICIES
        assert "pro" in TIER_POLICIES

    def test_pro_has_highest_limits(self):
        assert TIER_POLICIES["pro"].requests_per_minute > TIER_POLICIES["premium"].requests_per_minute
        assert TIER_POLICIES["premium"].requests_per_minute > TIER_POLICIES["free"].requests_per_minute

    def test_api_key_pro_only(self):
        assert TIER_POLICIES["pro"].api_key_allowed is True
        assert TIER_POLICIES["premium"].api_key_allowed is False
        assert TIER_POLICIES["free"].api_key_allowed is False

    def test_policy_frozen(self):
        import pytest

        with pytest.raises(AttributeError):
            TIER_POLICIES["free"].requests_per_minute = 999  # type: ignore[misc]


class TestGetPolicy:
    def test_known_tier(self):
        policy = get_policy("premium")
        assert policy.tier == "premium"

    def test_unknown_tier_defaults_free(self):
        policy = get_policy("enterprise")
        assert policy.tier == "free"


class TestCheckLimit:
    def test_within_limits(self):
        result = check_limit("free", requests_this_minute=5)
        assert result["allowed"] is True

    def test_minute_exceeded(self):
        result = check_limit("free", requests_this_minute=25)
        assert result["allowed"] is False
        assert "minute" in result["reason"].lower()

    def test_hour_exceeded(self):
        result = check_limit("free", requests_this_hour=250)
        assert result["allowed"] is False
        assert "hourly" in result["reason"].lower()

    def test_daily_search_exceeded(self):
        result = check_limit("free", searches_today=15)
        assert result["allowed"] is False
        assert "daily" in result["reason"].lower()

    def test_premium_higher_limits(self):
        # Same count, free blocked but premium allowed
        assert check_limit("free", requests_this_minute=25)["allowed"] is False
        assert check_limit("premium", requests_this_minute=25)["allowed"] is True

    def test_pro_highest_limits(self):
        assert check_limit("pro", requests_this_minute=150)["allowed"] is True
        assert check_limit("pro", requests_this_minute=250)["allowed"] is False


class TestUsageSnapshot:
    def test_basic_snapshot(self):
        snap = usage_snapshot("u1", "free", requests_this_minute=5)
        assert snap.user_id == "u1"
        assert snap.tier == "free"
        assert snap.minute_remaining == 15
        assert snap.policy.tier == "free"

    def test_utilization_calculation(self):
        snap = usage_snapshot("u1", "free", requests_this_minute=10)
        assert snap.utilization_pct == Decimal("50.0")

    def test_utilization_uses_max_dimension(self):
        # 10/20 minute = 50%, 190/200 hour = 95% -> should be 95%
        snap = usage_snapshot("u1", "free", requests_this_minute=10, requests_this_hour=190)
        assert snap.utilization_pct == Decimal("95.0")

    def test_zero_usage(self):
        snap = usage_snapshot("u1", "premium")
        assert snap.utilization_pct == Decimal("0")
        assert snap.minute_remaining == 60

    def test_remaining_floors_at_zero(self):
        snap = usage_snapshot("u1", "free", requests_this_minute=100)
        assert snap.minute_remaining == 0
