"""Tests for seasonal pricing intelligence."""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from redeemflow.search.seasonal_pricing import (
    BookingUrgency,
    Season,
    SeasonalAdvisory,
    compute_booking_window,
    compute_price_index,
    get_season,
    get_seasonal_patterns,
    seasonal_advisory,
)


class TestGetSeason:
    def test_peak_summer(self):
        assert get_season("SFO-NRT", 7) == Season.PEAK

    def test_shoulder_spring(self):
        assert get_season("SFO-NRT", 4) == Season.SHOULDER

    def test_off_peak_winter(self):
        assert get_season("SFO-NRT", 2) == Season.OFF_PEAK

    def test_peak_december(self):
        assert get_season("SFO-NRT", 12) == Season.PEAK

    def test_unknown_route_defaults(self):
        assert get_season("ORD-SIN", 7) == Season.PEAK
        assert get_season("ORD-SIN", 4) == Season.SHOULDER
        assert get_season("ORD-SIN", 2) == Season.OFF_PEAK


class TestSeasonalPatterns:
    def test_known_route(self):
        patterns = get_seasonal_patterns("SFO-NRT")
        assert len(patterns) == 3
        seasons = {p.season for p in patterns}
        assert seasons == {Season.PEAK, Season.SHOULDER, Season.OFF_PEAK}

    def test_unknown_route(self):
        assert get_seasonal_patterns("ORD-SIN") == []

    def test_all_months_covered(self):
        patterns = get_seasonal_patterns("SFO-NRT")
        all_months = set()
        for p in patterns:
            all_months.update(p.months)
        assert all_months == set(range(1, 13))


class TestPriceIndex:
    def test_peak_above_100(self):
        idx = compute_price_index("SFO-NRT", 7)
        assert idx > Decimal("100")

    def test_off_peak_below_100(self):
        idx = compute_price_index("SFO-NRT", 2)
        assert idx < Decimal("100")

    def test_unknown_route_returns_100(self):
        assert compute_price_index("ORD-SIN", 7) == Decimal("100")


class TestBookingWindow:
    def test_peak_book_early(self):
        window = compute_booking_window("SFO-NRT", 7)
        assert window.ideal_book_months_ahead == 6
        assert window.urgency == BookingUrgency.BOOK_NOW

    def test_shoulder_moderate(self):
        window = compute_booking_window("SFO-NRT", 4)
        assert window.ideal_book_months_ahead == 3
        assert window.urgency == BookingUrgency.GOOD_TIME

    def test_off_peak_flexible(self):
        window = compute_booking_window("SFO-NRT", 2)
        assert window.ideal_book_months_ahead == 1
        assert window.urgency == BookingUrgency.WAIT

    def test_savings_pct_increases_with_peak(self):
        peak = compute_booking_window("SFO-NRT", 7)
        off = compute_booking_window("SFO-NRT", 2)
        assert peak.savings_vs_last_minute_pct > off.savings_vs_last_minute_pct


class TestSeasonalAdvisory:
    def test_advisory_structure(self):
        adv = seasonal_advisory("SFO-NRT", 7)
        assert isinstance(adv, SeasonalAdvisory)
        assert adv.current_season == Season.PEAK
        assert adv.current_month == 7
        assert len(adv.patterns) == 3
        assert len(adv.best_value_months) > 0
        assert len(adv.worst_value_months) > 0

    def test_best_months_are_cheapest(self):
        adv = seasonal_advisory("SFO-NRT", 7)
        # Best value months should be off-peak months (1, 2, 11)
        for m in adv.best_value_months:
            assert get_season("SFO-NRT", m) == Season.OFF_PEAK

    def test_unknown_route_still_works(self):
        adv = seasonal_advisory("ORD-SIN", 5)
        assert adv.route == "ORD-SIN"
        assert adv.current_month == 5


class TestSeasonalPricingAPI:
    AUTH_HEADERS = {"Authorization": "Bearer test-token-eric"}

    @pytest.fixture
    def client(self):
        from redeemflow.app import create_app
        from redeemflow.ports import PortBundle

        return TestClient(create_app(ports=PortBundle()))

    def test_seasonal_known_route(self, client):
        resp = client.get("/api/seasonal/SFO-NRT?month=7", headers=self.AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["current_season"] == "peak"
        assert data["price_index"] is not None

    def test_seasonal_unknown_route(self, client):
        resp = client.get("/api/seasonal/ORD-SIN?month=5", headers=self.AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["route"] == "ORD-SIN"

    def test_seasonal_requires_auth(self, client):
        resp = client.get("/api/seasonal/SFO-NRT?month=7")
        assert resp.status_code == 401
