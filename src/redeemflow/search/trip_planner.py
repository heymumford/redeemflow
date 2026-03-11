"""Trip planning — multi-leg itinerary with points allocation.

Beck: A trip is a sequence of segments, each with its own optimization.
Fowler: Aggregate — trip owns segments and computes total value.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum


class SegmentType(str, Enum):
    FLIGHT = "flight"
    HOTEL = "hotel"
    CAR = "car"
    EXPERIENCE = "experience"


class BookingMethod(str, Enum):
    POINTS = "points"
    CASH = "cash"
    POINTS_PLUS_CASH = "points_plus_cash"


@dataclass(frozen=True)
class TripSegment:
    """A single leg of a trip."""

    segment_id: str
    segment_type: SegmentType
    description: str
    origin: str = ""
    destination: str = ""
    date: str = ""
    end_date: str = ""
    points_cost: int = 0
    cash_cost: Decimal = Decimal("0")
    program_code: str = ""
    booking_method: BookingMethod = BookingMethod.POINTS
    cpp: Decimal = Decimal("0")
    notes: str = ""


@dataclass(frozen=True)
class TripSummary:
    """Computed trip-level metrics."""

    total_segments: int
    total_points: int
    total_cash: Decimal
    total_value: Decimal
    avg_cpp: Decimal
    programs_used: list[str]
    segments: list[TripSegment]
    value_vs_cash: Decimal  # How much more value vs paying cash for everything


@dataclass
class Trip:
    """A multi-segment trip itinerary."""

    trip_id: str
    name: str
    segments: list[TripSegment] = field(default_factory=list)

    def add_segment(self, segment: TripSegment) -> None:
        self.segments.append(segment)

    def remove_segment(self, segment_id: str) -> bool:
        before = len(self.segments)
        self.segments = [s for s in self.segments if s.segment_id != segment_id]
        return len(self.segments) < before

    def summarize(self) -> TripSummary:
        """Compute trip-level metrics."""
        total_points = sum(s.points_cost for s in self.segments)
        total_cash = sum(
            (s.cash_cost for s in self.segments if s.booking_method == BookingMethod.CASH),
            Decimal("0"),
        )
        total_value = sum((s.cash_cost for s in self.segments), Decimal("0"))
        programs = sorted({s.program_code for s in self.segments if s.program_code})

        avg_cpp = Decimal("0")
        if total_points > 0:
            points_value = sum(
                (s.cash_cost for s in self.segments if s.booking_method == BookingMethod.POINTS),
                Decimal("0"),
            )
            avg_cpp = (points_value * 100 / total_points).quantize(Decimal("0.01"))

        # Value vs cash: total_value minus actual cash spent
        value_vs_cash = total_value - total_cash

        return TripSummary(
            total_segments=len(self.segments),
            total_points=total_points,
            total_cash=total_cash,
            total_value=total_value,
            avg_cpp=avg_cpp,
            programs_used=programs,
            segments=list(self.segments),
            value_vs_cash=value_vs_cash,
        )


def build_trip_from_segments(
    trip_id: str,
    name: str,
    segments_data: list[dict],
) -> Trip:
    """Build a trip from raw segment data."""
    trip = Trip(trip_id=trip_id, name=name)

    for i, seg in enumerate(segments_data):
        cash_cost = Decimal(str(seg.get("cash_cost", "0")))
        points_cost = seg.get("points_cost", 0)

        cpp = Decimal("0")
        if points_cost > 0 and cash_cost > 0:
            cpp = (cash_cost * 100 / points_cost).quantize(Decimal("0.01"))

        try:
            booking = BookingMethod(seg.get("booking_method", "points"))
        except ValueError:
            booking = BookingMethod.POINTS

        try:
            seg_type = SegmentType(seg.get("segment_type", "flight"))
        except ValueError:
            seg_type = SegmentType.FLIGHT

        trip.add_segment(
            TripSegment(
                segment_id=seg.get("segment_id", f"seg_{i + 1}"),
                segment_type=seg_type,
                description=seg.get("description", ""),
                origin=seg.get("origin", ""),
                destination=seg.get("destination", ""),
                date=seg.get("date", ""),
                end_date=seg.get("end_date", ""),
                points_cost=points_cost,
                cash_cost=cash_cost,
                program_code=seg.get("program_code", ""),
                booking_method=booking,
                cpp=cpp,
                notes=seg.get("notes", ""),
            )
        )

    return trip


# In-memory trip store
_TRIPS: dict[str, dict[str, Trip]] = {}  # user_id -> {trip_id -> Trip}
_TRIP_COUNTER: dict[str, int] = {}


def save_trip(user_id: str, trip: Trip) -> Trip:
    if user_id not in _TRIPS:
        _TRIPS[user_id] = {}
    _TRIPS[user_id][trip.trip_id] = trip
    return trip


def get_trips(user_id: str) -> list[Trip]:
    return list(_TRIPS.get(user_id, {}).values())


def get_trip(user_id: str, trip_id: str) -> Trip | None:
    return _TRIPS.get(user_id, {}).get(trip_id)


def next_trip_id(user_id: str) -> str:
    count = _TRIP_COUNTER.get(user_id, 0) + 1
    _TRIP_COUNTER[user_id] = count
    return f"trip_{count}"
