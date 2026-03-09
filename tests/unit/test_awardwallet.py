"""Sprint 2: AwardWallet adapter — balance fetching from external API."""

from __future__ import annotations

from decimal import Decimal

import pytest

from redeemflow.portfolio.awardwallet import (
    AwardWalletAdapter,
    AwardWalletError,
    FakeAwardWalletAdapter,
)
from redeemflow.portfolio.models import PointBalance
from redeemflow.portfolio.ports import BalanceFetcher


class TestAwardWalletAdapter:
    def test_implements_balance_fetcher_protocol(self):
        adapter = AwardWalletAdapter(api_key="test-key", base_url="https://api.example.com")
        assert isinstance(adapter, BalanceFetcher)

    def test_has_fetch_balances_method(self):
        adapter = AwardWalletAdapter(api_key="test-key", base_url="https://api.example.com")
        assert hasattr(adapter, "fetch_balances")
        assert callable(adapter.fetch_balances)


class TestFakeAwardWalletAdapter:
    def test_implements_balance_fetcher_protocol(self):
        adapter = FakeAwardWalletAdapter()
        assert isinstance(adapter, BalanceFetcher)

    def test_returns_deterministic_balances(self):
        adapter = FakeAwardWalletAdapter()
        balances1 = adapter.fetch_balances("auth0|eric")
        balances2 = adapter.fetch_balances("auth0|eric")
        assert balances1 == balances2

    def test_returns_point_balances(self):
        adapter = FakeAwardWalletAdapter()
        balances = adapter.fetch_balances("auth0|eric")
        assert len(balances) > 0
        assert all(isinstance(b, PointBalance) for b in balances)

    def test_balances_have_decimal_cpp(self):
        adapter = FakeAwardWalletAdapter()
        balances = adapter.fetch_balances("auth0|eric")
        for b in balances:
            assert isinstance(b.cpp_baseline, Decimal)

    def test_returns_empty_for_unknown_user(self):
        adapter = FakeAwardWalletAdapter()
        balances = adapter.fetch_balances("auth0|unknown")
        assert balances == []

    def test_different_users_get_different_balances(self):
        adapter = FakeAwardWalletAdapter()
        eric = adapter.fetch_balances("auth0|eric")
        steve = adapter.fetch_balances("auth0|steve")
        assert eric != steve


class TestAwardWalletErrorHandling:
    def test_timeout_error(self):
        adapter = FakeAwardWalletAdapter(simulate_error="timeout")
        with pytest.raises(AwardWalletError, match="timeout"):
            adapter.fetch_balances("auth0|eric")

    def test_auth_failure_error(self):
        adapter = FakeAwardWalletAdapter(simulate_error="auth_failure")
        with pytest.raises(AwardWalletError, match="auth"):
            adapter.fetch_balances("auth0|eric")

    def test_rate_limit_error(self):
        adapter = FakeAwardWalletAdapter(simulate_error="rate_limit")
        with pytest.raises(AwardWalletError, match="rate limit"):
            adapter.fetch_balances("auth0|eric")

    def test_error_includes_context(self):
        adapter = FakeAwardWalletAdapter(simulate_error="timeout")
        with pytest.raises(AwardWalletError) as exc_info:
            adapter.fetch_balances("auth0|eric")
        assert "AwardWallet" in str(exc_info.value)
