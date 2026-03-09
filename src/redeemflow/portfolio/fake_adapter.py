"""Portfolio domain — fake adapter for walking skeleton.

Replaced by AwardWallet ACL adapter in Sprint 2.
"""

from __future__ import annotations

from decimal import Decimal

from redeemflow.portfolio.models import PointBalance


class FakeBalanceFetcher:
    """In-memory balance fetcher with hardcoded test data."""

    _BALANCES: dict[str, list[PointBalance]] = {
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

    def fetch_balances(self, user_id: str) -> list[PointBalance]:
        return list(self._BALANCES.get(user_id, []))
