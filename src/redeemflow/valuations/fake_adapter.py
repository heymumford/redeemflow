"""Valuations domain — fake adapter for testing.

In-memory ValuationPort implementation seeded from existing seed data.
Zero network calls.
"""

from __future__ import annotations

from redeemflow.valuations.models import ProgramValuation
from redeemflow.valuations.seed_data import PROGRAM_VALUATIONS


class FakeValuationAdapter:
    """In-memory valuation adapter seeded with deterministic CPP data."""

    def __init__(self, data: dict[str, ProgramValuation] | None = None) -> None:
        self._data: dict[str, ProgramValuation] = dict(data) if data else dict(PROGRAM_VALUATIONS)

    def get_valuation(self, program_code: str) -> ProgramValuation | None:
        return self._data.get(program_code)

    def get_all(self) -> list[ProgramValuation]:
        return list(self._data.values())
