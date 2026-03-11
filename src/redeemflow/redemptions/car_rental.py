"""Car rental redemption analysis — value assessment for point-based car rentals.

Fowler: Separate the policy from the mechanism.
Beck: Make the implicit explicit — car rental CPP is often poor but sometimes valuable.

Most car rental redemptions deliver 0.5-1.0 CPP, well below airline/hotel sweet spots.
This module helps users understand when car rental redemptions make sense.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class CarRentalProvider(str, Enum):
    HERTZ = "hertz"
    NATIONAL = "national"
    AVIS = "avis"


class RentalClass(str, Enum):
    ECONOMY = "economy"
    MIDSIZE = "midsize"
    FULL_SIZE = "full_size"
    SUV = "suv"
    PREMIUM = "premium"


@dataclass(frozen=True)
class CarRentalRedemption:
    """A car rental redemption option via loyalty points."""

    provider: CarRentalProvider
    rental_class: RentalClass
    program_code: str
    points_per_day: int
    cash_equivalent_per_day: Decimal
    min_days: int = 1
    max_days: int = 14

    @property
    def cpp(self) -> Decimal:
        """Cents per point for this car rental redemption."""
        if self.points_per_day <= 0:
            return Decimal("0")
        return (self.cash_equivalent_per_day / self.points_per_day * 100).quantize(Decimal("0.01"))


@dataclass(frozen=True)
class CarRentalAnalysis:
    """Analysis of car rental redemption value vs alternative uses."""

    redemption: CarRentalRedemption
    days: int
    total_points: int
    total_cash_value: Decimal
    effective_cpp: Decimal
    alternative_cpp: Decimal  # What those points are worth in best airline/hotel use
    value_ratio: Decimal  # car_cpp / alternative_cpp
    recommendation: str  # "redeem_car", "use_elsewhere", "acceptable"
    rationale: str


# Seed data: real-world car rental redemption rates
CAR_RENTAL_REDEMPTIONS: list[CarRentalRedemption] = [
    # Chase UR via portal (typically ~1.25-1.5 CPP)
    CarRentalRedemption(
        provider=CarRentalProvider.HERTZ,
        rental_class=RentalClass.ECONOMY,
        program_code="chase-ur",
        points_per_day=8000,
        cash_equivalent_per_day=Decimal("45.00"),
    ),
    CarRentalRedemption(
        provider=CarRentalProvider.HERTZ,
        rental_class=RentalClass.MIDSIZE,
        program_code="chase-ur",
        points_per_day=10000,
        cash_equivalent_per_day=Decimal("60.00"),
    ),
    CarRentalRedemption(
        provider=CarRentalProvider.NATIONAL,
        rental_class=RentalClass.FULL_SIZE,
        program_code="chase-ur",
        points_per_day=12000,
        cash_equivalent_per_day=Decimal("75.00"),
    ),
    # Capital One via portal
    CarRentalRedemption(
        provider=CarRentalProvider.HERTZ,
        rental_class=RentalClass.ECONOMY,
        program_code="capital-one",
        points_per_day=9000,
        cash_equivalent_per_day=Decimal("45.00"),
    ),
    CarRentalRedemption(
        provider=CarRentalProvider.AVIS,
        rental_class=RentalClass.SUV,
        program_code="capital-one",
        points_per_day=20000,
        cash_equivalent_per_day=Decimal("110.00"),
    ),
    # Amex MR via portal
    CarRentalRedemption(
        provider=CarRentalProvider.HERTZ,
        rental_class=RentalClass.MIDSIZE,
        program_code="amex-mr",
        points_per_day=11000,
        cash_equivalent_per_day=Decimal("55.00"),
    ),
    CarRentalRedemption(
        provider=CarRentalProvider.NATIONAL,
        rental_class=RentalClass.PREMIUM,
        program_code="amex-mr",
        points_per_day=25000,
        cash_equivalent_per_day=Decimal("150.00"),
    ),
]


def analyze_car_rental(
    redemption: CarRentalRedemption,
    days: int,
    alternative_cpp: Decimal = Decimal("1.5"),
) -> CarRentalAnalysis:
    """Analyze whether a car rental redemption is worthwhile.

    Compares the car rental CPP against the best alternative use of those points.
    """
    total_points = redemption.points_per_day * days
    total_cash = redemption.cash_equivalent_per_day * days
    car_cpp = redemption.cpp

    value_ratio = (car_cpp / alternative_cpp).quantize(Decimal("0.01")) if alternative_cpp > 0 else Decimal("0")

    if value_ratio >= Decimal("0.9"):
        recommendation = "redeem_car"
        rationale = f"Car rental at {car_cpp} CPP is close to or better than alternatives at {alternative_cpp} CPP"
    elif value_ratio >= Decimal("0.6"):
        recommendation = "acceptable"
        rationale = (
            f"Car rental at {car_cpp} CPP is acceptable if you need a car, "
            f"but alternatives yield {alternative_cpp} CPP"
        )
    else:
        recommendation = "use_elsewhere"
        rationale = (
            f"Car rental at {car_cpp} CPP is poor value — "
            f"consider using points for flights/hotels at {alternative_cpp} CPP instead"
        )

    return CarRentalAnalysis(
        redemption=redemption,
        days=days,
        total_points=total_points,
        total_cash_value=total_cash,
        effective_cpp=car_cpp,
        alternative_cpp=alternative_cpp,
        value_ratio=value_ratio,
        recommendation=recommendation,
        rationale=rationale,
    )


def find_car_rentals(program_code: str) -> list[CarRentalRedemption]:
    """Find all car rental redemptions for a given loyalty program."""
    return [r for r in CAR_RENTAL_REDEMPTIONS if r.program_code == program_code]


def best_car_rental(program_code: str) -> CarRentalRedemption | None:
    """Find the best CPP car rental redemption for a program."""
    rentals = find_car_rentals(program_code)
    if not rentals:
        return None
    return max(rentals, key=lambda r: r.cpp)
