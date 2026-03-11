"""Charity domain — ports (Protocol interfaces).

DonationPort defines the contract for processing point-based charitable donations.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Protocol, runtime_checkable


@runtime_checkable
class DonationPort(Protocol):
    """Port for processing charitable point donations."""

    def process_donation(self, user_id: str, charity_name: str, dollar_amount: Decimal) -> dict: ...

    def get_donation_status(self, reference_id: str) -> str: ...
