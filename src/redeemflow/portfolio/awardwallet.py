"""Portfolio domain — AwardWallet ACL adapter.

Implements BalanceFetcher Protocol. Real API calls stubbed for now;
FakeAwardWalletAdapter provides deterministic test data.
"""

from __future__ import annotations

from decimal import Decimal

from redeemflow.portfolio.models import PointBalance


class AwardWalletError(Exception):
    """Raised when AwardWallet API interaction fails."""


class AwardWalletAdapter:
    """Real AwardWallet API adapter — stubbed, real calls behind feature flag."""

    def __init__(self, api_key: str, base_url: str = "https://api.awardwallet.com") -> None:
        self._api_key = api_key
        self._base_url = base_url

    def fetch_balances(self, user_id: str) -> list[PointBalance]:
        raise NotImplementedError("Real AwardWallet integration not yet enabled")


class FakeAwardWalletAdapter:
    """In-memory AwardWallet adapter with deterministic test data.

    Supports error simulation for testing timeout, auth failure, and rate limit scenarios.
    """

    _BALANCES: dict[str, list[PointBalance]] = {
        "auth0|eric": [
            PointBalance(program_code="chase-ur", points=95000, cpp_baseline=Decimal("1.85")),
            PointBalance(program_code="amex-mr", points=130000, cpp_baseline=Decimal("1.85")),
            PointBalance(program_code="united", points=87000, cpp_baseline=Decimal("1.15")),
            PointBalance(program_code="hyatt", points=42000, cpp_baseline=Decimal("1.77")),
            PointBalance(program_code="hilton", points=310000, cpp_baseline=Decimal("0.47")),
        ],
        "auth0|steve": [
            PointBalance(program_code="delta", points=62000, cpp_baseline=Decimal("1.15")),
            PointBalance(program_code="american", points=105000, cpp_baseline=Decimal("1.53")),
            PointBalance(program_code="marriott", points=180000, cpp_baseline=Decimal("0.73")),
        ],
    }

    def __init__(self, simulate_error: str | None = None) -> None:
        self._simulate_error = simulate_error

    def fetch_balances(self, user_id: str) -> list[PointBalance]:
        if self._simulate_error == "timeout":
            raise AwardWalletError("AwardWallet API timeout: request timed out after 30s")
        if self._simulate_error == "auth_failure":
            raise AwardWalletError("AwardWallet auth failure: invalid API key")
        if self._simulate_error == "rate_limit":
            raise AwardWalletError("AwardWallet rate limit exceeded: retry after 60s")

        return list(self._BALANCES.get(user_id, []))
