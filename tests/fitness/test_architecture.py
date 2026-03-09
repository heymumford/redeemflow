"""Architectural fitness functions — Fowler's executable guardrails."""

from __future__ import annotations

import importlib
import pkgutil

import redeemflow


class TestModuleStructure:
    """Verify the redeemflow namespace contains expected bounded contexts."""

    REQUIRED_MODULES = {"identity", "portfolio", "recommendations"}

    def test_all_required_modules_exist(self):
        submodules = {mod.name for mod in pkgutil.iter_modules(redeemflow.__path__)}
        missing = self.REQUIRED_MODULES - submodules
        assert not missing, f"Missing required modules: {missing}"

    def test_no_circular_imports(self):
        """All domain modules must import cleanly."""
        for mod_name in self.REQUIRED_MODULES:
            importlib.import_module(f"redeemflow.{mod_name}")


class TestDomainBoundaries:
    """Verify anti-corruption layer boundaries are respected."""

    def test_portfolio_does_not_import_recommendations(self):
        source = importlib.util.find_spec("redeemflow.portfolio.models").origin
        with open(source) as f:
            content = f.read()
        assert "recommendations" not in content, "portfolio must not depend on recommendations"

    def test_identity_does_not_import_portfolio(self):
        source = importlib.util.find_spec("redeemflow.identity.models").origin
        with open(source) as f:
            content = f.read()
        assert "portfolio" not in content, "identity must not depend on portfolio"

    def test_recommendations_depends_only_on_portfolio_models(self):
        source = importlib.util.find_spec("redeemflow.recommendations.engine").origin
        with open(source) as f:
            content = f.read()
        assert "redeemflow.portfolio.models" in content, "recommendations should use portfolio models"
        assert "redeemflow.identity" not in content, "recommendations must not depend on identity"


class TestFrozenValueObjects:
    """All domain models crossing boundaries must be frozen dataclasses."""

    def test_user_is_frozen(self):
        from redeemflow.identity.models import User

        assert User.__dataclass_params__.frozen

    def test_point_balance_is_frozen(self):
        from redeemflow.portfolio.models import PointBalance

        assert PointBalance.__dataclass_params__.frozen

    def test_loyalty_account_is_frozen(self):
        from redeemflow.portfolio.models import LoyaltyAccount

        assert LoyaltyAccount.__dataclass_params__.frozen

    def test_recommendation_is_frozen(self):
        from redeemflow.recommendations.models import Recommendation

        assert Recommendation.__dataclass_params__.frozen
