"""Tests for trip comparison — side-by-side redemption ranking."""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from redeemflow.search.trip_comparison import (
    ComparisonResult,
    RedemptionOption,
    compare_options,
    rank_options,
)


def _opt(
    code: str = "united",
    name: str = "United MileagePlus",
    points: int = 70000,
    cash: str = "1500.00",
    cpp: str = "2.14",
    cabin: str = "business",
    avail: str = "available",
    stops: int = 0,
    transfer: bool = False,
) -> RedemptionOption:
    return RedemptionOption(
        program_code=code,
        program_name=name,
        points_required=points,
        cash_price=Decimal(cash),
        cpp=Decimal(cpp),
        cabin_class=cabin,
        route="SFO-NRT",
        stops=stops,
        transfer_required=transfer,
        availability=avail,
    )


class TestRedemptionOption:
    def test_frozen(self):
        opt = _opt()
        with pytest.raises(AttributeError):
            opt.points_required = 50000  # type: ignore[misc]

    def test_defaults(self):
        opt = RedemptionOption(
            program_code="aa",
            program_name="AAdvantage",
            points_required=60000,
            cash_price=Decimal("1200"),
            cpp=Decimal("2.0"),
        )
        assert opt.cabin_class == "economy"
        assert opt.availability == "available"
        assert opt.transfer_required is False


class TestCompareOptions:
    def test_single_option(self):
        opts = [_opt()]
        result = compare_options("SFO-NRT", opts)
        assert isinstance(result, ComparisonResult)
        assert result.best_value == opts[0]
        assert result.value_spread == Decimal("0")

    def test_best_value_highest_cpp(self):
        opts = [
            _opt(code="united", cpp="2.14", points=70000),
            _opt(code="aa", name="AAdvantage", cpp="2.50", points=60000),
            _opt(code="delta", name="SkyMiles", cpp="1.80", points=80000),
        ]
        result = compare_options("SFO-NRT", opts)
        assert result.best_value.program_code == "aa"

    def test_cheapest_points(self):
        opts = [
            _opt(code="united", points=70000, cpp="2.14"),
            _opt(code="aa", name="AAdvantage", points=50000, cpp="2.50"),
        ]
        result = compare_options("SFO-NRT", opts)
        assert result.cheapest_points.program_code == "aa"

    def test_best_availability_prefers_available(self):
        opts = [
            _opt(code="united", cpp="2.50", avail="waitlist"),
            _opt(code="aa", name="AAdvantage", cpp="2.00", avail="available"),
        ]
        result = compare_options("SFO-NRT", opts)
        assert result.best_availability.program_code == "aa"

    def test_availability_tiebreak_by_cpp(self):
        opts = [
            _opt(code="united", cpp="2.50", avail="available"),
            _opt(code="aa", name="AAdvantage", cpp="2.00", avail="available"),
        ]
        result = compare_options("SFO-NRT", opts)
        assert result.best_availability.program_code == "united"

    def test_value_spread(self):
        opts = [
            _opt(code="united", cpp="2.50"),
            _opt(code="aa", name="AAdvantage", cpp="1.50"),
        ]
        result = compare_options("SFO-NRT", opts)
        assert result.value_spread == Decimal("1.00")

    def test_options_sorted_by_cpp_desc(self):
        opts = [
            _opt(code="delta", name="SkyMiles", cpp="1.80"),
            _opt(code="aa", name="AAdvantage", cpp="2.50"),
            _opt(code="united", cpp="2.14"),
        ]
        result = compare_options("SFO-NRT", opts)
        cpps = [o.cpp for o in result.options]
        assert cpps == sorted(cpps, reverse=True)

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="At least one"):
            compare_options("SFO-NRT", [])

    def test_cheapest_excludes_unavailable(self):
        opts = [
            _opt(code="united", points=30000, avail="unavailable"),
            _opt(code="aa", name="AAdvantage", points=60000, avail="available"),
        ]
        result = compare_options("SFO-NRT", opts)
        assert result.cheapest_points.program_code == "aa"

    def test_cheapest_fallback_when_all_unavailable(self):
        opts = [
            _opt(code="united", points=30000, avail="unavailable"),
            _opt(code="aa", name="AAdvantage", points=60000, avail="unavailable"),
        ]
        result = compare_options("SFO-NRT", opts)
        assert result.cheapest_points.program_code == "united"


class TestRankOptions:
    def test_empty(self):
        assert rank_options([]) == []

    def test_single(self):
        ranked = rank_options([_opt()])
        assert len(ranked) == 1
        assert ranked[0]["composite_score"] > 0

    def test_highest_composite_first(self):
        opts = [
            _opt(code="united", cpp="2.50", points=70000, avail="available"),
            _opt(code="aa", name="AAdvantage", cpp="1.50", points=90000, avail="waitlist"),
        ]
        ranked = rank_options(opts)
        assert ranked[0]["program_code"] == "united"

    def test_custom_weights(self):
        opts = [
            _opt(code="united", cpp="1.00", points=30000, avail="available"),
            _opt(code="aa", name="AAdvantage", cpp="3.00", points=90000, avail="available"),
        ]
        # Heavy cost weight should favor cheaper points
        ranked = rank_options(
            opts,
            weights={
                "value": Decimal("0.10"),
                "cost": Decimal("0.80"),
                "availability": Decimal("0.10"),
            },
        )
        assert ranked[0]["program_code"] == "united"

    def test_all_scores_present(self):
        ranked = rank_options([_opt()])
        r = ranked[0]
        assert "value_score" in r
        assert "cost_score" in r
        assert "availability_score" in r
        assert "composite_score" in r


class TestTripComparisonAPI:
    AUTH_HEADERS = {"Authorization": "Bearer test-token-eric"}

    @pytest.fixture
    def client(self):
        from redeemflow.app import create_app
        from redeemflow.ports import PortBundle

        return TestClient(create_app(ports=PortBundle()))

    def test_compare_trips(self, client):
        resp = client.post(
            "/api/trip-compare",
            json={
                "route": "SFO-NRT",
                "options": [
                    {
                        "program_code": "united",
                        "program_name": "United MileagePlus",
                        "points_required": 70000,
                        "cash_price": "1500.00",
                        "cpp": "2.14",
                        "cabin_class": "business",
                    },
                    {
                        "program_code": "aa",
                        "program_name": "AAdvantage",
                        "points_required": 60000,
                        "cash_price": "1500.00",
                        "cpp": "2.50",
                        "cabin_class": "business",
                    },
                ],
            },
            headers=self.AUTH_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["best_value"]["program_code"] == "aa"
        assert len(data["options"]) == 2

    def test_compare_requires_auth(self, client):
        resp = client.post("/api/trip-compare", json={"route": "SFO-NRT", "options": []})
        assert resp.status_code == 401

    def test_compare_empty_options(self, client):
        resp = client.post(
            "/api/trip-compare",
            json={"route": "SFO-NRT", "options": []},
            headers=self.AUTH_HEADERS,
        )
        assert resp.status_code == 400
