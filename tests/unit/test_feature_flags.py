"""Tests for feature flags."""

from __future__ import annotations

from redeemflow.middleware.feature_flags import (
    DEFAULT_FLAGS,
    FeatureFlag,
    FlagRegistry,
    FlagStatus,
)


class TestFlagRegistry:
    def test_register_and_get(self):
        reg = FlagRegistry()
        flag = FeatureFlag("test", "Test flag", FlagStatus.ENABLED)
        reg.register(flag)
        assert reg.get_flag("test") is flag

    def test_unknown_flag(self):
        reg = FlagRegistry()
        assert reg.get_flag("nope") is None

    def test_enabled_flag(self):
        reg = FlagRegistry()
        reg.register(FeatureFlag("test", "Test", FlagStatus.ENABLED))
        assert reg.is_enabled("test") is True

    def test_disabled_flag(self):
        reg = FlagRegistry()
        reg.register(FeatureFlag("test", "Test", FlagStatus.DISABLED))
        assert reg.is_enabled("test") is False

    def test_tier_gated_allowed(self):
        reg = FlagRegistry()
        reg.register(FeatureFlag("test", "Test", FlagStatus.TIER_GATED, allowed_tiers=["pro"]))
        assert reg.is_enabled("test", tier="pro") is True

    def test_tier_gated_denied(self):
        reg = FlagRegistry()
        reg.register(FeatureFlag("test", "Test", FlagStatus.TIER_GATED, allowed_tiers=["pro"]))
        assert reg.is_enabled("test", tier="free") is False

    def test_percentage_rollout_deterministic(self):
        reg = FlagRegistry()
        reg.register(FeatureFlag("test", "Test", FlagStatus.PERCENTAGE, percentage=50))
        # Same user+flag should always give the same result
        result1 = reg.is_enabled("test", user_id="user1")
        result2 = reg.is_enabled("test", user_id="user1")
        assert result1 == result2

    def test_percentage_zero(self):
        reg = FlagRegistry()
        reg.register(FeatureFlag("test", "Test", FlagStatus.PERCENTAGE, percentage=0))
        assert reg.is_enabled("test", user_id="user1") is False

    def test_percentage_hundred(self):
        reg = FlagRegistry()
        reg.register(FeatureFlag("test", "Test", FlagStatus.PERCENTAGE, percentage=100))
        assert reg.is_enabled("test", user_id="user1") is True

    def test_percentage_no_user(self):
        reg = FlagRegistry()
        reg.register(FeatureFlag("test", "Test", FlagStatus.PERCENTAGE, percentage=50))
        assert reg.is_enabled("test") is False

    def test_list_flags(self):
        reg = FlagRegistry()
        reg.register(FeatureFlag("a", "A", FlagStatus.ENABLED))
        reg.register(FeatureFlag("b", "B", FlagStatus.DISABLED))
        assert len(reg.list_flags()) == 2

    def test_enabled_for_user(self):
        reg = FlagRegistry()
        reg.register(FeatureFlag("a", "A", FlagStatus.ENABLED))
        reg.register(FeatureFlag("b", "B", FlagStatus.DISABLED))
        reg.register(FeatureFlag("c", "C", FlagStatus.TIER_GATED, allowed_tiers=["pro"]))
        enabled = reg.enabled_for_user("user1", tier="pro")
        assert "a" in enabled
        assert "b" not in enabled
        assert "c" in enabled

    def test_flag_summary(self):
        reg = FlagRegistry()
        reg.register(FeatureFlag("a", "A", FlagStatus.ENABLED))
        reg.register(FeatureFlag("b", "B", FlagStatus.DISABLED))
        reg.register(FeatureFlag("c", "C", FlagStatus.PERCENTAGE, percentage=50))
        s = reg.flag_summary()
        assert s["total"] == 3
        assert s["enabled"] == 1
        assert s["disabled"] == 1
        assert s["percentage"] == 1

    def test_update_flag(self):
        reg = FlagRegistry()
        reg.register(FeatureFlag("test", "Test", FlagStatus.ENABLED))
        reg.register(FeatureFlag("test", "Test v2", FlagStatus.DISABLED))
        assert reg.is_enabled("test") is False

    def test_unknown_returns_false(self):
        reg = FlagRegistry()
        assert reg.is_enabled("doesnt_exist") is False


class TestDefaultFlags:
    def test_default_flags_loaded(self):
        assert len(DEFAULT_FLAGS) >= 10

    def test_all_have_names(self):
        for f in DEFAULT_FLAGS:
            assert f.name
            assert f.description
