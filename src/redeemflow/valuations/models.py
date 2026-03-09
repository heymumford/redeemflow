"""Valuations domain — value objects for CPP analysis and card comparison.

Beck: The simplest thing that could work.
Fowler: Value objects are immutable. They define equality by their fields.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from statistics import median


class ValuationSource(str, Enum):
    TPG = "tpg"
    OMAAT = "omaat"
    NERDWALLET = "nerdwallet"
    UPGRADED_POINTS = "upgraded_points"


@dataclass(frozen=True)
class AnnualValueResult:
    total_points: int
    points_value: Decimal
    net_value: Decimal


@dataclass(frozen=True)
class ProgramValuation:
    program_code: str
    program_name: str
    valuations: dict[ValuationSource, Decimal]
    cash_back_cpp: Decimal = Decimal("1.0")

    def __post_init__(self) -> None:
        if not self.valuations:
            raise ValueError("ProgramValuation requires at least one valuation source")

    @property
    def _sorted_cpps(self) -> list[Decimal]:
        return sorted(self.valuations.values())

    @property
    def min_cpp(self) -> Decimal:
        return self._sorted_cpps[0]

    @property
    def max_cpp(self) -> Decimal:
        return self._sorted_cpps[-1]

    @property
    def median_cpp(self) -> Decimal:
        values = self._sorted_cpps
        m = median(values)
        return Decimal(str(m))

    def dollar_value(self, points: int) -> Decimal:
        return (Decimal(points) * self.median_cpp / Decimal(100)).quantize(Decimal("0.01"))

    def dollar_value_range(self, points: int) -> tuple[Decimal, Decimal]:
        low = (Decimal(points) * self.min_cpp / Decimal(100)).quantize(Decimal("0.01"))
        high = (Decimal(points) * self.max_cpp / Decimal(100)).quantize(Decimal("0.01"))
        return low, high

    def cash_back_value(self, points: int) -> Decimal:
        return (Decimal(points) * self.cash_back_cpp / Decimal(100)).quantize(Decimal("0.01"))

    def opportunity_cost(self, points: int) -> Decimal:
        return self.dollar_value(points) - self.cash_back_value(points)


@dataclass(frozen=True)
class CreditCard:
    name: str
    issuer: str
    annual_fee: Decimal
    earn_rates: dict[str, Decimal]
    credits: dict[str, Decimal]
    currency: str

    @property
    def net_annual_fee(self) -> Decimal:
        return self.annual_fee - sum(self.credits.values())

    def points_earned(self, category: str, spend: Decimal) -> int:
        rate = self.earn_rates.get(category, self.earn_rates.get("other", Decimal("1.0")))
        return int(spend * rate)

    def annual_value(self, spend_by_category: dict[str, Decimal], cpp: Decimal) -> AnnualValueResult:
        total_points = 0
        for category, amount in spend_by_category.items():
            total_points += self.points_earned(category, amount)

        points_value = (Decimal(total_points) * cpp / Decimal(100)).quantize(Decimal("0.01"))
        net_value = points_value - self.net_annual_fee
        return AnnualValueResult(total_points=total_points, points_value=points_value, net_value=net_value)
