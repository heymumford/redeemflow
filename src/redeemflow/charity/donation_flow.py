"""Donation pipeline — Change API integration for point-based charitable giving.

Beck: The simplest thing that could work.
Fowler: Protocol for provider interface, frozen dataclasses for value objects.

IRS Disclosure: Loyalty point donations are NOT tax-deductible. The IRS treats
loyalty points as rebates, not income. When points are converted to a dollar
value and donated, the donor has no cost basis — the donation is a conversion
of a rebate, not a charitable contribution eligible for a tax deduction.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from typing import Protocol, runtime_checkable

import httpx

from redeemflow.charity.models import CharityPartnerNetwork
from redeemflow.middleware.logging import get_logger
from redeemflow.valuations.models import ProgramValuation

logger = get_logger("donations")


class DonationStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


@dataclass(frozen=True)
class Donation:
    id: str
    user_id: str
    charity_name: str
    charity_state: str
    program_code: str
    points_donated: int
    dollar_value: Decimal
    status: DonationStatus
    created_at: str
    completed_at: str | None = None
    change_api_reference: str | None = None
    cpp_at_donation: Decimal | None = None

    def __post_init__(self) -> None:
        if self.points_donated <= 0:
            raise ValueError(f"points_donated must be > 0, got {self.points_donated}")
        if self.dollar_value <= 0:
            raise ValueError(f"dollar_value must be > 0, got {self.dollar_value}")


@runtime_checkable
class DonationProvider(Protocol):
    def process_donation(self, user_id: str, charity_name: str, dollar_amount: Decimal) -> dict: ...
    def get_donation_status(self, reference_id: str) -> str: ...


class ChangeApiError(Exception):
    """Raised when Change API interaction fails."""


class ChangeApiAdapter:
    """Real Change API adapter — calls Change.org/getchange.io donation API.

    Change API docs: https://docs.getchange.io
    Authentication: API key as Bearer token.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.getchange.io/api/v1",
        timeout: float = 30.0,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url
        self._timeout = timeout

    def process_donation(self, user_id: str, charity_name: str, dollar_amount: Decimal) -> dict:
        """Submit a donation through the Change API."""
        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.post(
                    f"{self._base_url}/donations",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    json={
                        "amount": int((dollar_amount * 100).quantize(Decimal("1"))),  # cents
                        "nonprofit_id": charity_name,
                        "funds_collected": True,
                        "metadata": {"user_id": user_id, "source": "redeemflow"},
                    },
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.TimeoutException as e:
            raise ChangeApiError(f"Change API timeout: {e}") from e
        except httpx.HTTPStatusError as e:
            raise ChangeApiError(f"Change API error: {e.response.status_code}") from e
        except httpx.HTTPError as e:
            raise ChangeApiError(f"Change API connection error: {e}") from e

        reference_id = data.get("id")
        if not reference_id:
            raise ChangeApiError("Change API response missing donation ID")
        status = data.get("status", "pending")

        logger.info(
            "donation_processed",
            reference_id=reference_id,
            charity=charity_name,
            amount_cents=int((dollar_amount * 100).quantize(Decimal("1"))),
        )
        return {"reference_id": reference_id, "status": status}

    def get_donation_status(self, reference_id: str) -> str:
        """Check status of a previously submitted donation."""
        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.get(
                    f"{self._base_url}/donations/{reference_id}",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError:
            return "unknown"

        return data.get("status", "unknown")


class FakeDonationProvider:
    """In-memory donation provider for tests and development."""

    def __init__(self) -> None:
        self._donations: dict[str, dict] = {}

    def process_donation(self, user_id: str, charity_name: str, dollar_amount: Decimal) -> dict:
        reference_id = f"fake-ref-{uuid.uuid4().hex[:12]}"
        self._donations[reference_id] = {
            "user_id": user_id,
            "charity_name": charity_name,
            "dollar_amount": dollar_amount,
            "status": "completed",
        }
        return {"reference_id": reference_id, "status": "completed"}

    def get_donation_status(self, reference_id: str) -> str:
        record = self._donations.get(reference_id)
        if record is None:
            return "unknown"
        return record["status"]


class DonationService:
    """Orchestrates point-to-dollar conversion and donation processing."""

    def __init__(
        self,
        provider: DonationProvider,
        valuations: dict[str, ProgramValuation],
        charity_network: CharityPartnerNetwork,
        repository: object | None = None,
    ) -> None:
        self._provider = provider
        self._valuations = valuations
        self._charity_network = charity_network
        self._repository = repository
        self._donations: list[Donation] = []

    def donate(
        self,
        user_id: str,
        charity_name: str,
        charity_state: str,
        program_code: str,
        points: int,
    ) -> Donation:
        if points <= 0:
            raise ValueError("points must be greater than zero")

        valuation = self._valuations.get(program_code)
        if valuation is None:
            raise ValueError(f"Unknown program: {program_code}")

        # Validate charity exists in network
        matches = [c for c in self._charity_network.charities if c.name == charity_name and c.state == charity_state]
        if not matches:
            raise ValueError(f"Unknown charity: {charity_name} in {charity_state}")

        dollar_value = valuation.dollar_value(points)
        now = datetime.now(UTC).isoformat()

        try:
            result = self._provider.process_donation(user_id, charity_name, dollar_value)
        except Exception as e:
            # Provider failed — record as FAILED, not COMPLETED
            failed_donation = Donation(
                id=f"don-{uuid.uuid4().hex[:12]}",
                user_id=user_id,
                charity_name=charity_name,
                charity_state=charity_state,
                program_code=program_code,
                points_donated=points,
                dollar_value=dollar_value,
                status=DonationStatus.FAILED,
                created_at=now,
                cpp_at_donation=valuation.median_cpp,
            )
            self._donations.append(failed_donation)
            logger.error("donation_failed", user_id=user_id, charity=charity_name, error=str(e))
            raise

        # Map provider status to our status
        provider_status = result.get("status", "unknown")
        if provider_status == "completed":
            status = DonationStatus.COMPLETED
            completed_at = now
        elif provider_status in ("pending", "processing"):
            status = DonationStatus.PROCESSING
            completed_at = None
        else:
            status = DonationStatus.PENDING
            completed_at = None

        donation = Donation(
            id=f"don-{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            charity_name=charity_name,
            charity_state=charity_state,
            program_code=program_code,
            points_donated=points,
            dollar_value=dollar_value,
            status=status,
            created_at=now,
            completed_at=completed_at,
            change_api_reference=result.get("reference_id"),
            cpp_at_donation=valuation.median_cpp,
        )
        if self._repository:
            self._repository.save(donation)
        self._donations.append(donation)
        return donation

    def get_user_donations(self, user_id: str) -> list[Donation]:
        if self._repository:
            return self._repository.get_by_user(user_id)
        return [d for d in self._donations if d.user_id == user_id]

    def get_all_donations(self) -> list[Donation]:
        if self._repository:
            return self._repository.get_all()
        return list(self._donations)
