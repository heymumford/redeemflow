"""Optimization domain — value objects for the transfer graph engine."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class ActionType(str, Enum):
    TRANSFER = "transfer"
    BURN = "burn"
    HOLD = "hold"
    DONATE = "donate"


@dataclass(frozen=True)
class TransferPartner:
    """A directed edge in the loyalty program transfer graph."""

    source_program: str
    target_program: str
    transfer_ratio: float
    transfer_bonus: float = 0.0
    min_transfer: int = 1000
    is_instant: bool = True

    def __post_init__(self) -> None:
        if self.transfer_ratio <= 0:
            raise ValueError(f"transfer_ratio must be > 0, got {self.transfer_ratio}")
        if self.source_program == self.target_program:
            raise ValueError(f"source_program and target_program must differ, got '{self.source_program}'")

    @property
    def effective_ratio(self) -> float:
        """Ratio including any active bonus (e.g., 1.0 * (1 + 0.25) = 1.25)."""
        return self.transfer_ratio * (1.0 + self.transfer_bonus)


@dataclass(frozen=True)
class RedemptionOption:
    """A high-value redemption available within a loyalty program."""

    program: str
    description: str
    points_required: int
    cash_value: float
    availability: str = "medium"

    @property
    def cpp(self) -> float:
        """Cents per point: cash_value / points_required * 100."""
        if self.points_required <= 0:
            return 0.0
        return self.cash_value / self.points_required * 100


@dataclass(frozen=True)
class TransferPath:
    """A complete path from source program through transfers to a redemption."""

    steps: tuple[TransferPartner, ...]
    redemption: RedemptionOption
    source_points_needed: int
    effective_cpp: float
    total_hops: int


@dataclass(frozen=True)
class OptimizationAction:
    """A recommended action for a user's loyalty points."""

    action_type: ActionType
    program_code: str
    points: int
    expected_value: Decimal
    description: str
    target_program: str | None = None

    def __post_init__(self) -> None:
        if self.expected_value <= 0:
            raise ValueError(f"expected_value must be > 0, got {self.expected_value}")
