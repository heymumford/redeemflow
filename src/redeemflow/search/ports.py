"""Search domain — ports (Protocol interfaces).

AwardSearchPort defines the contract for searching award availability
across loyalty programs.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from redeemflow.search.award_search import AwardResult


@runtime_checkable
class AwardSearchPort(Protocol):
    """Port for searching award availability across loyalty programs."""

    def search(self, origin: str, destination: str, date: str, cabin: str) -> list[AwardResult]: ...
