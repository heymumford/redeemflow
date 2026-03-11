"""Architectural fitness functions — Fowler's executable guardrails.

Beck: Test where risk is — structure, not behavior.
Fowler: Fitness functions guard architecture decisions automatically.
"""

from __future__ import annotations

import dataclasses
import importlib
import inspect
import pkgutil

import pytest

import redeemflow


@pytest.mark.fitness
class TestModuleStructure:
    """Verify the redeemflow namespace contains expected bounded contexts."""

    REQUIRED_MODULES = {
        "identity",
        "portfolio",
        "recommendations",
        "optimization",
        "billing",
        "charity",
        "community",
        "search",
        "notifications",
        "infra",
        "middleware",
    }

    def test_all_required_modules_exist(self):
        submodules = {mod.name for mod in pkgutil.iter_modules(redeemflow.__path__)}
        missing = self.REQUIRED_MODULES - submodules
        assert not missing, f"Missing required modules: {missing}"

    def test_no_circular_imports(self):
        """All domain modules must import cleanly."""
        for mod_name in self.REQUIRED_MODULES:
            importlib.import_module(f"redeemflow.{mod_name}")

    def test_module_count_gate(self):
        """Guard against unbounded module growth — max 17 top-level modules."""
        submodules = {mod.name for mod in pkgutil.iter_modules(redeemflow.__path__)}
        assert len(submodules) <= 17, f"Too many top-level modules ({len(submodules)}): {submodules}"

    def test_all_modules_import_cleanly(self):
        """All domain modules must import without circular dependency errors."""
        submodules = {mod.name for mod in pkgutil.iter_modules(redeemflow.__path__)}
        for mod_name in submodules:
            importlib.import_module(f"redeemflow.{mod_name}")


@pytest.mark.fitness
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

    def test_recommendations_depends_on_portfolio_and_optimization(self):
        source = importlib.util.find_spec("redeemflow.recommendations.engine").origin
        with open(source) as f:
            content = f.read()
        assert "redeemflow.portfolio.models" in content, "recommendations should use portfolio models"
        assert "redeemflow.optimization" in content, "recommendations should use optimization graph"
        assert "redeemflow.identity" not in content, "recommendations must not depend on identity"

    def test_optimization_depends_only_on_portfolio_models(self):
        source = importlib.util.find_spec("redeemflow.optimization.graph").origin
        with open(source) as f:
            content = f.read()
        assert "redeemflow.portfolio.models" in content, "optimization should use portfolio models"
        assert "redeemflow.identity" not in content, "optimization must not depend on identity"
        assert "redeemflow.recommendations" not in content, "optimization must not depend on recommendations"

    def test_infra_does_not_import_domain_services(self):
        """Repository layer must not import service classes."""
        source = importlib.util.find_spec("redeemflow.infra.pg_repositories").origin
        with open(source) as f:
            content = f.read()
        assert "DonationService" not in content, "infra must not import domain services"
        assert "PoolService" not in content, "infra must not import domain services"
        assert "ForumService" not in content, "infra must not import domain services"


@pytest.mark.fitness
class TestFrozenValueObjects:
    """All domain models crossing boundaries must be frozen dataclasses."""

    FROZEN_CLASSES = [
        "redeemflow.identity.models.User",
        "redeemflow.portfolio.models.PointBalance",
        "redeemflow.portfolio.models.LoyaltyAccount",
        "redeemflow.portfolio.models.LoyaltyProgram",
        "redeemflow.recommendations.models.Recommendation",
        "redeemflow.optimization.models.TransferPartner",
        "redeemflow.optimization.models.RedemptionOption",
        "redeemflow.optimization.models.TransferPath",
        "redeemflow.billing.models.Subscription",
        "redeemflow.billing.models.SubscriptionPlan",
        "redeemflow.charity.donation_flow.Donation",
        "redeemflow.community.models.Pledge",
        "redeemflow.community.forum.ForumReply",
        "redeemflow.search.award_search.AwardResult",
        "redeemflow.valuations.models.ProgramValuation",
        "redeemflow.valuations.models.AnnualValueResult",
    ]

    @pytest.mark.parametrize("class_path", FROZEN_CLASSES)
    def test_value_object_is_frozen(self, class_path: str):
        module_path, class_name = class_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        cls = getattr(module, class_name)
        assert dataclasses.is_dataclass(cls), f"{class_name} is not a dataclass"
        assert cls.__dataclass_params__.frozen, f"{class_name} must be frozen"


@pytest.mark.fitness
class TestDecimalDiscipline:
    """Financial values must use Decimal, never float."""

    FINANCIAL_MODULES = [
        "redeemflow.valuations.models",
        "redeemflow.billing.models",
        "redeemflow.charity.donation_flow",
        "redeemflow.community.models",
    ]

    @pytest.mark.parametrize("module_path", FINANCIAL_MODULES)
    def test_no_float_annotations_in_financial_models(self, module_path: str):
        module = importlib.import_module(module_path)
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if not dataclasses.is_dataclass(obj):
                continue
            for field in dataclasses.fields(obj):
                annotation = str(field.type)
                assert "float" not in annotation.lower(), (
                    f"{name}.{field.name} uses float — must use Decimal for financial values"
                )


@pytest.mark.fitness
class TestFixtureBuilders:
    """Verify test fixture builders produce valid instances."""

    def test_builders_exist_and_produce_valid_objects(self):
        from tests.fixtures.builders import (
            build_alert,
            build_award_result,
            build_balance,
            build_charity,
            build_donation,
            build_forum_post,
            build_forum_reply,
            build_founder,
            build_pledge,
            build_pool,
            build_recommendation,
            build_subscription,
            build_transfer_partner,
            build_user,
            build_valuation,
        )

        assert build_user().id.startswith("user-")
        assert build_balance().points == 50000
        assert build_valuation().program_code == "chase-ur"
        assert build_transfer_partner().source_program == "chase-ur"
        assert build_subscription().status == "active"
        assert build_charity().is_501c3 is True
        assert build_donation().status.value == "pending"
        assert build_pool().status.value == "open"
        assert build_pledge().points_pledged == 2000
        assert build_forum_post().title == "Test Post"
        assert build_forum_reply().content == "Test reply content."
        assert build_founder().status.value == "active"
        assert build_recommendation().program_code == "chase-ur"
        assert build_alert().priority.value == "medium"
        assert build_award_result().cabin == "business"
