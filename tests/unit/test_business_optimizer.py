"""Business travel optimizer tests — TDD: written before implementation.

Tests the business optimizer domain: card assignments, optimization logic.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from redeemflow.optimization.business_optimizer import (
    BusinessOptimization,
    BusinessOptimizer,
    CardAssignment,
)
from redeemflow.valuations.seed_data import CREDIT_CARDS, PROGRAM_VALUATIONS


class TestCardAssignment:
    def test_frozen_dataclass(self):
        ca = CardAssignment(
            card_name="Amex Gold",
            card_id="amex-gold",
            category="dining",
            earn_rate=Decimal("4.0"),
            monthly_points=4000,
            annual_points=48000,
            annual_value=Decimal("816.00"),
        )
        with pytest.raises(AttributeError):
            ca.card_name = "Other"  # type: ignore[misc]

    def test_fields(self):
        ca = CardAssignment(
            card_name="Amex Gold",
            card_id="amex-gold",
            category="dining",
            earn_rate=Decimal("4.0"),
            monthly_points=4000,
            annual_points=48000,
            annual_value=Decimal("816.00"),
        )
        assert ca.card_name == "Amex Gold"
        assert ca.category == "dining"
        assert isinstance(ca.annual_value, Decimal)


class TestBusinessOptimization:
    def test_frozen_dataclass(self):
        opt = BusinessOptimization(
            assignments=[],
            total_annual_points=0,
            total_annual_value=Decimal("0"),
            missed_value_generic_card=Decimal("0"),
        )
        with pytest.raises(AttributeError):
            opt.total_annual_points = 1  # type: ignore[misc]

    def test_totals(self):
        a1 = CardAssignment(
            card_name="Amex Gold",
            card_id="amex-gold",
            category="dining",
            earn_rate=Decimal("4.0"),
            monthly_points=4000,
            annual_points=48000,
            annual_value=Decimal("816.00"),
        )
        a2 = CardAssignment(
            card_name="CSR",
            card_id="chase-sapphire-reserve",
            category="travel",
            earn_rate=Decimal("3.0"),
            monthly_points=3000,
            annual_points=36000,
            annual_value=Decimal("612.00"),
        )
        opt = BusinessOptimization(
            assignments=[a1, a2],
            total_annual_points=84000,
            total_annual_value=Decimal("1428.00"),
            missed_value_generic_card=Decimal("500.00"),
        )
        assert opt.total_annual_points == 84000
        assert opt.total_annual_value == Decimal("1428.00")
        assert opt.missed_value_generic_card == Decimal("500.00")


class TestBusinessOptimizer:
    def _make_optimizer(self) -> BusinessOptimizer:
        return BusinessOptimizer(cards=CREDIT_CARDS, valuations=PROGRAM_VALUATIONS)

    def test_optimize_with_known_categories(self):
        optimizer = self._make_optimizer()
        expenses = {
            "dining": Decimal("1000"),
            "travel": Decimal("2000"),
        }
        result = optimizer.optimize(expenses)
        assert isinstance(result, BusinessOptimization)
        assert len(result.assignments) == 2
        assert result.total_annual_points > 0
        assert result.total_annual_value > Decimal("0")

    def test_dining_uses_best_dining_card(self):
        optimizer = self._make_optimizer()
        expenses = {"dining": Decimal("1000")}
        result = optimizer.optimize(expenses)
        assert len(result.assignments) == 1
        dining_assignment = result.assignments[0]
        assert dining_assignment.category == "dining"
        # Amex Gold has 4x dining, which with amex-mr median CPP should beat others
        assert dining_assignment.earn_rate >= Decimal("3.0")

    def test_empty_categories_returns_empty(self):
        optimizer = self._make_optimizer()
        result = optimizer.optimize({})
        assert isinstance(result, BusinessOptimization)
        assert len(result.assignments) == 0
        assert result.total_annual_points == 0
        assert result.total_annual_value == Decimal("0")

    def test_missed_value_generic_card_positive(self):
        optimizer = self._make_optimizer()
        expenses = {
            "dining": Decimal("1000"),
            "travel": Decimal("2000"),
        }
        result = optimizer.optimize(expenses)
        # Optimized cards should earn more than a generic 1x card
        assert result.missed_value_generic_card > Decimal("0")

    def test_optimize_covers_all_expense_categories(self):
        optimizer = self._make_optimizer()
        expenses = {
            "dining": Decimal("500"),
            "travel": Decimal("1000"),
            "groceries": Decimal("800"),
        }
        result = optimizer.optimize(expenses)
        categories = {a.category for a in result.assignments}
        assert categories == {"dining", "travel", "groceries"}
