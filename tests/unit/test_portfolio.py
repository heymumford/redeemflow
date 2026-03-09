"""Slice 3: Portfolio domain — loyalty accounts and point balances."""

from __future__ import annotations

from decimal import Decimal

import pytest

from redeemflow.portfolio.fake_adapter import FakeBalanceFetcher
from redeemflow.portfolio.models import LoyaltyAccount, LoyaltyProgram, PointBalance
from redeemflow.portfolio.ports import BalanceFetcher


class TestLoyaltyProgram:
    def test_program_is_frozen(self):
        program = LoyaltyProgram(code="UA", name="United MileagePlus")
        with pytest.raises(AttributeError):
            program.code = "AA"

    def test_program_equality_by_code(self):
        a = LoyaltyProgram(code="UA", name="United MileagePlus")
        b = LoyaltyProgram(code="UA", name="Different Name")
        assert a == b


class TestPointBalance:
    def test_balance_is_frozen(self):
        balance = PointBalance(program_code="UA", points=50000, cpp_baseline=Decimal("1.5"))
        with pytest.raises(AttributeError):
            balance.points = 0

    def test_estimated_value_cents(self):
        balance = PointBalance(program_code="UA", points=50000, cpp_baseline=Decimal("1.5"))
        assert balance.estimated_value_cents == 75000

    def test_estimated_value_dollars(self):
        balance = PointBalance(program_code="UA", points=50000, cpp_baseline=Decimal("1.5"))
        assert balance.estimated_value_dollars == Decimal("750.00")

    def test_zero_points_zero_value(self):
        balance = PointBalance(program_code="UA", points=0, cpp_baseline=Decimal("1.5"))
        assert balance.estimated_value_cents == 0
        assert balance.estimated_value_dollars == Decimal("0.00")


class TestLoyaltyAccount:
    def test_account_is_frozen(self):
        account = LoyaltyAccount(
            user_id="auth0|abc",
            program_code="UA",
            member_id="UA123456",
        )
        with pytest.raises(AttributeError):
            account.member_id = "changed"

    def test_account_requires_user_and_program(self):
        account = LoyaltyAccount(
            user_id="auth0|abc",
            program_code="UA",
            member_id="UA123456",
        )
        assert account.user_id == "auth0|abc"
        assert account.program_code == "UA"


class TestFakeBalanceFetcher:
    def test_implements_protocol(self):
        fetcher = FakeBalanceFetcher()
        assert isinstance(fetcher, BalanceFetcher)

    def test_returns_balances_for_known_user(self):
        fetcher = FakeBalanceFetcher()
        balances = fetcher.fetch_balances("auth0|eric")
        assert len(balances) > 0
        assert all(isinstance(b, PointBalance) for b in balances)

    def test_returns_empty_for_unknown_user(self):
        fetcher = FakeBalanceFetcher()
        balances = fetcher.fetch_balances("auth0|nobody")
        assert balances == []

    def test_total_portfolio_value(self):
        fetcher = FakeBalanceFetcher()
        balances = fetcher.fetch_balances("auth0|eric")
        total_cents = sum(b.estimated_value_cents for b in balances)
        assert total_cents > 0
