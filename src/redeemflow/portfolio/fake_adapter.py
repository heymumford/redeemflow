"""Portfolio domain — fake adapter for testing.

In-memory PortfolioPort implementation with deterministic test data.
Zero network calls. Supports error simulation.
"""

from __future__ import annotations

from decimal import Decimal

from redeemflow.portfolio.models import PointBalance, UserPortfolio
from redeemflow.portfolio.ports import SyncResult, SyncStatus

_TEST_BALANCES: dict[str, list[PointBalance]] = {
    "auth0|eric": [
        PointBalance(program_code="UA", points=87000, cpp_baseline=Decimal("1.5")),
        PointBalance(program_code="MR", points=120000, cpp_baseline=Decimal("1.0")),
        PointBalance(program_code="UR", points=65000, cpp_baseline=Decimal("1.5")),
        PointBalance(program_code="HH", points=210000, cpp_baseline=Decimal("0.5")),
    ],
    "auth0|steve": [
        PointBalance(program_code="AA", points=95000, cpp_baseline=Decimal("1.4")),
        PointBalance(program_code="DL", points=42000, cpp_baseline=Decimal("1.2")),
        PointBalance(program_code="MR", points=75000, cpp_baseline=Decimal("1.0")),
    ],
}


class FakePortfolioAdapter:
    """In-memory portfolio adapter with deterministic test data."""

    def __init__(self, simulate_error: str | None = None) -> None:
        self._simulate_error = simulate_error
        self._data: dict[str, list[PointBalance]] = {k: list(v) for k, v in _TEST_BALANCES.items()}

    def fetch_balances(self, user_id: str) -> list[PointBalance]:
        if self._simulate_error == "timeout":
            raise TimeoutError("Portfolio fetch timed out")
        return list(self._data.get(user_id, []))

    def fetch_portfolio(self, user_id: str) -> UserPortfolio:
        balances = self.fetch_balances(user_id)
        return UserPortfolio(user_id=user_id, balances=tuple(balances))

    def sync(self, user_id: str) -> SyncResult:
        if self._simulate_error == "sync_failed":
            return SyncResult(
                user_id=user_id,
                status=SyncStatus.FAILED,
                programs_synced=0,
                programs_failed=1,
                message="Simulated sync failure",
            )
        balances = self._data.get(user_id, [])
        return SyncResult(
            user_id=user_id,
            status=SyncStatus.SUCCESS,
            programs_synced=len(balances),
            programs_failed=0,
        )


# Backwards-compatible alias for existing tests
FakeBalanceFetcher = FakePortfolioAdapter
