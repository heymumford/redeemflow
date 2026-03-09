"""Tests for the bank vs burn timing advisor."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from redeemflow.optimization.graph import TransferGraph
from redeemflow.optimization.models import RedemptionOption, TransferPartner
from redeemflow.optimization.timing_advisor import TimingAdvice, TimingAdvisor
from redeemflow.portfolio.models import PointBalance
from redeemflow.valuations.seed_data import PROGRAM_VALUATIONS


class TestTimingAdvice:
    def test_frozen_dataclass(self) -> None:
        advice = TimingAdvice(
            program_code="chase-ur",
            recommendation="bank",
            rationale="No active bonuses, CPP strong",
            confidence="high",
            cpp_trend="stable",
            active_bonuses=[],
        )
        with pytest.raises(FrozenInstanceError):
            advice.recommendation = "burn"  # type: ignore[misc]

    def test_all_fields(self) -> None:
        advice = TimingAdvice(
            program_code="amex-mr",
            recommendation="transfer",
            rationale="30% bonus to ANA active",
            confidence="high",
            cpp_trend="stable",
            active_bonuses=["ANA 30% bonus"],
        )
        assert advice.program_code == "amex-mr"
        assert advice.recommendation == "transfer"
        assert advice.rationale == "30% bonus to ANA active"
        assert advice.confidence == "high"
        assert advice.cpp_trend == "stable"
        assert advice.active_bonuses == ["ANA 30% bonus"]


def _build_bonus_graph() -> TransferGraph:
    graph = TransferGraph()
    graph.add_partner(
        TransferPartner(source_program="amex-mr", target_program="ana", transfer_ratio=1.0, transfer_bonus=0.30)
    )
    graph.add_partner(TransferPartner(source_program="chase-ur", target_program="hyatt", transfer_ratio=1.0))
    graph.add_partner(TransferPartner(source_program="chase-ur", target_program="united", transfer_ratio=1.0))
    graph.add_redemption(
        RedemptionOption(program="hyatt", description="Hyatt Cat 1-4", points_required=8000, cash_value=240.0)
    )
    graph.add_redemption(
        RedemptionOption(program="ana", description="ANA First SFO-NRT", points_required=110000, cash_value=16500.0)
    )
    return graph


class TestTimingAdvisor:
    def test_program_with_active_bonus_recommends_transfer(self) -> None:
        graph = _build_bonus_graph()
        advisor = TimingAdvisor(graph=graph, valuations=PROGRAM_VALUATIONS)
        advice = advisor.advise("amex-mr", 130000)
        assert advice.recommendation == "transfer"
        assert len(advice.active_bonuses) > 0
        assert advice.confidence in ("high", "medium", "low")

    def test_stable_program_recommends_bank(self) -> None:
        graph = _build_bonus_graph()
        advisor = TimingAdvisor(graph=graph, valuations=PROGRAM_VALUATIONS)
        advice = advisor.advise("chase-ur", 95000)
        # Chase UR has no bonus in this graph, so should recommend bank
        assert advice.recommendation == "bank"
        assert advice.cpp_trend in ("rising", "stable", "declining")

    def test_advise_portfolio_returns_advice_for_each_balance(self) -> None:
        graph = _build_bonus_graph()
        advisor = TimingAdvisor(graph=graph, valuations=PROGRAM_VALUATIONS)
        balances = [
            PointBalance(program_code="chase-ur", points=95000, cpp_baseline=Decimal("1.85")),
            PointBalance(program_code="amex-mr", points=130000, cpp_baseline=Decimal("1.85")),
        ]
        advice_list = advisor.advise_portfolio(balances)
        assert len(advice_list) == 2
        codes = {a.program_code for a in advice_list}
        assert codes == {"chase-ur", "amex-mr"}

    def test_confidence_field_is_valid(self) -> None:
        graph = _build_bonus_graph()
        advisor = TimingAdvisor(graph=graph, valuations=PROGRAM_VALUATIONS)
        advice = advisor.advise("chase-ur", 50000)
        assert advice.confidence in ("high", "medium", "low")

    def test_cpp_trend_field_is_valid(self) -> None:
        graph = _build_bonus_graph()
        advisor = TimingAdvisor(graph=graph, valuations=PROGRAM_VALUATIONS)
        advice = advisor.advise("chase-ur", 50000)
        assert advice.cpp_trend in ("rising", "stable", "declining")

    def test_unknown_program_recommends_bank(self) -> None:
        graph = _build_bonus_graph()
        advisor = TimingAdvisor(graph=graph, valuations=PROGRAM_VALUATIONS)
        advice = advisor.advise("unknown-program", 10000)
        assert advice.recommendation == "bank"
        assert advice.confidence == "low"
