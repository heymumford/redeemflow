"""Optimization domain — ports (Protocol interfaces).

TransferGraphPort defines the contract for querying transfer paths and ratios
between loyalty programs.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from redeemflow.optimization.models import TransferPartner, TransferPath


@runtime_checkable
class TransferGraphPort(Protocol):
    """Port for querying the loyalty program transfer graph."""

    def find_paths(self, source: str, target: str) -> list[TransferPath]: ...

    def get_ratio(self, source: str, target: str) -> float | None: ...

    def get_partners_from(self, source: str) -> list[TransferPartner]: ...
