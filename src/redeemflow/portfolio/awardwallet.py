"""Portfolio domain — AwardWallet ACL adapter.

Implements BalanceFetcher Protocol. AwardWalletAdapter calls the real API.
FakeAwardWalletAdapter provides deterministic test data.

Beck: Protocol boundary — both sides satisfy the same contract.
Fowler: Anti-corruption layer — translate external schema to our models.
"""

from __future__ import annotations

from decimal import Decimal

import httpx

from redeemflow.middleware.logging import get_logger
from redeemflow.portfolio.models import PointBalance

logger = get_logger("awardwallet")

# Map AwardWallet program names to our program codes
_PROGRAM_MAP: dict[str, str] = {
    "Chase Ultimate Rewards": "chase-ur",
    "American Express Membership Rewards": "amex-mr",
    "Citi ThankYou Points": "citi-typ",
    "Capital One Miles": "cap1-miles",
    "United MileagePlus": "united",
    "American Airlines AAdvantage": "american",
    "Delta SkyMiles": "delta",
    "Hilton Honors": "hilton",
    "Hyatt World of Hyatt": "hyatt",
    "Marriott Bonvoy": "marriott",
    "Southwest Rapid Rewards": "southwest",
    "JetBlue TrueBlue": "jetblue",
}

# Default CPP baselines when AwardWallet doesn't provide them
_DEFAULT_CPP: dict[str, Decimal] = {
    "chase-ur": Decimal("1.85"),
    "amex-mr": Decimal("1.85"),
    "citi-typ": Decimal("1.60"),
    "cap1-miles": Decimal("1.85"),
    "united": Decimal("1.15"),
    "american": Decimal("1.53"),
    "delta": Decimal("1.15"),
    "hilton": Decimal("0.47"),
    "hyatt": Decimal("1.77"),
    "marriott": Decimal("0.73"),
    "southwest": Decimal("1.36"),
    "jetblue": Decimal("1.30"),
}


class AwardWalletError(Exception):
    """Raised when AwardWallet API interaction fails."""


class AwardWalletAdapter:
    """Real AwardWallet API adapter — calls /api/v2/accounts for balance data.

    AwardWallet API docs: https://awardwallet.com/api
    Authentication: API key as query parameter or header.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.awardwallet.com/v2",
        timeout: float = 30.0,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url
        self._timeout = timeout

    def fetch_balances(self, user_id: str) -> list[PointBalance]:
        """Fetch all loyalty balances for a user from AwardWallet."""
        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.get(
                    f"{self._base_url}/accounts",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    params={"user_id": user_id},
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.TimeoutException as e:
            raise AwardWalletError(f"AwardWallet API timeout: {e}") from e
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AwardWalletError("AwardWallet auth failure: invalid API key") from e
            if e.response.status_code == 429:
                raise AwardWalletError("AwardWallet rate limit exceeded") from e
            raise AwardWalletError(f"AwardWallet API error: {e.response.status_code}") from e
        except httpx.HTTPError as e:
            raise AwardWalletError(f"AwardWallet connection error: {e}") from e

        return self._parse_accounts(data)

    def _parse_accounts(self, data: dict) -> list[PointBalance]:
        """Translate AwardWallet response to our PointBalance model."""
        accounts = data.get("accounts", [])
        balances: list[PointBalance] = []

        for acct in accounts:
            program_name = acct.get("program", "")
            program_code = _PROGRAM_MAP.get(program_name, program_name.lower().replace(" ", "-"))
            points = int(acct.get("balance", 0))
            cpp = _DEFAULT_CPP.get(program_code, Decimal("1.0"))

            if points > 0:
                balances.append(
                    PointBalance(
                        program_code=program_code,
                        points=points,
                        cpp_baseline=cpp,
                    )
                )

        logger.info("balances_fetched", user_id="redacted", count=len(balances))
        return balances


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
