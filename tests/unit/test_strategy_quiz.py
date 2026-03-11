"""Tests for strategy quiz classification engine."""

from __future__ import annotations

import pytest

from redeemflow.recommendations.strategy_quiz import (
    QuizAnswers,
    RedemptionPreference,
    SpendLevel,
    StrategyArchetype,
    TravelFrequency,
    classify,
)


def _answers(**overrides) -> QuizAnswers:
    defaults = {
        "travel_frequency": TravelFrequency.OCCASIONAL,
        "preferred_cabin": "economy",
        "redemption_preference": RedemptionPreference.NO_PREFERENCE,
        "monthly_spend": SpendLevel.MEDIUM,
        "flexibility": False,
        "hotel_priority": "midrange",
    }
    defaults.update(overrides)
    return QuizAnswers(**defaults)


class TestClassification:
    def test_maximizer_profile(self):
        answers = _answers(
            travel_frequency=TravelFrequency.FREQUENT,
            preferred_cabin="business",
            redemption_preference=RedemptionPreference.TRANSFER_PARTNERS,
            flexibility=True,
        )
        result = classify(answers)
        assert result.archetype == StrategyArchetype.MAXIMIZER

    def test_simplifier_profile(self):
        answers = _answers(
            travel_frequency=TravelFrequency.RARELY,
            preferred_cabin="economy",
            redemption_preference=RedemptionPreference.CASH_BACK,
            flexibility=False,
            hotel_priority="budget",
        )
        result = classify(answers)
        assert result.archetype == StrategyArchetype.SIMPLIFIER

    def test_aspirational_profile(self):
        answers = _answers(
            travel_frequency=TravelFrequency.FREQUENT,
            preferred_cabin="first",
            hotel_priority="luxury",
        )
        result = classify(answers)
        assert result.archetype == StrategyArchetype.ASPIRATIONAL

    def test_accumulator_profile(self):
        answers = _answers(
            travel_frequency=TravelFrequency.RARELY,
            monthly_spend=SpendLevel.HIGH,
            redemption_preference=RedemptionPreference.TRAVEL_PORTAL,
        )
        result = classify(answers)
        assert result.archetype == StrategyArchetype.ACCUMULATOR

    def test_result_has_recommendations(self):
        result = classify(_answers())
        assert len(result.recommended_programs) > 0
        assert len(result.recommended_cards) > 0

    def test_result_has_strategies(self):
        result = classify(_answers())
        assert len(result.top_strategy) > 0
        assert len(result.secondary_strategy) > 0

    def test_score_breakdown_has_all_archetypes(self):
        result = classify(_answers())
        assert len(result.score_breakdown) == 4
        for archetype in StrategyArchetype:
            assert archetype.value in result.score_breakdown

    def test_all_scores_non_negative(self):
        result = classify(_answers())
        for score in result.score_breakdown.values():
            assert score >= 0


class TestQuizEndpoint:
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient

        from redeemflow.app import create_app
        from redeemflow.ports import PortBundle

        return TestClient(create_app(ports=PortBundle()))

    def test_quiz_returns_archetype(self, client):
        resp = client.post(
            "/api/strategy-quiz",
            json={
                "travel_frequency": "frequent",
                "preferred_cabin": "business",
                "redemption_preference": "transfer_partners",
                "monthly_spend": "high",
                "flexibility": True,
                "hotel_priority": "luxury",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["archetype"] in [a.value for a in StrategyArchetype]
        assert "recommended_programs" in data
        assert "recommended_cards" in data

    def test_quiz_minimal_input(self, client):
        resp = client.post(
            "/api/strategy-quiz",
            json={"travel_frequency": "occasional"},
        )
        assert resp.status_code == 200
        assert "archetype" in resp.json()

    def test_quiz_invalid_frequency(self, client):
        resp = client.post(
            "/api/strategy-quiz",
            json={"travel_frequency": "invalid"},
        )
        assert resp.status_code == 400
