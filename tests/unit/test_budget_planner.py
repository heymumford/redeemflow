"""Tests for annual points budget planner."""

from __future__ import annotations

from redeemflow.optimization.budget_planner import (
    AllocationTarget,
    BudgetSummary,
    EarningSource,
    compute_budget,
)


class TestComputeBudget:
    def test_basic_budget(self):
        sources = [EarningSource("CSR dining", "chase-ur", 5000, "card_spend")]
        targets = [AllocationTarget("SFO-NRT J", "chase-ur", 50000)]
        result = compute_budget(sources, targets)
        assert isinstance(result, BudgetSummary)
        assert result.total_annual_earnings == 60000
        assert result.total_allocation_needed == 50000
        assert result.surplus_or_deficit == 10000

    def test_multiple_sources_same_program(self):
        sources = [
            EarningSource("CSR dining", "chase-ur", 5000, "card_spend"),
            EarningSource("CSR travel", "chase-ur", 3000, "card_spend"),
        ]
        targets = []
        result = compute_budget(sources, targets)
        assert result.total_annual_earnings == 96000

    def test_forecast_12_months(self):
        sources = [EarningSource("Card", "united", 10000, "card_spend")]
        result = compute_budget(sources, [])
        assert len(result.forecasts_by_program["united"]) == 12
        assert result.forecasts_by_program["united"][11].cumulative == 120000

    def test_forecast_with_existing_balance(self):
        sources = [EarningSource("Card", "united", 5000, "card_spend")]
        result = compute_budget(sources, [], current_balances={"united": 20000})
        # Month 1: 20000 + 5000 = 25000
        assert result.forecasts_by_program["united"][0].cumulative == 25000

    def test_feasibility_achievable(self):
        sources = [EarningSource("Card", "united", 10000, "card_spend")]
        targets = [AllocationTarget("Trip", "united", 50000)]
        result = compute_budget(sources, targets, current_balances={"united": 20000})
        f = result.allocation_feasibility[0]
        assert f["feasible_this_year"] is True
        assert f["months_to_reach"] == 3  # Need 30K more, earn 10K/month

    def test_feasibility_not_achievable(self):
        sources = [EarningSource("Card", "united", 1000, "card_spend")]
        targets = [AllocationTarget("Trip", "united", 100000)]
        result = compute_budget(sources, targets)
        f = result.allocation_feasibility[0]
        assert f["feasible_this_year"] is False

    def test_no_earning_source(self):
        targets = [AllocationTarget("Trip", "united", 50000)]
        result = compute_budget([], targets)
        assert result.total_annual_earnings == 0
        f = result.allocation_feasibility[0]
        assert f["feasible_this_year"] is False

    def test_priority_ordering(self):
        sources = [EarningSource("Card", "chase-ur", 5000, "card_spend")]
        targets = [
            AllocationTarget("Trip B", "chase-ur", 30000, priority=2),
            AllocationTarget("Trip A", "chase-ur", 20000, priority=1),
        ]
        result = compute_budget(sources, targets)
        assert result.allocation_feasibility[0]["name"] == "Trip A"

    def test_multiple_programs(self):
        sources = [
            EarningSource("CSR", "chase-ur", 5000, "card_spend"),
            EarningSource("MPE", "united", 3000, "card_spend"),
        ]
        result = compute_budget(sources, [])
        assert "chase-ur" in result.forecasts_by_program
        assert "united" in result.forecasts_by_program
        assert result.total_annual_earnings == 96000

    def test_deficit(self):
        sources = [EarningSource("Card", "united", 1000, "card_spend")]
        targets = [AllocationTarget("Trip", "united", 50000)]
        result = compute_budget(sources, targets)
        assert result.surplus_or_deficit < 0

    def test_empty_everything(self):
        result = compute_budget([], [])
        assert result.total_annual_earnings == 0
        assert result.total_allocation_needed == 0
        assert result.surplus_or_deficit == 0
