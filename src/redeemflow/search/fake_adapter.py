"""Search domain — fake adapter for testing.

In-memory AwardSearchPort implementation with deterministic route data.
Zero network calls.
"""

from __future__ import annotations

from decimal import Decimal

from redeemflow.search.award_search import AwardResult

_FAKE_ROUTES: dict[tuple[str, str, str], list[AwardResult]] = {
    ("SFO", "NRT", "business"): [
        AwardResult(
            program="united",
            origin="SFO",
            destination="NRT",
            date="2026-06-15",
            cabin="business",
            points_required=80000,
            cash_value=Decimal("5600.00"),
            source="fake",
            direct=True,
            available_seats=2,
        ),
        AwardResult(
            program="ana",
            origin="SFO",
            destination="NRT",
            date="2026-06-15",
            cabin="business",
            points_required=88000,
            cash_value=Decimal("6200.00"),
            source="fake",
            direct=True,
            available_seats=1,
        ),
    ],
    ("SFO", "NRT", "first"): [
        AwardResult(
            program="ana",
            origin="SFO",
            destination="NRT",
            date="2026-06-15",
            cabin="first",
            points_required=110000,
            cash_value=Decimal("16500.00"),
            source="fake",
            direct=True,
            available_seats=1,
        ),
    ],
    ("JFK", "LHR", "business"): [
        AwardResult(
            program="virgin-atlantic",
            origin="JFK",
            destination="LHR",
            date="2026-06-15",
            cabin="business",
            points_required=47500,
            cash_value=Decimal("3800.00"),
            source="fake",
            direct=True,
            available_seats=4,
        ),
        AwardResult(
            program="british-airways",
            origin="JFK",
            destination="LHR",
            date="2026-06-15",
            cabin="business",
            points_required=60000,
            cash_value=Decimal("4500.00"),
            source="fake",
            direct=True,
            available_seats=2,
        ),
    ],
    ("JFK", "DOH", "business"): [
        AwardResult(
            program="american",
            origin="JFK",
            destination="DOH",
            date="2026-06-15",
            cabin="business",
            points_required=70000,
            cash_value=Decimal("6000.00"),
            source="fake",
            direct=True,
            available_seats=2,
        ),
    ],
}


class FakeAwardSearchAdapter:
    """In-memory award search adapter with deterministic test data."""

    def __init__(self, simulate_error: str | None = None) -> None:
        self._simulate_error = simulate_error

    def search(self, origin: str, destination: str, date: str, cabin: str) -> list[AwardResult]:
        if self._simulate_error == "timeout":
            raise TimeoutError("Award search timed out")

        key = (origin, destination, cabin)
        results = _FAKE_ROUTES.get(key, [])
        # Update the date field to match the requested date
        return [
            AwardResult(
                program=r.program,
                origin=r.origin,
                destination=r.destination,
                date=date,
                cabin=r.cabin,
                points_required=r.points_required,
                cash_value=r.cash_value,
                source=r.source,
                direct=r.direct,
                available_seats=r.available_seats,
            )
            for r in results
        ]
