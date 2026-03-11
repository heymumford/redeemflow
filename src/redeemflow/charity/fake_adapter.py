"""Charity domain — fake adapter for testing.

In-memory DonationPort implementation with deterministic behavior.
Zero network calls. Tracks donations for verification.
"""

from __future__ import annotations

import uuid
from decimal import Decimal


class FakeDonationAdapter:
    """In-memory donation adapter for testing."""

    def __init__(self, simulate_error: str | None = None) -> None:
        self._simulate_error = simulate_error
        self._donations: dict[str, dict] = {}

    def process_donation(self, user_id: str, charity_name: str, dollar_amount: Decimal) -> dict:
        if self._simulate_error == "api_error":
            raise RuntimeError("Donation API error: service unavailable")

        reference_id = f"fake-don-{uuid.uuid4().hex[:12]}"
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

    @property
    def donation_count(self) -> int:
        """Number of donations processed (test inspection)."""
        return len(self._donations)
