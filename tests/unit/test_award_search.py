"""Tests for the award search module — Seats.aero integration."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from redeemflow.search.award_search import (
    AwardResult,
    AwardSearchProvider,
    FakeAwardSearchProvider,
    SeatsAeroAdapter,
)


class TestAwardResult:
    def test_frozen_dataclass(self) -> None:
        result = AwardResult(
            program="united",
            origin="SFO",
            destination="NRT",
            date="2026-06-15",
            cabin="business",
            points_required=80000,
            cash_value=Decimal("5600.00"),
            source="seats.aero",
            direct=True,
            available_seats=2,
        )
        with pytest.raises(FrozenInstanceError):
            result.program = "delta"  # type: ignore[misc]

    def test_all_fields(self) -> None:
        result = AwardResult(
            program="ana",
            origin="LAX",
            destination="NRT",
            date="2026-07-01",
            cabin="first",
            points_required=110000,
            cash_value=Decimal("16500.00"),
            source="seats.aero",
            direct=False,
            available_seats=None,
        )
        assert result.program == "ana"
        assert result.origin == "LAX"
        assert result.destination == "NRT"
        assert result.date == "2026-07-01"
        assert result.cabin == "first"
        assert result.points_required == 110000
        assert result.cash_value == Decimal("16500.00")
        assert result.source == "seats.aero"
        assert result.direct is False
        assert result.available_seats is None

    def test_cash_value_is_decimal(self) -> None:
        result = AwardResult(
            program="delta",
            origin="JFK",
            destination="CDG",
            date="2026-08-01",
            cabin="economy",
            points_required=30000,
            cash_value=Decimal("450.00"),
            source="test",
            direct=True,
            available_seats=5,
        )
        assert isinstance(result.cash_value, Decimal)


class TestFakeAwardSearchProvider:
    def test_returns_results_for_known_routes(self) -> None:
        provider = FakeAwardSearchProvider()
        results = provider.search(origin="SFO", destination="NRT", date="2026-06-15", cabin="business")
        assert len(results) > 0
        for r in results:
            assert isinstance(r, AwardResult)
            assert r.origin == "SFO"
            assert r.destination == "NRT"

    def test_unknown_route_returns_empty(self) -> None:
        provider = FakeAwardSearchProvider()
        results = provider.search(origin="XXX", destination="YYY", date="2026-06-15", cabin="economy")
        assert results == []

    def test_results_have_correct_cabin(self) -> None:
        provider = FakeAwardSearchProvider()
        results = provider.search(origin="JFK", destination="LHR", date="2026-06-15", cabin="business")
        if results:
            for r in results:
                assert r.cabin == "business"

    def test_implements_protocol(self) -> None:
        provider = FakeAwardSearchProvider()
        # Verify it satisfies AwardSearchProvider Protocol structurally
        assert hasattr(provider, "search")
        assert callable(provider.search)


class TestSeatsAeroAdapter:
    def test_implements_protocol(self) -> None:
        adapter = SeatsAeroAdapter(api_key="test-key")
        assert hasattr(adapter, "search")
        assert callable(adapter.search)

    def test_satisfies_protocol(self) -> None:
        adapter = SeatsAeroAdapter(api_key="test-key")
        assert isinstance(adapter, AwardSearchProvider)
