"""Portfolio domain — ports (Protocol interfaces)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from redeemflow.portfolio.models import PointBalance


@runtime_checkable
class BalanceFetcher(Protocol):
    def fetch_balances(self, user_id: str) -> list[PointBalance]: ...
