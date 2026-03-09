"""Portfolio domain — loyalty program value objects."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, eq=False)
class LoyaltyProgram:
    code: str
    name: str

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LoyaltyProgram):
            return NotImplemented
        return self.code == other.code

    def __hash__(self) -> int:
        return hash(self.code)


@dataclass(frozen=True)
class PointBalance:
    program_code: str
    points: int
    cpp_baseline: Decimal

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
