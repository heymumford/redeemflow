"""Tests for exchange platform analysis — buy, sell, swap rates."""

from __future__ import annotations

from decimal import Decimal

import pytest

from redeemflow.redemptions.exchange import (
    EXCHANGE_RATES,
    SWAP_RATES,
    analyze_buy,
    analyze_sell,
    find_exchange_rates,
    find_swap_rates,
)


class TestExchangeData:
    def test_buy_rates_exist(self):
        buy_rates = [r for r in EXCHANGE_RATES if r.exchange_type.value == "buy"]
        assert len(buy_rates) >= 5

    def test_sell_rates_exist(self):
        sell_rates = [r for r in EXCHANGE_RATES if r.exchange_type.value == "sell"]
        assert len(sell_rates) >= 2

    def test_swap_rates_exist(self):
        assert len(SWAP_RATES) >= 2

    def test_effective_rate_accounts_for_fees(self):
        for rate in EXCHANGE_RATES:
            assert rate.effective_rate > Decimal("0")

    def test_find_rates_for_united(self):
        rates = find_exchange_rates("united")
        assert len(rates) >= 2  # buy + sell

    def test_find_rates_unknown_program(self):
        rates = find_exchange_rates("nonexistent")
        assert rates == []

    def test_find_swaps_for_marriott(self):
        swaps = find_swap_rates("marriott")
        assert len(swaps) >= 1
        assert swaps[0].target_program == "united"


class TestAnalyzeBuy:
    def test_buy_united_points(self):
        analysis = analyze_buy("united", 50000)
        assert analysis is not None
        assert analysis.cash_cost_or_value > Decimal("0")
        assert analysis.break_even_redemption_cpp > Decimal("0")

    def test_buy_with_high_target_cpp(self):
        analysis = analyze_buy("hilton", 50000, Decimal("5.0"))
        assert analysis is not None
        assert analysis.recommendation == "buy"

    def test_buy_with_low_target_cpp(self):
        analysis = analyze_buy("united", 50000, Decimal("0.5"))
        assert analysis is not None
        assert analysis.recommendation == "hold"

    def test_buy_outside_limits(self):
        analysis = analyze_buy("united", 1)  # Below min_transaction
        assert analysis is not None
        assert analysis.recommendation == "hold"

    def test_buy_nonexistent_program(self):
        analysis = analyze_buy("nonexistent", 50000)
        assert analysis is None


class TestAnalyzeSell:
    def test_sell_united_points(self):
        analysis = analyze_sell("united", 50000)
        assert analysis is not None
        assert analysis.cash_cost_or_value > Decimal("0")

    def test_sell_hilton_points_is_poor(self):
        analysis = analyze_sell("hilton", 50000)
        assert analysis is not None
        # Hilton sell rate is 0.004 * (1-5%) = ~0.38 CPP — should recommend hold
        assert analysis.recommendation == "hold"

    def test_sell_nonexistent_program(self):
        analysis = analyze_sell("nonexistent", 50000)
        assert analysis is None


class TestAPIEndpoints:
    AUTH = {"Authorization": "Bearer test-token-eric"}

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient

        from redeemflow.app import create_app
        from redeemflow.ports import PortBundle

        return TestClient(create_app(ports=PortBundle()))

    def test_get_exchange_rates(self, client):
        resp = client.get("/api/exchange-rates/united", headers=self.AUTH)
        assert resp.status_code == 200
        data = resp.json()
        assert data["program"] == "united"
        assert data["count"] >= 2

    def test_get_exchange_rates_unknown(self, client):
        resp = client.get("/api/exchange-rates/nonexistent", headers=self.AUTH)
        assert resp.status_code == 200
        assert resp.json()["count"] == 0

    def test_buy_analysis_endpoint(self, client):
        resp = client.post(
            "/api/exchange/buy-analysis",
            json={"program": "united", "points": 50000},
            headers=self.AUTH,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "recommendation" in data
        assert "cash_cost" in data

    def test_sell_analysis_endpoint(self, client):
        resp = client.post(
            "/api/exchange/sell-analysis",
            json={"program": "united", "points": 50000},
            headers=self.AUTH,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "recommendation" in data

    def test_swap_rates_endpoint(self, client):
        resp = client.get("/api/exchange/swaps/marriott", headers=self.AUTH)
        assert resp.status_code == 200
        data = resp.json()
        assert data["source_program"] == "marriott"
        assert data["count"] >= 1

    def test_swap_rates_unknown(self, client):
        resp = client.get("/api/exchange/swaps/nonexistent", headers=self.AUTH)
        assert resp.status_code == 200
        assert resp.json()["count"] == 0

    def test_requires_auth(self, client):
        resp = client.get("/api/exchange-rates/united")
        assert resp.status_code == 401
