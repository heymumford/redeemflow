"""Tests for trip planning — multi-segment itinerary with value metrics."""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from redeemflow.search.trip_planner import (
    BookingMethod,
    SegmentType,
    Trip,
    TripSegment,
    build_trip_from_segments,
)


def _segment(
    segment_id: str = "seg_1",
    points_cost: int = 50000,
    cash_cost: str = "800",
    booking_method: BookingMethod = BookingMethod.POINTS,
    program_code: str = "united",
) -> TripSegment:
    return TripSegment(
        segment_id=segment_id,
        segment_type=SegmentType.FLIGHT,
        description="SFO-NRT",
        origin="SFO",
        destination="NRT",
        date="2025-06-15",
        points_cost=points_cost,
        cash_cost=Decimal(cash_cost),
        program_code=program_code,
        booking_method=booking_method,
        cpp=Decimal(cash_cost) * 100 / points_cost if points_cost > 0 else Decimal("0"),
    )


class TestTripSegment:
    def test_frozen(self):
        seg = _segment()
        with pytest.raises(AttributeError):
            seg.points_cost = 99999  # type: ignore[misc]

    def test_defaults(self):
        seg = TripSegment(segment_id="s1", segment_type=SegmentType.FLIGHT, description="test")
        assert seg.points_cost == 0
        assert seg.cash_cost == Decimal("0")
        assert seg.booking_method == BookingMethod.POINTS


class TestTrip:
    def test_add_and_remove_segment(self):
        trip = Trip(trip_id="t1", name="Japan Trip")
        trip.add_segment(_segment("seg_1"))
        trip.add_segment(_segment("seg_2", program_code="hyatt"))
        assert len(trip.segments) == 2

        removed = trip.remove_segment("seg_1")
        assert removed is True
        assert len(trip.segments) == 1

    def test_remove_nonexistent(self):
        trip = Trip(trip_id="t1", name="Trip")
        assert trip.remove_segment("nope") is False

    def test_summarize_single_segment(self):
        trip = Trip(trip_id="t1", name="Trip")
        trip.add_segment(_segment(points_cost=50000, cash_cost="800"))
        s = trip.summarize()
        assert s.total_segments == 1
        assert s.total_points == 50000
        assert s.avg_cpp == Decimal("1.60")
        assert "united" in s.programs_used

    def test_summarize_mixed_booking(self):
        trip = Trip(trip_id="t1", name="Mixed")
        trip.add_segment(_segment("seg_1", points_cost=50000, cash_cost="800", booking_method=BookingMethod.POINTS))
        trip.add_segment(
            _segment("seg_2", points_cost=0, cash_cost="200", booking_method=BookingMethod.CASH, program_code="")
        )
        s = trip.summarize()
        assert s.total_points == 50000
        assert s.total_cash == Decimal("200")
        assert s.total_value == Decimal("1000")
        assert s.value_vs_cash == Decimal("800")

    def test_summarize_empty(self):
        trip = Trip(trip_id="t1", name="Empty")
        s = trip.summarize()
        assert s.total_segments == 0
        assert s.total_points == 0
        assert s.avg_cpp == Decimal("0")

    def test_summarize_programs_sorted(self):
        trip = Trip(trip_id="t1", name="Multi")
        trip.add_segment(_segment("s1", program_code="united"))
        trip.add_segment(_segment("s2", program_code="amex-mr"))
        trip.add_segment(_segment("s3", program_code="united"))
        s = trip.summarize()
        assert s.programs_used == ["amex-mr", "united"]


class TestBuildTripFromSegments:
    def test_basic_build(self):
        data = [
            {
                "description": "SFO to NRT",
                "origin": "SFO",
                "destination": "NRT",
                "date": "2025-06-15",
                "points_cost": 70000,
                "cash_cost": "1200",
                "program_code": "united",
                "segment_type": "flight",
                "booking_method": "points",
            }
        ]
        trip = build_trip_from_segments("t1", "Japan", data)
        assert trip.trip_id == "t1"
        assert len(trip.segments) == 1
        seg = trip.segments[0]
        assert seg.segment_id == "seg_1"
        assert seg.points_cost == 70000
        assert seg.cpp == Decimal("1.71")

    def test_default_values(self):
        trip = build_trip_from_segments("t1", "Minimal", [{}])
        seg = trip.segments[0]
        assert seg.segment_type == SegmentType.FLIGHT
        assert seg.booking_method == BookingMethod.POINTS
        assert seg.points_cost == 0

    def test_invalid_enums_default(self):
        trip = build_trip_from_segments("t1", "Bad", [{"segment_type": "spaceship", "booking_method": "barter"}])
        seg = trip.segments[0]
        assert seg.segment_type == SegmentType.FLIGHT
        assert seg.booking_method == BookingMethod.POINTS

    def test_multiple_segments_auto_ids(self):
        data = [{}, {}, {}]
        trip = build_trip_from_segments("t1", "Multi", data)
        ids = [s.segment_id for s in trip.segments]
        assert ids == ["seg_1", "seg_2", "seg_3"]

    def test_custom_segment_id(self):
        trip = build_trip_from_segments("t1", "Custom", [{"segment_id": "my_seg"}])
        assert trip.segments[0].segment_id == "my_seg"

    def test_hotel_segment(self):
        trip = build_trip_from_segments(
            "t1",
            "Hotel",
            [
                {
                    "segment_type": "hotel",
                    "description": "Park Hyatt Tokyo",
                    "points_cost": 25000,
                    "cash_cost": "450",
                    "program_code": "hyatt",
                    "date": "2025-06-15",
                    "end_date": "2025-06-18",
                }
            ],
        )
        seg = trip.segments[0]
        assert seg.segment_type == SegmentType.HOTEL
        assert seg.end_date == "2025-06-18"


class TestTripAPI:
    AUTH_HEADERS = {"Authorization": "Bearer test-token-eric"}

    @pytest.fixture
    def client(self):
        from redeemflow.app import create_app
        from redeemflow.ports import PortBundle
        from redeemflow.search.trip_planner import _TRIP_COUNTER, _TRIPS

        _TRIPS.clear()
        _TRIP_COUNTER.clear()
        return TestClient(create_app(ports=PortBundle()))

    def test_list_trips_empty(self, client):
        resp = client.get("/api/trips", headers=self.AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["trips"] == []

    def test_create_trip(self, client):
        resp = client.post(
            "/api/trips",
            json={
                "name": "Japan 2025",
                "segments": [
                    {
                        "description": "SFO-NRT",
                        "origin": "SFO",
                        "destination": "NRT",
                        "points_cost": 70000,
                        "cash_cost": "1200",
                        "program_code": "united",
                        "segment_type": "flight",
                    }
                ],
            },
            headers=self.AUTH_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["trip_id"] == "trip_1"
        assert data["total_segments"] == 1
        assert data["total_points"] == 70000

    def test_create_and_get_trip(self, client):
        client.post(
            "/api/trips",
            json={
                "name": "Europe",
                "segments": [
                    {"description": "JFK-LHR", "points_cost": 60000, "cash_cost": "900", "program_code": "amex-mr"},
                    {"description": "Ritz London", "segment_type": "hotel", "points_cost": 40000, "cash_cost": "500"},
                ],
            },
            headers=self.AUTH_HEADERS,
        )
        resp = client.get("/api/trips/trip_1", headers=self.AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_segments"] == 2
        assert len(data["segments"]) == 2
        assert data["segments"][0]["segment_id"] == "seg_1"

    def test_get_nonexistent_trip(self, client):
        resp = client.get("/api/trips/nope", headers=self.AUTH_HEADERS)
        assert resp.status_code == 404
        assert "detail" in resp.json()

    def test_trips_require_auth(self, client):
        assert client.get("/api/trips").status_code == 401
        assert client.post("/api/trips", json={"name": "X"}).status_code == 401

    def test_trip_value_metrics(self, client):
        resp = client.post(
            "/api/trips",
            json={
                "name": "Value Test",
                "segments": [
                    {"points_cost": 50000, "cash_cost": "800", "booking_method": "points"},
                ],
            },
            headers=self.AUTH_HEADERS,
        )
        data = resp.json()
        assert "avg_cpp" in data
        assert Decimal(data["avg_cpp"]) == Decimal("1.60")

    def test_create_empty_trip(self, client):
        resp = client.post(
            "/api/trips",
            json={"name": "Empty Trip"},
            headers=self.AUTH_HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["total_segments"] == 0

    def test_list_after_create(self, client):
        client.post("/api/trips", json={"name": "Trip A"}, headers=self.AUTH_HEADERS)
        client.post("/api/trips", json={"name": "Trip B"}, headers=self.AUTH_HEADERS)
        resp = client.get("/api/trips", headers=self.AUTH_HEADERS)
        assert len(resp.json()["trips"]) == 2
