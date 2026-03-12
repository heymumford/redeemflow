"""Tests for sweet spots discovery engine."""

from __future__ import annotations

from decimal import Decimal

import pytest

from redeemflow.search.sweet_spots import (
    ALL_SWEET_SPOTS,
    SweetSpotCategory,
    ValueRating,
    find_sweet_spots,
)


class TestSweetSpotsData:
    def test_data_is_populated(self):
        assert len(ALL_SWEET_SPOTS) >= 10

    def test_all_have_positive_cpp(self):
        for spot in ALL_SWEET_SPOTS:
            assert spot.effective_cpp > Decimal("0")

    def test_all_have_positive_multiplier(self):
        for spot in ALL_SWEET_SPOTS:
            assert spot.value_multiplier > Decimal("0")

    def test_all_categories_represented(self):
        categories = {spot.category for spot in ALL_SWEET_SPOTS}
        assert SweetSpotCategory.FLIGHTS in categories
        assert SweetSpotCategory.HOTELS in categories
        assert SweetSpotCategory.TRANSFERS in categories

    def test_effective_cpp_equals_cash_over_points(self):
        for spot in ALL_SWEET_SPOTS:
            expected = (spot.cash_equivalent / Decimal(spot.points_required) * Decimal(100)).quantize(Decimal("0.01"))
            assert spot.effective_cpp == expected


class TestFindSweetSpots:
    def test_no_filter_returns_all(self):
        spots = find_sweet_spots()
        assert len(spots) == len(ALL_SWEET_SPOTS)

    def test_filter_by_flights(self):
        spots = find_sweet_spots(category=SweetSpotCategory.FLIGHTS)
        for spot in spots:
            assert spot.category == SweetSpotCategory.FLIGHTS

    def test_filter_by_hotels(self):
        spots = find_sweet_spots(category=SweetSpotCategory.HOTELS)
        for spot in spots:
            assert spot.category == SweetSpotCategory.HOTELS

    def test_filter_by_program(self):
        spots = find_sweet_spots(program="hyatt")
        for spot in spots:
            assert spot.program == "hyatt"

    def test_filter_by_min_rating_good(self):
        spots = find_sweet_spots(min_rating=ValueRating.GOOD)
        for spot in spots:
            assert spot.rating in (ValueRating.GOOD, ValueRating.EXCELLENT, ValueRating.EXCEPTIONAL)

    def test_filter_by_min_rating_excellent(self):
        spots = find_sweet_spots(min_rating=ValueRating.EXCELLENT)
        for spot in spots:
            assert spot.rating in (ValueRating.EXCELLENT, ValueRating.EXCEPTIONAL)

    def test_sorted_by_multiplier_descending(self):
        spots = find_sweet_spots()
        multipliers = [s.value_multiplier for s in spots]
        assert multipliers == sorted(multipliers, reverse=True)

    def test_combined_filters(self):
        spots = find_sweet_spots(category=SweetSpotCategory.FLIGHTS, min_rating=ValueRating.GOOD)
        for spot in spots:
            assert spot.category == SweetSpotCategory.FLIGHTS
            assert spot.rating in (ValueRating.GOOD, ValueRating.EXCELLENT, ValueRating.EXCEPTIONAL)


class TestAPIEndpoint:
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient

        from redeemflow.app import create_app
        from redeemflow.ports import PortBundle

        return TestClient(create_app(ports=PortBundle()))

    def test_list_sweet_spots(self, client):
        resp = client.get("/api/sweet-spots")
        assert resp.status_code == 200
        data = resp.json()
        assert "count" in data
        assert "sweet_spots" in data
        assert data["count"] == len(data["sweet_spots"])

    def test_filter_by_category(self, client):
        resp = client.get("/api/sweet-spots?category=flights")
        assert resp.status_code == 200
        for spot in resp.json()["sweet_spots"]:
            assert spot["category"] == "flights"

    def test_filter_by_program(self, client):
        resp = client.get("/api/sweet-spots?program=hyatt")
        assert resp.status_code == 200
        for spot in resp.json()["sweet_spots"]:
            assert spot["program"] == "hyatt"

    def test_filter_by_min_rating(self, client):
        resp = client.get("/api/sweet-spots?min_rating=excellent")
        assert resp.status_code == 200
        for spot in resp.json()["sweet_spots"]:
            assert spot["rating"] in ("excellent", "exceptional")

    def test_invalid_category(self, client):
        resp = client.get("/api/sweet-spots?category=invalid")
        assert resp.status_code == 400
        assert "detail" in resp.json()
