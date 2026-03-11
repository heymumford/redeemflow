"""Portfolio domain — ports (Protocol interfaces).

PortfolioPort defines the full contract for fetching and syncing user loyalty balances.
BalanceFetcher is the minimal contract (fetch_balances only) for backward compatibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

from redeemflow.portfolio.models import PointBalance, UserPortfolio


class SyncStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass(frozen=True)
class SyncResult:
    """Result of a portfolio sync operation."""

    user_id: str
    status: SyncStatus
    programs_synced: int
    programs_failed: int
    message: str = ""


@runtime_checkable
class BalanceFetcher(Protocol):
    """Minimal port: fetch balances only. Backward-compatible."""

    def fetch_balances(self, user_id: str) -> list[PointBalance]: ...


@runtime_checkable
class PortfolioPort(Protocol):
    """Full port for fetching and syncing user loyalty program balances."""

    def fetch_balances(self, user_id: str) -> list[PointBalance]: ...

    def fetch_portfolio(self, user_id: str) -> UserPortfolio: ...

    def sync(self, user_id: str) -> SyncResult: ...
