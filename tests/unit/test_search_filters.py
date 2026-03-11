"""Tests for search filters, sorting, and filtered search API."""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from redeemflow.search.award_search import AwardResult
from redeemflow.search.filters import (
    SearchFilters,
    SortDirection,
    SortField,
    apply_filters,
    compute_cpp,
    search_summary,
)


def _make_result(
    program="united",
    cabin="business",
    points=80000,
    cash=Decimal("5600"),
    direct=True,
    seats=2,
) -> AwardResult:
    return AwardResult(
        program=program,
        origin="SFO",
        destination="NRT",
        date="2026-06-15",
        cabin=cabin,
        points_required=points,
        cash_value=cash,
        source="fake",
        direct=direct,
        available_seats=seats,
    )


class TestComputeCpp:
    def test_basic_cpp(self):
        result = _make_result(points=80000, cash=Decimal("5600"))
        assert compute_cpp(result) == Decimal("7.00")

    def test_zero_points(self):
        result = _make_result(points=0)
        assert compute_cpp(result) == Decimal("0")

    def test_small_values(self):
        result = _make_result(points=10000, cash=Decimal("100"))
        assert compute_cpp(result) == Decimal("1.00")


class TestApplyFilters:
    def _results(self):
        return [
            _make_result(program="united", cabin="business", points=80000, cash=Decimal("5600"), seats=2),
            _make_result(program="ana", cabin="business", points=88000, cash=Decimal("6200"), seats=1),
            _make_result(program="united", cabin="economy", points=35000, cash=Decimal("800"), seats=5),
            _make_result(program="delta", cabin="business", points=70000, cash=Decimal("4200"), direct=False, seats=3),
        ]

    def test_no_filters(self):
        results = apply_filters(self._results(), SearchFilters())
        assert len(results) == 4

    def test_filter_by_cabin(self):
        results = apply_filters(self._results(), SearchFilters(cabins=["business"]))
        assert len(results) == 3
        assert all(r.result.cabin == "business" for r in results)

    def test_filter_by_program(self):
        results = apply_filters(self._results(), SearchFilters(programs=["united"]))
        assert len(results) == 2
        assert all(r.result.program == "united" for r in results)

    def test_filter_max_points(self):
        results = apply_filters(self._results(), SearchFilters(max_points=75000))
        assert all(r.result.points_required <= 75000 for r in results)

    def test_filter_min_points(self):
        results = apply_filters(self._results(), SearchFilters(min_points=80000))
        assert all(r.result.points_required >= 80000 for r in results)

    def test_filter_direct_only(self):
        results = apply_filters(self._results(), SearchFilters(direct_only=True))
        assert len(results) == 3
        assert all(r.result.direct for r in results)

    def test_filter_min_seats(self):
        results = apply_filters(self._results(), SearchFilters(min_seats=2))
        assert all(r.result.available_seats >= 2 for r in results)

    def test_filter_min_cpp(self):
        results = apply_filters(self._results(), SearchFilters(min_cpp=Decimal("5.0")))
        assert all(r.cpp >= Decimal("5.0") for r in results)

    def test_filter_max_cpp(self):
        results = apply_filters(self._results(), SearchFilters(max_cpp=Decimal("3.0")))
        assert all(r.cpp <= Decimal("3.0") for r in results)

    def test_combined_filters(self):
        results = apply_filters(
            self._results(),
            SearchFilters(cabins=["business"], direct_only=True, max_points=85000),
        )
        assert len(results) == 1
        assert results[0].result.program == "united"

    def test_sort_by_points_asc(self):
        results = apply_filters(
            self._results(),
            SearchFilters(sort_by=SortField.POINTS, sort_direction=SortDirection.ASC),
        )
        points = [r.result.points_required for r in results]
        assert points == sorted(points)

    def test_sort_by_points_desc(self):
        results = apply_filters(
            self._results(),
            SearchFilters(sort_by=SortField.POINTS, sort_direction=SortDirection.DESC),
        )
        points = [r.result.points_required for r in results]
        assert points == sorted(points, reverse=True)

    def test_sort_by_cpp(self):
        results = apply_filters(
            self._results(),
            SearchFilters(sort_by=SortField.CPP, sort_direction=SortDirection.DESC),
        )
        cpps = [r.cpp for r in results]
        assert cpps == sorted(cpps, reverse=True)

    def test_sort_by_value(self):
        results = apply_filters(
            self._results(),
            SearchFilters(sort_by=SortField.VALUE, sort_direction=SortDirection.DESC),
        )
        values = [r.result.cash_value for r in results]
        assert values == sorted(values, reverse=True)

    def test_limit(self):
        results = apply_filters(self._results(), SearchFilters(limit=2))
        assert len(results) == 2

    def test_value_rating_assigned(self):
        results = apply_filters(self._results(), SearchFilters())
        for r in results:
            assert r.value_rating in ("excellent", "good", "fair", "poor")

    def test_empty_results(self):
        results = apply_filters([], SearchFilters())
        assert len(results) == 0


class TestSearchSummary:
    def test_summary_with_results(self):
        results = apply_filters(
            [
                _make_result(program="united", points=80000, cash=Decimal("5600")),
                _make_result(program="ana", points=88000, cash=Decimal("6200")),
            ],
            SearchFilters(),
        )
        summary = search_summary(results)
        assert summary["total_results"] == 2
        assert "united" in summary["programs"]
        assert summary["best_value"] is not None

    def test_summary_empty(self):
        summary = search_summary([])
        assert summary["total_results"] == 0
        assert summary["best_value"] is None


class TestFilteredSearchAPI:
    AUTH_HEADERS = {"Authorization": "Bearer test-token-eric"}

    @pytest.fixture
    def client(self):
        from redeemflow.app import create_app
        from redeemflow.ports import PortBundle

        return TestClient(create_app(ports=PortBundle()))

    def test_filtered_search_returns_results(self, client):
        resp = client.post(
            "/api/award-search/filtered",
            json={"origin": "SFO", "destination": "NRT", "date": "2026-06-15"},
            headers=self.AUTH_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert "summary" in data

    def test_filtered_search_with_cabin_filter(self, client):
        resp = client.post(
            "/api/award-search/filtered",
            json={
                "origin": "SFO",
                "destination": "NRT",
                "date": "2026-06-15",
                "cabins": ["business"],
            },
            headers=self.AUTH_HEADERS,
        )
        assert resp.status_code == 200
        for r in resp.json()["results"]:
            assert r["cabin"] == "business"

    def test_filtered_search_with_sort(self, client):
        resp = client.post(
            "/api/award-search/filtered",
            json={
                "origin": "SFO",
                "destination": "NRT",
                "date": "2026-06-15",
                "sort_by": "cpp",
                "sort_direction": "desc",
            },
            headers=self.AUTH_HEADERS,
        )
        assert resp.status_code == 200
        results = resp.json()["results"]
        if len(results) > 1:
            cpps = [Decimal(r["cpp"]) for r in results]
            assert cpps == sorted(cpps, reverse=True)

    def test_filtered_search_includes_cpp(self, client):
        resp = client.post(
            "/api/award-search/filtered",
            json={"origin": "SFO", "destination": "NRT", "date": "2026-06-15"},
            headers=self.AUTH_HEADERS,
        )
        for r in resp.json()["results"]:
            assert "cpp" in r
            assert "value_rating" in r

    def test_filtered_search_requires_auth(self, client):
        resp = client.post(
            "/api/award-search/filtered",
            json={"origin": "SFO", "destination": "NRT", "date": "2026-06-15"},
        )
        assert resp.status_code == 401
