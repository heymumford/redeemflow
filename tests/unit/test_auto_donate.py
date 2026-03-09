"""Auto-donate rules engine tests — TDD: written before implementation.

Tests the auto-donate domain: rule model, engine lifecycle, threshold evaluation.
"""

from __future__ import annotations

import pytest

from redeemflow.charity.auto_donate import AutoDonateEngine, AutoDonateRule
from redeemflow.charity.donation_flow import DonationService, FakeDonationProvider
from redeemflow.charity.seed_data import CHARITY_NETWORK
from redeemflow.valuations.seed_data import PROGRAM_VALUATIONS


def _make_donation_service() -> DonationService:
    return DonationService(
        provider=FakeDonationProvider(),
        valuations=PROGRAM_VALUATIONS,
        charity_network=CHARITY_NETWORK,
    )


class TestAutoDonateRule:
    def test_frozen_dataclass(self):
        rule = AutoDonateRule(
            id="rule-1",
            user_id="auth0|eric",
            program_code="chase-ur",
            charity_name="Girl Scouts of the USA",
            charity_state="TX",
            days_unused_threshold=90,
            is_active=True,
        )
        with pytest.raises(AttributeError):
            rule.id = "rule-2"  # type: ignore[misc]

    def test_fields(self):
        rule = AutoDonateRule(
            id="rule-1",
            user_id="auth0|eric",
            program_code="chase-ur",
            charity_name="Girl Scouts of the USA",
            charity_state="TX",
            days_unused_threshold=90,
            is_active=True,
        )
        assert rule.user_id == "auth0|eric"
        assert rule.program_code == "chase-ur"
        assert rule.days_unused_threshold == 90
        assert rule.is_active is True


class TestAutoDonateEngine:
    def test_add_rule_and_get_user_rules(self):
        engine = AutoDonateEngine(donation_service=_make_donation_service())
        rule = engine.add_rule(
            user_id="auth0|eric",
            program_code="chase-ur",
            charity_name="Girl Scouts of the USA",
            charity_state="TX",
            days_threshold=90,
        )
        assert isinstance(rule, AutoDonateRule)
        rules = engine.get_user_rules("auth0|eric")
        assert len(rules) == 1
        assert rules[0].id == rule.id

    def test_evaluate_rules_triggers_donation_when_threshold_met(self):
        engine = AutoDonateEngine(donation_service=_make_donation_service())
        engine.add_rule(
            user_id="auth0|eric",
            program_code="chase-ur",
            charity_name="Girl Scouts of the USA",
            charity_state="TX",
            days_threshold=90,
        )
        # Simulate balances and activity
        balances = {"chase-ur": 10000}
        last_activity_days = {"chase-ur": 100}  # 100 days > 90 threshold
        donations = engine.evaluate_rules(balances, last_activity_days)
        assert len(donations) == 1
        assert donations[0].program_code == "chase-ur"
        assert donations[0].points_donated == 10000

    def test_evaluate_rules_does_not_trigger_under_threshold(self):
        engine = AutoDonateEngine(donation_service=_make_donation_service())
        engine.add_rule(
            user_id="auth0|eric",
            program_code="chase-ur",
            charity_name="Girl Scouts of the USA",
            charity_state="TX",
            days_threshold=90,
        )
        balances = {"chase-ur": 10000}
        last_activity_days = {"chase-ur": 30}  # 30 days < 90 threshold
        donations = engine.evaluate_rules(balances, last_activity_days)
        assert len(donations) == 0

    def test_remove_rule(self):
        engine = AutoDonateEngine(donation_service=_make_donation_service())
        rule = engine.add_rule(
            user_id="auth0|eric",
            program_code="chase-ur",
            charity_name="Girl Scouts of the USA",
            charity_state="TX",
            days_threshold=90,
        )
        engine.remove_rule(rule.id)
        assert len(engine.get_user_rules("auth0|eric")) == 0

    def test_multiple_rules_for_user(self):
        engine = AutoDonateEngine(donation_service=_make_donation_service())
        engine.add_rule(
            user_id="auth0|eric",
            program_code="chase-ur",
            charity_name="Girl Scouts of the USA",
            charity_state="TX",
            days_threshold=90,
        )
        engine.add_rule(
            user_id="auth0|eric",
            program_code="amex-mr",
            charity_name="AAUW",
            charity_state="CA",
            days_threshold=60,
        )
        assert len(engine.get_user_rules("auth0|eric")) == 2

    def test_evaluate_rules_only_triggers_matching_programs(self):
        engine = AutoDonateEngine(donation_service=_make_donation_service())
        engine.add_rule(
            user_id="auth0|eric",
            program_code="chase-ur",
            charity_name="Girl Scouts of the USA",
            charity_state="TX",
            days_threshold=90,
        )
        engine.add_rule(
            user_id="auth0|eric",
            program_code="amex-mr",
            charity_name="AAUW",
            charity_state="CA",
            days_threshold=60,
        )
        balances = {"chase-ur": 10000, "amex-mr": 5000}
        last_activity_days = {"chase-ur": 100, "amex-mr": 30}
        donations = engine.evaluate_rules(balances, last_activity_days)
        # Only chase-ur should trigger (100 > 90), amex-mr should not (30 < 60)
        assert len(donations) == 1
        assert donations[0].program_code == "chase-ur"
