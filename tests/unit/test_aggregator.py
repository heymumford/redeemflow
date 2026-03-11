"""Tests for CPP aggregation engine — strategies, invariants, confidence levels."""

from __future__ import annotations

from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from redeemflow.valuations.aggregator import (
    AggregationStrategy,
    aggregate_cpp,
    batch_aggregate,
)
from redeemflow.valuations.models import ProgramValuation, ValuationSource
from redeemflow.valuations.seed_data import PROGRAM_VALUATIONS


def _make_valuation(
    cpps: dict[ValuationSource, Decimal],
    code: str = "test-program",
    name: str = "Test Program",
) -> ProgramValuation:
    return ProgramValuation(program_code=code, program_name=name, valuations=cpps)


class TestMedianStrategy:
    def test_single_source(self):
        val = _make_valuation({ValuationSource.TPG: Decimal("2.0")})
        agg = aggregate_cpp(val, AggregationStrategy.MEDIAN)
        assert agg.aggregated_cpp == Decimal("2.0")

    def test_two_sources(self):
        val = _make_valuation(
            {
                ValuationSource.TPG: Decimal("2.0"),
                ValuationSource.OMAAT: Decimal("1.6"),
            }
        )
        agg = aggregate_cpp(val, AggregationStrategy.MEDIAN)
        assert agg.aggregated_cpp == Decimal("1.8")

    def test_three_sources(self):
        val = _make_valuation(
            {
                ValuationSource.TPG: Decimal("2.0"),
                ValuationSource.OMAAT: Decimal("1.7"),
                ValuationSource.NERDWALLET: Decimal("1.5"),
            }
        )
        agg = aggregate_cpp(val, AggregationStrategy.MEDIAN)
        assert agg.aggregated_cpp == Decimal("1.7")


class TestMeanStrategy:
    def test_two_sources(self):
        val = _make_valuation(
            {
                ValuationSource.TPG: Decimal("2.0"),
                ValuationSource.OMAAT: Decimal("1.0"),
            }
        )
        agg = aggregate_cpp(val, AggregationStrategy.MEAN)
        assert agg.aggregated_cpp == Decimal("1.50")

    def test_four_sources(self):
        val = _make_valuation(
            {
                ValuationSource.TPG: Decimal("2.0"),
                ValuationSource.OMAAT: Decimal("1.7"),
                ValuationSource.NERDWALLET: Decimal("1.5"),
                ValuationSource.UPGRADED_POINTS: Decimal("2.0"),
            }
        )
        agg = aggregate_cpp(val, AggregationStrategy.MEAN)
        assert agg.aggregated_cpp == Decimal("1.80")


class TestWeightedStrategy:
    def test_weighted_with_defaults(self):
        val = _make_valuation(
            {
                ValuationSource.TPG: Decimal("2.0"),
                ValuationSource.OMAAT: Decimal("1.7"),
            }
        )
        agg = aggregate_cpp(val, AggregationStrategy.WEIGHTED)
        # TPG weight 1.0, OMAAT weight 1.2 → (2.0*1.0 + 1.7*1.2) / 2.2
        expected = ((Decimal("2.0") + Decimal("1.7") * Decimal("1.2")) / Decimal("2.2")).quantize(Decimal("0.01"))
        assert agg.aggregated_cpp == expected

    def test_weighted_with_custom_weights(self):
        val = _make_valuation(
            {
                ValuationSource.TPG: Decimal("2.0"),
                ValuationSource.OMAAT: Decimal("1.0"),
            }
        )
        weights = {
            ValuationSource.TPG: Decimal("3.0"),
            ValuationSource.OMAAT: Decimal("1.0"),
        }
        agg = aggregate_cpp(val, AggregationStrategy.WEIGHTED, weights=weights)
        # (2.0*3 + 1.0*1) / 4 = 1.75
        assert agg.aggregated_cpp == Decimal("1.75")


class TestAggregatedValuationMetadata:
    def test_spread_calculation(self):
        val = _make_valuation(
            {
                ValuationSource.TPG: Decimal("2.0"),
                ValuationSource.OMAAT: Decimal("1.5"),
            }
        )
        agg = aggregate_cpp(val)
        assert agg.spread == Decimal("0.5")

    def test_source_count(self):
        val = _make_valuation(
            {
                ValuationSource.TPG: Decimal("2.0"),
                ValuationSource.OMAAT: Decimal("1.5"),
                ValuationSource.NERDWALLET: Decimal("1.3"),
            }
        )
        agg = aggregate_cpp(val)
        assert agg.source_count == 3

    def test_confidence_high(self):
        val = _make_valuation(
            {
                ValuationSource.TPG: Decimal("2.0"),
                ValuationSource.OMAAT: Decimal("1.8"),
                ValuationSource.NERDWALLET: Decimal("1.9"),
            }
        )
        agg = aggregate_cpp(val)
        assert agg.confidence == "high"

    def test_confidence_medium(self):
        val = _make_valuation(
            {
                ValuationSource.TPG: Decimal("2.0"),
                ValuationSource.OMAAT: Decimal("1.0"),
            }
        )
        agg = aggregate_cpp(val)
        assert agg.confidence == "medium"

    def test_confidence_low(self):
        val = _make_valuation({ValuationSource.TPG: Decimal("2.0")})
        agg = aggregate_cpp(val)
        assert agg.confidence == "low"


class TestBatchAggregate:
    def test_all_seed_programs(self):
        results = batch_aggregate(PROGRAM_VALUATIONS)
        assert len(results) == len(PROGRAM_VALUATIONS)

    def test_all_results_have_valid_cpp(self):
        results = batch_aggregate(PROGRAM_VALUATIONS)
        for _code, agg in results.items():
            assert agg.aggregated_cpp > Decimal("0")
            assert agg.min_cpp <= agg.aggregated_cpp <= agg.max_cpp


class TestAPIEndpoints:
    """Test aggregation API routes via TestClient."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient

        from redeemflow.app import create_app
        from redeemflow.ports import PortBundle

        return TestClient(create_app(ports=PortBundle()))

    def test_get_single_valuation(self, client):
        resp = client.get("/api/valuations/chase-ur")
        assert resp.status_code == 200
        data = resp.json()
        assert data["program_code"] == "chase-ur"
        assert "aggregated_cpp" in data
        assert data["strategy"] == "median"
        assert data["confidence"] in ("high", "medium", "low")

    def test_get_valuation_with_mean_strategy(self, client):
        resp = client.get("/api/valuations/chase-ur?strategy=mean")
        assert resp.status_code == 200
        assert resp.json()["strategy"] == "mean"

    def test_get_valuation_unknown_program(self, client):
        resp = client.get("/api/valuations/nonexistent")
        assert resp.status_code == 404

    def test_get_valuation_invalid_strategy(self, client):
        resp = client.get("/api/valuations/chase-ur?strategy=invalid")
        assert resp.status_code == 400

    def test_list_all_valuations(self, client):
        resp = client.get("/api/valuations")
        assert resp.status_code == 200
        data = resp.json()
        assert data["strategy"] == "median"
        assert len(data["programs"]) == len(PROGRAM_VALUATIONS)

    def test_list_valuations_sorted_by_cpp_descending(self, client):
        resp = client.get("/api/valuations")
        programs = resp.json()["programs"]
        cpps = [Decimal(p["aggregated_cpp"]) for p in programs]
        assert cpps == sorted(cpps, reverse=True)


class TestPropertyBased:
    """Property-based tests for aggregation invariants."""

    @given(
        cpp1=st.decimals(min_value=Decimal("0.01"), max_value=Decimal("100.0"), places=2),
        cpp2=st.decimals(min_value=Decimal("0.01"), max_value=Decimal("100.0"), places=2),
    )
    @settings(max_examples=50)
    def test_aggregated_between_min_and_max(self, cpp1, cpp2):
        val = _make_valuation(
            {
                ValuationSource.TPG: cpp1,
                ValuationSource.OMAAT: cpp2,
            }
        )
        for strategy in AggregationStrategy:
            agg = aggregate_cpp(val, strategy)
            assert agg.min_cpp <= agg.aggregated_cpp <= agg.max_cpp

    @given(
        cpp=st.decimals(min_value=Decimal("0.01"), max_value=Decimal("100.0"), places=2),
    )
    @settings(max_examples=30)
    def test_single_source_all_strategies_equal(self, cpp):
        val = _make_valuation({ValuationSource.TPG: cpp})
        for strategy in AggregationStrategy:
            agg = aggregate_cpp(val, strategy)
            assert agg.aggregated_cpp == cpp

    @given(
        cpp1=st.decimals(min_value=Decimal("0.01"), max_value=Decimal("100.0"), places=2),
        cpp2=st.decimals(min_value=Decimal("0.01"), max_value=Decimal("100.0"), places=2),
        cpp3=st.decimals(min_value=Decimal("0.01"), max_value=Decimal("100.0"), places=2),
    )
    @settings(max_examples=30)
    def test_spread_is_non_negative(self, cpp1, cpp2, cpp3):
        val = _make_valuation(
            {
                ValuationSource.TPG: cpp1,
                ValuationSource.OMAAT: cpp2,
                ValuationSource.NERDWALLET: cpp3,
            }
        )
        agg = aggregate_cpp(val)
        assert agg.spread >= Decimal("0")
