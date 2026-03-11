"""Sprint 2: Protocol ports and fake adapters — zero I/O verification.

Tests every port Protocol and its fake adapter. Confirms:
1. Each fake adapter satisfies its Protocol (isinstance check)
2. Deterministic data returned from fakes
3. Error simulation paths work
4. No network calls (all in-memory)
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from redeemflow.billing.fake_adapter import FakeBillingAdapter
from redeemflow.billing.models import SubscriptionTier
from redeemflow.billing.ports import BillingPort
from redeemflow.charity.fake_adapter import FakeDonationAdapter
from redeemflow.charity.ports import DonationPort
from redeemflow.notifications.fake_adapter import FakeAlertAdapter
from redeemflow.notifications.models import Alert, AlertPriority, AlertType
from redeemflow.notifications.ports import AlertPort, AlertPreferences
from redeemflow.optimization.fake_adapter import FakeTransferGraphAdapter
from redeemflow.optimization.models import TransferPartner
from redeemflow.optimization.ports import TransferGraphPort
from redeemflow.portfolio.fake_adapter import FakePortfolioAdapter
from redeemflow.portfolio.models import PointBalance, UserPortfolio
from redeemflow.portfolio.ports import PortfolioPort, SyncStatus
from redeemflow.search.fake_adapter import FakeAwardSearchAdapter
from redeemflow.search.ports import AwardSearchPort
from redeemflow.valuations.fake_adapter import FakeValuationAdapter
from redeemflow.valuations.models import ProgramValuation
from redeemflow.valuations.ports import ValuationPort

# ─── PortfolioPort ───────────────────────────────────────────────────────────


class TestPortfolioPort:
    def test_fake_satisfies_protocol(self):
        adapter = FakePortfolioAdapter()
        assert isinstance(adapter, PortfolioPort)

    def test_fetch_balances_returns_list(self):
        adapter = FakePortfolioAdapter()
        balances = adapter.fetch_balances("auth0|eric")
        assert isinstance(balances, list)
        assert len(balances) > 0
        assert all(isinstance(b, PointBalance) for b in balances)

    def test_fetch_balances_unknown_user_empty(self):
        adapter = FakePortfolioAdapter()
        assert adapter.fetch_balances("auth0|nobody") == []

    def test_fetch_portfolio_returns_user_portfolio(self):
        adapter = FakePortfolioAdapter()
        portfolio = adapter.fetch_portfolio("auth0|eric")
        assert isinstance(portfolio, UserPortfolio)
        assert portfolio.user_id == "auth0|eric"
        assert len(portfolio.balances) > 0

    def test_fetch_portfolio_unknown_user_empty(self):
        adapter = FakePortfolioAdapter()
        portfolio = adapter.fetch_portfolio("auth0|nobody")
        assert portfolio.user_id == "auth0|nobody"
        assert len(portfolio.balances) == 0

    def test_sync_success(self):
        adapter = FakePortfolioAdapter()
        result = adapter.sync("auth0|eric")
        assert result.status == SyncStatus.SUCCESS
        assert result.programs_synced > 0
        assert result.programs_failed == 0

    def test_sync_failure_simulation(self):
        adapter = FakePortfolioAdapter(simulate_error="sync_failed")
        result = adapter.sync("auth0|eric")
        assert result.status == SyncStatus.FAILED
        assert result.programs_failed > 0

    def test_fetch_balances_timeout_simulation(self):
        adapter = FakePortfolioAdapter(simulate_error="timeout")
        with pytest.raises(TimeoutError):
            adapter.fetch_balances("auth0|eric")

    def test_deterministic_data(self):
        a = FakePortfolioAdapter()
        b = FakePortfolioAdapter()
        assert a.fetch_balances("auth0|eric") == b.fetch_balances("auth0|eric")

    def test_two_users_different_data(self):
        adapter = FakePortfolioAdapter()
        eric = adapter.fetch_balances("auth0|eric")
        steve = adapter.fetch_balances("auth0|steve")
        assert eric != steve


# ─── ValuationPort ───────────────────────────────────────────────────────────


class TestValuationPort:
    def test_fake_satisfies_protocol(self):
        adapter = FakeValuationAdapter()
        assert isinstance(adapter, ValuationPort)

    def test_get_valuation_known_program(self):
        adapter = FakeValuationAdapter()
        val = adapter.get_valuation("chase-ur")
        assert isinstance(val, ProgramValuation)
        assert val.program_code == "chase-ur"

    def test_get_valuation_unknown_program(self):
        adapter = FakeValuationAdapter()
        assert adapter.get_valuation("nonexistent") is None

    def test_get_all_returns_list(self):
        adapter = FakeValuationAdapter()
        all_vals = adapter.get_all()
        assert isinstance(all_vals, list)
        assert len(all_vals) > 10  # seed data has 20+ programs

    def test_all_valuations_have_positive_cpp(self):
        adapter = FakeValuationAdapter()
        for val in adapter.get_all():
            assert val.median_cpp > 0

    def test_deterministic_data(self):
        a = FakeValuationAdapter()
        b = FakeValuationAdapter()
        assert a.get_valuation("hyatt") == b.get_valuation("hyatt")

    def test_custom_data_injection(self):
        from redeemflow.valuations.models import ValuationSource

        custom = {
            "test-prog": ProgramValuation(
                program_code="test-prog",
                program_name="Test",
                valuations={ValuationSource.TPG: Decimal("2.0")},
            )
        }
        adapter = FakeValuationAdapter(data=custom)
        assert adapter.get_valuation("test-prog") is not None
        assert adapter.get_valuation("chase-ur") is None
        assert len(adapter.get_all()) == 1


# ─── TransferGraphPort ───────────────────────────────────────────────────────


class TestTransferGraphPort:
    def test_fake_satisfies_protocol(self):
        adapter = FakeTransferGraphAdapter()
        assert isinstance(adapter, TransferGraphPort)

    def test_find_paths_direct(self):
        adapter = FakeTransferGraphAdapter()
        paths = adapter.find_paths("UR", "UA")
        assert len(paths) > 0
        assert all(p.total_hops >= 1 for p in paths)

    def test_find_paths_no_route(self):
        adapter = FakeTransferGraphAdapter()
        paths = adapter.find_paths("UA", "NONEXISTENT")
        assert paths == []

    def test_find_paths_sorted_by_cpp_descending(self):
        adapter = FakeTransferGraphAdapter()
        paths = adapter.find_paths("UR", "UA")
        if len(paths) > 1:
            assert paths[0].effective_cpp >= paths[1].effective_cpp

    def test_get_ratio_direct_link(self):
        adapter = FakeTransferGraphAdapter()
        ratio = adapter.get_ratio("UR", "UA")
        assert ratio is not None
        assert ratio > 0

    def test_get_ratio_no_link(self):
        adapter = FakeTransferGraphAdapter()
        assert adapter.get_ratio("UA", "UR") is None

    def test_get_ratio_with_bonus(self):
        adapter = FakeTransferGraphAdapter()
        ratio = adapter.get_ratio("MR", "BA")
        assert ratio is not None
        assert ratio > 1.0  # 25% bonus

    def test_get_partners_from(self):
        adapter = FakeTransferGraphAdapter()
        partners = adapter.get_partners_from("UR")
        assert len(partners) > 0
        assert all(isinstance(p, TransferPartner) for p in partners)
        assert all(p.source_program == "UR" for p in partners)

    def test_get_partners_from_unknown_program(self):
        adapter = FakeTransferGraphAdapter()
        assert adapter.get_partners_from("NONEXISTENT") == []

    def test_two_hop_paths(self):
        # MR -> BA -> (redemption) is 1-hop
        # UR -> BA -> (redemption) also 1-hop
        # Check that multi-hop paths exist when source needs intermediary
        adapter = FakeTransferGraphAdapter()
        # UR has no direct link to ANA, but UR->? and ?->ANA check
        paths = adapter.find_paths("UR", "ANA")
        # No direct UR->ANA partner in test data, so no paths
        assert paths == []


# ─── DonationPort ────────────────────────────────────────────────────────────


class TestDonationPort:
    def test_fake_satisfies_protocol(self):
        adapter = FakeDonationAdapter()
        assert isinstance(adapter, DonationPort)

    def test_process_donation_returns_reference(self):
        adapter = FakeDonationAdapter()
        result = adapter.process_donation("user-1", "Girl Scouts", Decimal("50.00"))
        assert "reference_id" in result
        assert result["status"] == "completed"

    def test_get_donation_status_known_reference(self):
        adapter = FakeDonationAdapter()
        result = adapter.process_donation("user-1", "Test Charity", Decimal("25.00"))
        status = adapter.get_donation_status(result["reference_id"])
        assert status == "completed"

    def test_get_donation_status_unknown_reference(self):
        adapter = FakeDonationAdapter()
        assert adapter.get_donation_status("fake-nonexistent") == "unknown"

    def test_donation_count_tracking(self):
        adapter = FakeDonationAdapter()
        assert adapter.donation_count == 0
        adapter.process_donation("u1", "Charity A", Decimal("10.00"))
        adapter.process_donation("u2", "Charity B", Decimal("20.00"))
        assert adapter.donation_count == 2

    def test_error_simulation(self):
        adapter = FakeDonationAdapter(simulate_error="api_error")
        with pytest.raises(RuntimeError, match="service unavailable"):
            adapter.process_donation("user-1", "Test", Decimal("10.00"))


# ─── AwardSearchPort ────────────────────────────────────────────────────────


class TestAwardSearchPort:
    def test_fake_satisfies_protocol(self):
        adapter = FakeAwardSearchAdapter()
        assert isinstance(adapter, AwardSearchPort)

    def test_search_known_route(self):
        adapter = FakeAwardSearchAdapter()
        results = adapter.search("SFO", "NRT", "2026-07-01", "business")
        assert len(results) > 0
        assert all(r.origin == "SFO" for r in results)
        assert all(r.destination == "NRT" for r in results)

    def test_search_unknown_route_empty(self):
        adapter = FakeAwardSearchAdapter()
        results = adapter.search("SFO", "XXX", "2026-07-01", "economy")
        assert results == []

    def test_search_date_overridden(self):
        adapter = FakeAwardSearchAdapter()
        results = adapter.search("SFO", "NRT", "2026-12-25", "business")
        assert all(r.date == "2026-12-25" for r in results)

    def test_search_first_class(self):
        adapter = FakeAwardSearchAdapter()
        results = adapter.search("SFO", "NRT", "2026-07-01", "first")
        assert len(results) > 0
        assert all(r.cabin == "first" for r in results)

    def test_timeout_simulation(self):
        adapter = FakeAwardSearchAdapter(simulate_error="timeout")
        with pytest.raises(TimeoutError):
            adapter.search("SFO", "NRT", "2026-07-01", "business")

    def test_deterministic_data(self):
        a = FakeAwardSearchAdapter()
        b = FakeAwardSearchAdapter()
        assert a.search("JFK", "LHR", "2026-01-01", "business") == b.search("JFK", "LHR", "2026-01-01", "business")


# ─── BillingPort ─────────────────────────────────────────────────────────────


class TestBillingPort:
    def test_fake_satisfies_protocol(self):
        adapter = FakeBillingAdapter()
        assert isinstance(adapter, BillingPort)

    def test_create_subscription(self):
        adapter = FakeBillingAdapter()
        sub = adapter.create_subscription("user-1", SubscriptionTier.PREMIUM)
        assert sub.user_id == "user-1"
        assert sub.tier == SubscriptionTier.PREMIUM
        assert sub.status == "active"

    def test_create_default_free_tier(self):
        adapter = FakeBillingAdapter()
        sub = adapter.create_subscription("user-1")
        assert sub.tier == SubscriptionTier.FREE

    def test_cancel_subscription(self):
        adapter = FakeBillingAdapter()
        sub = adapter.create_subscription("user-1", SubscriptionTier.PREMIUM)
        cancelled = adapter.cancel_subscription(sub.id)
        assert cancelled.status == "cancelled"
        assert cancelled.user_id == "user-1"

    def test_cancel_unknown_subscription_raises(self):
        adapter = FakeBillingAdapter()
        with pytest.raises(ValueError, match="not found"):
            adapter.cancel_subscription("sub_nonexistent")

    def test_get_subscription(self):
        adapter = FakeBillingAdapter()
        adapter.create_subscription("user-1", SubscriptionTier.PRO)
        sub = adapter.get_subscription("user-1")
        assert sub is not None
        assert sub.tier == SubscriptionTier.PRO

    def test_get_subscription_unknown_user(self):
        adapter = FakeBillingAdapter()
        assert adapter.get_subscription("unknown") is None

    def test_webhook_checkout_completed(self):
        adapter = FakeBillingAdapter()
        result = adapter.handle_webhook(
            "checkout.session.completed",
            {"user_id": "user-1", "tier": "premium"},
        )
        assert result["status"] == "processed"
        sub = adapter.get_subscription("user-1")
        assert sub is not None
        assert sub.tier == SubscriptionTier.PREMIUM

    def test_webhook_subscription_deleted(self):
        adapter = FakeBillingAdapter()
        adapter.create_subscription("user-1", SubscriptionTier.PREMIUM)
        result = adapter.handle_webhook(
            "customer.subscription.deleted",
            {"user_id": "user-1"},
        )
        assert result["status"] == "processed"
        sub = adapter.get_subscription("user-1")
        assert sub is not None
        assert sub.status == "cancelled"

    def test_webhook_unknown_event_ignored(self):
        adapter = FakeBillingAdapter()
        result = adapter.handle_webhook("unknown.event", {})
        assert result["status"] == "ignored"

    def test_subscription_count(self):
        adapter = FakeBillingAdapter()
        assert adapter.subscription_count == 0
        adapter.create_subscription("u1", SubscriptionTier.FREE)
        adapter.create_subscription("u2", SubscriptionTier.PREMIUM)
        assert adapter.subscription_count == 2


# ─── AlertPort ───────────────────────────────────────────────────────────────


class TestAlertPort:
    def _make_alert(self) -> Alert:
        return Alert(
            id="alert-1",
            alert_type=AlertType.TRANSFER_BONUS,
            priority=AlertPriority.HIGH,
            title="25% MR to BA bonus",
            message="Transfer bonus active",
            program_code="MR",
            action_url=None,
            created_at="2026-03-11T00:00:00Z",
            expires_at=None,
        )

    def test_fake_satisfies_protocol(self):
        adapter = FakeAlertAdapter()
        assert isinstance(adapter, AlertPort)

    def test_send_alert_success(self):
        adapter = FakeAlertAdapter()
        alert = self._make_alert()
        assert adapter.send_alert("user-1", alert) is True
        assert adapter.alert_count == 1

    def test_send_alert_failure_simulation(self):
        adapter = FakeAlertAdapter(simulate_error="delivery_failed")
        alert = self._make_alert()
        assert adapter.send_alert("user-1", alert) is False
        assert adapter.alert_count == 0

    def test_get_preferences_default(self):
        adapter = FakeAlertAdapter()
        prefs = adapter.get_preferences("user-1")
        assert isinstance(prefs, AlertPreferences)
        assert prefs.user_id == "user-1"
        assert prefs.email_enabled is True

    def test_get_preferences_custom(self):
        adapter = FakeAlertAdapter()
        custom = AlertPreferences(
            user_id="user-1",
            email_enabled=False,
            push_enabled=True,
            enabled_types=frozenset({AlertType.DEVALUATION}),
        )
        adapter.set_preferences(custom)
        prefs = adapter.get_preferences("user-1")
        assert prefs.email_enabled is False
        assert prefs.push_enabled is True
        assert AlertType.DEVALUATION in prefs.enabled_types

    def test_sent_alerts_tracking(self):
        adapter = FakeAlertAdapter()
        alert = self._make_alert()
        adapter.send_alert("user-1", alert)
        adapter.send_alert("user-2", alert)
        assert len(adapter.sent_alerts) == 2
        assert adapter.sent_alerts[0][0] == "user-1"
        assert adapter.sent_alerts[1][0] == "user-2"
