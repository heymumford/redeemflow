"""Tests for portfolio rebalancing."""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from redeemflow.portfolio.rebalance import RiskLevel, analyze_portfolio


class TestAnalyzePortfolio:
    def test_basic_analysis(self):
        balances = [
            {"program_code": "chase-ur", "program_name": "Chase UR", "points": 100000},
            {"program_code": "amex-mr", "program_name": "Amex MR", "points": 50000},
        ]
        report = analyze_portfolio(balances)
        assert len(report.balances) == 2
        assert report.concentration.total_programs == 2

    def test_concentrated_portfolio(self):
        balances = [
            {"program_code": "chase-ur", "program_name": "Chase UR", "points": 500000},
            {"program_code": "amex-mr", "program_name": "Amex MR", "points": 10000},
        ]
        report = analyze_portfolio(balances)
        assert report.concentration.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
        assert len(report.actions) > 0

    def test_diversified_portfolio(self):
        balances = [
            {"program_code": "chase-ur", "points": 30000},
            {"program_code": "amex-mr", "points": 30000},
            {"program_code": "united", "points": 25000},
            {"program_code": "hyatt", "points": 20000},
        ]
        report = analyze_portfolio(balances)
        assert report.concentration.risk_level == RiskLevel.LOW

    def test_single_program_is_critical(self):
        balances = [{"program_code": "chase-ur", "points": 100000}]
        report = analyze_portfolio(balances)
        assert report.concentration.risk_level == RiskLevel.CRITICAL
        assert report.concentration.largest_pct == Decimal("100.0")

    def test_empty_portfolio(self):
        report = analyze_portfolio([])
        assert report.concentration.total_programs == 0
        assert report.concentration.total_value == Decimal("0")

    def test_balances_sorted_by_value(self):
        balances = [
            {"program_code": "amex-mr", "points": 10000},
            {"program_code": "chase-ur", "points": 100000},
        ]
        report = analyze_portfolio(balances)
        assert report.balances[0].program_code == "chase-ur"

    def test_low_value_redeem_suggestion(self):
        balances = [
            {"program_code": "chase-ur", "points": 50000},
            {"program_code": "hilton", "points": 200000},
        ]
        report = analyze_portfolio(balances)
        redeem_actions = [a for a in report.actions if a.action_type == "redeem"]
        assert len(redeem_actions) >= 1
        assert redeem_actions[0].from_program == "hilton"

    def test_hhi_computed(self):
        balances = [
            {"program_code": "chase-ur", "points": 50000},
            {"program_code": "amex-mr", "points": 50000},
        ]
        report = analyze_portfolio(balances)
        assert report.concentration.herfindahl_index > 0

    def test_custom_valuations(self):
        balances = [{"program_code": "chase-ur", "points": 100000}]
        report = analyze_portfolio(balances, {"chase-ur": Decimal("2.00")})
        assert report.balances[0].cpp == Decimal("2.00")
        assert report.balances[0].value == Decimal("2000.00")

    def test_transfer_action_generated(self):
        balances = [
            {"program_code": "chase-ur", "points": 500000},
            {"program_code": "hyatt", "points": 10000},
        ]
        report = analyze_portfolio(balances)
        transfer_actions = [a for a in report.actions if a.action_type == "transfer"]
        assert len(transfer_actions) >= 1


class TestPortfolioRebalanceAPI:
    AUTH_HEADERS = {"Authorization": "Bearer test-token-eric"}

    @pytest.fixture
    def client(self):
        from redeemflow.app import create_app
        from redeemflow.ports import PortBundle

        return TestClient(create_app(ports=PortBundle()))

    def test_rebalance_endpoint(self, client):
        resp = client.post(
            "/api/portfolio/rebalance",
            json={
                "balances": [
                    {"program_code": "chase-ur", "program_name": "Chase UR", "points": 200000},
                    {"program_code": "amex-mr", "program_name": "Amex MR", "points": 50000},
                ],
            },
            headers=self.AUTH_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "concentration" in data
        assert "actions" in data

    def test_rebalance_requires_auth(self, client):
        resp = client.post("/api/portfolio/rebalance", json={"balances": []})
        assert resp.status_code == 401
