"""Portfolio domain — loyalty program value objects.

Frozen dataclasses for all value objects. Decimal for all financial math.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum


class ProgramCategory(str, Enum):
    HOTEL = "hotel"
    AIRLINE = "airline"
    CAR_RENTAL = "car_rental"
    CREDIT_CARD = "credit_card"
    RETAIL = "retail"


@dataclass(frozen=True, eq=False)
class LoyaltyProgram:
    code: str
    name: str
    category: ProgramCategory = ProgramCategory.CREDIT_CARD
    cpp_min: float = 0.1
    cpp_max: float = 10.0

    def __post_init__(self) -> None:
        if not self.code:
            raise ValueError("code must not be empty")
        if not self.name:
            raise ValueError("name must not be empty")
        if self.cpp_min < 0.1:
            raise ValueError(f"cpp_min must be >= 0.1, got {self.cpp_min}")
        if self.cpp_max > 10.0:
            raise ValueError(f"cpp_max must be <= 10.0, got {self.cpp_max}")
        if self.cpp_min > self.cpp_max:
            raise ValueError(f"cpp_min ({self.cpp_min}) must be <= cpp_max ({self.cpp_max})")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LoyaltyProgram):
            return NotImplemented
        return self.code == other.code

    def __hash__(self) -> int:
        return hash(self.code)


@dataclass(frozen=True)
class PointBalance:
    """A user's point balance in a specific loyalty program."""

    program_code: str
    points: int
    cpp_baseline: Decimal

    def __post_init__(self) -> None:
        if self.points < 0:
            raise ValueError(f"points must be >= 0, got {self.points}")

    @property
    def estimated_value_cents(self) -> int:
        return int(self.points * self.cpp_baseline)

    @property
    def estimated_value_dollars(self) -> Decimal:
        return Decimal(self.estimated_value_cents) / Decimal(100)


@dataclass(frozen=True)
class LoyaltyAccount:
    user_id: str
    program_code: str
    member_id: str


@dataclass(frozen=True)
class UserPortfolio:
    """Aggregate of N program balances for a single user."""

    user_id: str
    balances: tuple[PointBalance, ...] = field(default_factory=tuple)

    @property
    def total_estimated_value_cents(self) -> int:
        return sum(b.estimated_value_cents for b in self.balances)

    @property
    def total_estimated_value_dollars(self) -> Decimal:
        return Decimal(self.total_estimated_value_cents) / Decimal(100)

    @property
    def program_codes(self) -> frozenset[str]:
        return frozenset(b.program_code for b in self.balances)

    def balance_for(self, program_code: str) -> PointBalance | None:
        for b in self.balances:
            if b.program_code == program_code:
                return b
        return None
