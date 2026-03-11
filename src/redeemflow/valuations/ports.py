"""Valuations domain — ports (Protocol interfaces).

ValuationPort defines the contract for fetching CPP valuations per program.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from redeemflow.valuations.models import ProgramValuation


@runtime_checkable
class ValuationPort(Protocol):
    """Port for fetching loyalty program CPP valuations."""

    def get_valuation(self, program_code: str) -> ProgramValuation | None: ...

    def get_all(self) -> list[ProgramValuation]: ...
