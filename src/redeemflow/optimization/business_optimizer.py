"""Business travel optimizer — category-based card stacking for maximum value.

Beck: The simplest thing that could work.
Fowler: Frozen dataclasses for results, strategy pattern for card selection.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from redeemflow.valuations.models import CreditCard, ProgramValuation


@dataclass(frozen=True)
class CardAssignment:
    card_name: str
    card_id: str
    category: str
    earn_rate: Decimal
    monthly_points: int
    annual_points: int
    annual_value: Decimal


@dataclass(frozen=True)
class BusinessOptimization:
    assignments: list[CardAssignment]
    total_annual_points: int
    total_annual_value: Decimal
    missed_value_generic_card: Decimal


class BusinessOptimizer:
    """Finds optimal card assignments per expense category to maximize total annual value."""

    def __init__(self, cards: dict[str, CreditCard], valuations: dict[str, ProgramValuation]) -> None:
        self._cards = cards
        self._valuations = valuations

    def optimize(self, expense_categories: dict[str, Decimal]) -> BusinessOptimization:
        if not expense_categories:
            return BusinessOptimization(
                assignments=[],
                total_annual_points=0,
                total_annual_value=Decimal("0"),
                missed_value_generic_card=Decimal("0"),
            )

        assignments: list[CardAssignment] = []
        total_annual_points = 0
        total_annual_value = Decimal("0")
        generic_annual_value = Decimal("0")

        for category, monthly_spend in expense_categories.items():
            best_assignment = self._best_card_for_category(category, monthly_spend)
            if best_assignment is not None:
                assignments.append(best_assignment)
                total_annual_points += best_assignment.annual_points
                total_annual_value += best_assignment.annual_value

            # Generic 1x card baseline for comparison
            generic_monthly_points = int(monthly_spend * Decimal("1"))
            generic_annual_pts = generic_monthly_points * 12
            # Use median of ~1.5 CPP as a generous generic baseline
            generic_value = (Decimal(generic_annual_pts) * Decimal("1.0") / Decimal("100")).quantize(Decimal("0.01"))
            generic_annual_value += generic_value

        missed_value = (total_annual_value - generic_annual_value).quantize(Decimal("0.01"))

        return BusinessOptimization(
            assignments=assignments,
            total_annual_points=total_annual_points,
            total_annual_value=total_annual_value,
            missed_value_generic_card=missed_value if missed_value > Decimal("0") else Decimal("0"),
        )

    def _best_card_for_category(self, category: str, monthly_spend: Decimal) -> CardAssignment | None:
        best: CardAssignment | None = None
        best_value = Decimal("-1")

        for card_id, card in self._cards.items():
            earn_rate = card.earn_rates.get(category, card.earn_rates.get("other", Decimal("1.0")))
            monthly_points = int(monthly_spend * earn_rate)
            annual_points = monthly_points * 12

            valuation = self._valuations.get(card.currency)
            if valuation is None:
                continue

            cpp = valuation.median_cpp
            annual_value = (Decimal(annual_points) * cpp / Decimal("100")).quantize(Decimal("0.01"))

            if annual_value > best_value:
                best_value = annual_value
                best = CardAssignment(
                    card_name=card.name,
                    card_id=card_id,
                    category=category,
                    earn_rate=earn_rate,
                    monthly_points=monthly_points,
                    annual_points=annual_points,
                    annual_value=annual_value,
                )

        return best
