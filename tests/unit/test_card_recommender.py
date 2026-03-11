"""Tests for spend-pattern-aware card recommender."""

from __future__ import annotations

from decimal import Decimal

import pytest

from redeemflow.recommendations.card_recommender import recommend_cards, recommend_combo, score_card
from redeemflow.valuations.seed_data import CREDIT_CARDS, PROGRAM_VALUATIONS

SAMPLE_SPEND = {
    "dining": Decimal("500"),
    "travel": Decimal("300"),
    "groceries": Decimal("600"),
    "other": Decimal("1000"),
}


class TestScoreCard:
    def test_sapphire_reserve_dining_heavy(self):
        card = CREDIT_CARDS["chase-sapphire-reserve"]
        val = PROGRAM_VALUATIONS["chase-ur"]
        score = score_card(card, "chase-sapphire-reserve", SAMPLE_SPEND, val)
        assert score.total_points_earned > 0
        assert score.points_value > Decimal("0")
        assert score.net_value == score.points_value - card.net_annual_fee

    def test_zero_spend_yields_zero_points(self):
        card = CREDIT_CARDS["chase-sapphire-reserve"]
        val = PROGRAM_VALUATIONS["chase-ur"]
        score = score_card(card, "chase-sapphire-reserve", {}, val)
        assert score.total_points_earned == 0

    def test_no_valuation_uses_1cpp(self):
        card = CREDIT_CARDS["chase-sapphire-reserve"]
        score = score_card(card, "chase-sapphire-reserve", SAMPLE_SPEND, None)
        assert score.points_value > Decimal("0")

    def test_category_breakdown_populated(self):
        card = CREDIT_CARDS["amex-gold"]
        val = PROGRAM_VALUATIONS["amex-mr"]
        score = score_card(card, "amex-gold", SAMPLE_SPEND, val)
        assert "dining" in score.category_breakdown
        assert "groceries" in score.category_breakdown


class TestRecommendCards:
    def test_returns_ranked_list(self):
        scores = recommend_cards(SAMPLE_SPEND, CREDIT_CARDS, PROGRAM_VALUATIONS)
        values = [s.net_value for s in scores]
        assert values == sorted(values, reverse=True)

    def test_max_results_limit(self):
        scores = recommend_cards(SAMPLE_SPEND, CREDIT_CARDS, PROGRAM_VALUATIONS, max_results=3)
        assert len(scores) == 3

    def test_all_cards_scored(self):
        scores = recommend_cards(SAMPLE_SPEND, CREDIT_CARDS, PROGRAM_VALUATIONS, max_results=100)
        assert len(scores) == len(CREDIT_CARDS)


class TestRecommendCombo:
    def test_primary_and_secondary_different_issuers(self):
        combo = recommend_combo(SAMPLE_SPEND, CREDIT_CARDS, PROGRAM_VALUATIONS)
        assert combo.primary_card is not None
        if combo.secondary_card is not None:
            assert combo.primary_card.issuer != combo.secondary_card.issuer

    def test_combined_value_is_sum(self):
        combo = recommend_combo(SAMPLE_SPEND, CREDIT_CARDS, PROGRAM_VALUATIONS)
        expected = combo.primary_card.net_value
        if combo.secondary_card:
            expected += combo.secondary_card.net_value
        assert combo.combined_net_value == expected

    def test_strategy_summary_non_empty(self):
        combo = recommend_combo(SAMPLE_SPEND, CREDIT_CARDS, PROGRAM_VALUATIONS)
        assert len(combo.strategy_summary) > 0


class TestAPIEndpoints:
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient

        from redeemflow.app import create_app
        from redeemflow.ports import PortBundle

        return TestClient(create_app(ports=PortBundle()))

    def test_recommend_cards_endpoint(self, client):
        resp = client.post(
            "/api/recommend-cards",
            json={"monthly_spend": {"dining": 500, "travel": 300}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "recommendations" in data
        assert len(data["recommendations"]) <= 5

    def test_recommend_cards_with_max_results(self, client):
        resp = client.post(
            "/api/recommend-cards",
            json={"monthly_spend": {"dining": 500}, "max_results": 2},
        )
        assert resp.status_code == 200
        assert len(resp.json()["recommendations"]) == 2

    def test_recommend_combo_endpoint(self, client):
        resp = client.post(
            "/api/recommend-combo",
            json={"monthly_spend": {"dining": 500, "groceries": 600, "travel": 300}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "primary_card" in data
        assert "strategy_summary" in data

    def test_recommend_combo_different_issuers(self, client):
        resp = client.post(
            "/api/recommend-combo",
            json={"monthly_spend": {"dining": 500, "travel": 300, "other": 1000}},
        )
        data = resp.json()
        if data["secondary_card"] is not None:
            assert data["primary_card"]["issuer"] != data["secondary_card"]["issuer"]
