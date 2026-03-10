"""Search domain — award availability search.

Defines the AwardSearchProvider Protocol and implementations:
- SeatsAeroAdapter: real Seats.aero API for live award availability
- FakeAwardSearchProvider: deterministic test data

Beck: Protocol boundary — same contract, different implementations.
Fowler: Anti-corruption layer — translate Seats.aero schema to our models.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol, runtime_checkable

import httpx

from redeemflow.middleware.logging import get_logger

logger = get_logger("award_search")


@dataclass(frozen=True)
class AwardResult:
    """A single award search result."""

    program: str
    origin: str
    destination: str
    date: str
    cabin: str  # "economy", "premium_economy", "business", "first"
    points_required: int
    cash_value: Decimal
    source: str
    direct: bool
    available_seats: int | None


@runtime_checkable
class AwardSearchProvider(Protocol):
    def search(self, origin: str, destination: str, date: str, cabin: str) -> list[AwardResult]: ...


# Map Seats.aero cabin classes to our cabin names
_CABIN_MAP: dict[str, str] = {
    "Y": "economy",
    "W": "premium_economy",
    "J": "business",
    "F": "first",
}


class SeatsAeroError(Exception):
    """Raised when Seats.aero API interaction fails."""


class SeatsAeroAdapter:
    """Real Seats.aero API adapter — searches live award availability.

    Seats.aero API: https://seats.aero/api
    Authentication: API key as partner_id parameter.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://seats.aero/api/availability",
        timeout: float = 30.0,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url
        self._timeout = timeout

    def search(self, origin: str, destination: str, date: str, cabin: str) -> list[AwardResult]:
        """Search for award availability on a route."""
        # Map our cabin name to Seats.aero cabin code
        cabin_code = next(
            (k for k, v in _CABIN_MAP.items() if v == cabin),
            cabin[0].upper() if cabin else "J",
        )

        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.get(
                    self._base_url,
                    headers={"Partner-Authorization": self._api_key},
                    params={
                        "origin": origin,
                        "destination": destination,
                        "date": date,
                        "cabin": cabin_code,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.TimeoutException as e:
            raise SeatsAeroError(f"Seats.aero API timeout: {e}") from e
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise SeatsAeroError("Seats.aero auth failure: invalid API key") from e
            if e.response.status_code == 429:
                raise SeatsAeroError("Seats.aero rate limit exceeded") from e
            raise SeatsAeroError(f"Seats.aero API error: {e.response.status_code}") from e
        except httpx.HTTPError as e:
            raise SeatsAeroError(f"Seats.aero connection error: {e}") from e

        return self._parse_results(data, origin, destination, date, cabin)

    def _parse_results(self, data: dict, origin: str, destination: str, date: str, cabin: str) -> list[AwardResult]:
        """Translate Seats.aero response to our AwardResult model."""
        results: list[AwardResult] = []
        flights = data.get("data", [])

        for flight in flights:
            program = flight.get("source", "unknown").lower()
            points = int(flight.get("miles", 0) or flight.get("points", 0))
            cash = Decimal(str(flight.get("cash_price", "0")))
            direct = flight.get("stops", 1) == 0
            seats = flight.get("seats", None)
            if seats is not None:
                seats = int(seats)

            if points > 0:
                results.append(
                    AwardResult(
                        program=program,
                        origin=origin,
                        destination=destination,
                        date=date,
                        cabin=cabin,
                        points_required=points,
                        cash_value=cash,
                        source="seats.aero",
                        direct=direct,
                        available_seats=seats,
                    )
                )

        logger.info(
            "award_search_completed",
            origin=origin,
            destination=destination,
            cabin=cabin,
            results=len(results),
        )
        return results


# --- Deterministic test data for FakeAwardSearchProvider ---

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


class FakeAwardSearchProvider:
    """In-memory award search provider with deterministic test data."""

    def search(self, origin: str, destination: str, date: str, cabin: str) -> list[AwardResult]:
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
