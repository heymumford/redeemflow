"""Slice 4: Recommendations domain — CPP-based redemption advice."""

from __future__ import annotations

from decimal import Decimal

import pytest

from redeemflow.portfolio.models import PointBalance
from redeemflow.recommendations.engine import RecommendationEngine
from redeemflow.recommendations.models import Recommendation


class TestRecommendation:
    def test_recommendation_is_frozen(self):
        rec = Recommendation(
            program_code="UA",
            action="Transfer to Hyatt",
            rationale="Hyatt offers 2.0 CPP vs 1.5 CPP baseline",
            cpp_gain=Decimal("0.5"),
            points_involved=50000,
        )
        with pytest.raises(AttributeError):
            rec.action = "changed"


class TestRecommendationEngine:
    def setup_method(self):
        self.engine = RecommendationEngine()

    def test_no_balances_no_recommendations(self):
        recs = self.engine.recommend([])
        assert recs == []

    def test_single_balance_gets_recommendation(self):
        balances = [
            PointBalance(program_code="UA", points=50000, cpp_baseline=Decimal("1.5")),
        ]
        recs = self.engine.recommend(balances)
        assert len(recs) >= 1
        assert all(isinstance(r, Recommendation) for r in recs)

    def test_recommendations_sorted_by_cpp_gain_descending(self):
        balances = [
            PointBalance(program_code="UA", points=50000, cpp_baseline=Decimal("1.5")),
            PointBalance(program_code="AA", points=80000, cpp_baseline=Decimal("1.4")),
            PointBalance(program_code="MR", points=100000, cpp_baseline=Decimal("1.0")),
        ]
        recs = self.engine.recommend(balances)
        gains = [r.cpp_gain for r in recs]
        assert gains == sorted(gains, reverse=True)

    def test_recommendation_has_positive_cpp_gain(self):
        balances = [
            PointBalance(program_code="UA", points=50000, cpp_baseline=Decimal("1.5")),
        ]
        recs = self.engine.recommend(balances)
        for r in recs:
            assert r.cpp_gain > 0

    def test_low_balance_excluded(self):
        balances = [
            PointBalance(program_code="UA", points=100, cpp_baseline=Decimal("1.5")),
        ]
        recs = self.engine.recommend(balances)
        assert recs == []

    def test_multiple_programs_each_get_recommendation(self):
        balances = [
            PointBalance(program_code="UA", points=50000, cpp_baseline=Decimal("1.5")),
            PointBalance(program_code="MR", points=100000, cpp_baseline=Decimal("1.0")),
        ]
        recs = self.engine.recommend(balances)
        program_codes = {r.program_code for r in recs}
        assert len(program_codes) >= 2
