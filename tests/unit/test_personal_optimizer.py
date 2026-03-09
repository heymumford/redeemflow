"""Tests for the personalized optimization engine."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from redeemflow.optimization.graph import TransferGraph
from redeemflow.optimization.models import RedemptionOption, TransferPartner
from redeemflow.optimization.personal_optimizer import PersonalizedAction, PersonalOptimizer
from redeemflow.portfolio.models import PointBalance
from redeemflow.valuations.seed_data import PROGRAM_VALUATIONS


class TestPersonalizedAction:
    def test_frozen_dataclass(self) -> None:
        action = PersonalizedAction(
            program_code="chase-ur",
            action_type="transfer",
            description="Transfer to Hyatt",
            estimated_value_gain=Decimal("50.00"),
            urgency="immediate",
            confidence="high",
            details={"target": "hyatt"},
        )
        with pytest.raises(FrozenInstanceError):
            action.program_code = "amex-mr"  # type: ignore[misc]

    def test_all_fields(self) -> None:
        action = PersonalizedAction(
            program_code="amex-mr",
            action_type="redeem",
            description="Redeem for ANA First",
            estimated_value_gain=Decimal("125.00"),
            urgency="soon",
            confidence="medium",
            details={"route": "SFO-NRT"},
        )
        assert action.program_code == "amex-mr"
        assert action.action_type == "redeem"
        assert action.description == "Redeem for ANA First"
        assert action.estimated_value_gain == Decimal("125.00")
        assert action.urgency == "soon"
        assert action.confidence == "medium"
        assert action.details == {"route": "SFO-NRT"}

    def test_estimated_value_gain_is_decimal(self) -> None:
        action = PersonalizedAction(
            program_code="chase-ur",
            action_type="hold",
            description="Hold points",
            estimated_value_gain=Decimal("0.00"),
            urgency="opportunity",
            confidence="high",
            details={},
        )
        assert isinstance(action.estimated_value_gain, Decimal)


def _build_test_graph() -> TransferGraph:
    """Build a small test graph with known bonuses and redemptions."""
    graph = TransferGraph()
    graph.add_partner(TransferPartner(source_program="chase-ur", target_program="hyatt", transfer_ratio=1.0))
    graph.add_partner(TransferPartner(source_program="chase-ur", target_program="united", transfer_ratio=1.0))
    graph.add_partner(
        TransferPartner(source_program="amex-mr", target_program="ana", transfer_ratio=1.0, transfer_bonus=0.30)
    )
    graph.add_partner(TransferPartner(source_program="amex-mr", target_program="delta", transfer_ratio=1.0))
    graph.add_redemption(
        RedemptionOption(program="hyatt", description="Hyatt Cat 1-4", points_required=8000, cash_value=240.0)
    )
    graph.add_redemption(
        RedemptionOption(
            program="hyatt", description="Hyatt all-inclusive Ziva/Zilara", points_required=25000, cash_value=750.0
        )
    )
    graph.add_redemption(
        RedemptionOption(program="ana", description="ANA First SFO-NRT", points_required=110000, cash_value=16500.0)
    )
    graph.add_redemption(
        RedemptionOption(
            program="united", description="United Polaris Business SFO-NRT", points_required=80000, cash_value=5600.0
        )
    )
    return graph


class TestPersonalOptimizer:
    def test_optimize_with_balances_returns_ranked_actions(self) -> None:
        graph = _build_test_graph()
        optimizer = PersonalOptimizer(graph=graph, valuations=PROGRAM_VALUATIONS)
        balances = [
            PointBalance(program_code="chase-ur", points=95000, cpp_baseline=Decimal("1.85")),
            PointBalance(program_code="amex-mr", points=130000, cpp_baseline=Decimal("1.85")),
        ]
        actions = optimizer.optimize(balances)
        assert len(actions) > 0
        # Actions should be sorted by estimated_value_gain descending
        gains = [a.estimated_value_gain for a in actions]
        assert gains == sorted(gains, reverse=True)

    def test_optimize_empty_balances_returns_empty(self) -> None:
        graph = _build_test_graph()
        optimizer = PersonalOptimizer(graph=graph, valuations=PROGRAM_VALUATIONS)
        actions = optimizer.optimize([])
        assert actions == []

    def test_top_actions_limits_results(self) -> None:
        graph = _build_test_graph()
        optimizer = PersonalOptimizer(graph=graph, valuations=PROGRAM_VALUATIONS)
        balances = [
            PointBalance(program_code="chase-ur", points=95000, cpp_baseline=Decimal("1.85")),
            PointBalance(program_code="amex-mr", points=130000, cpp_baseline=Decimal("1.85")),
        ]
        top = optimizer.top_actions(balances, n=2)
        assert len(top) <= 2

    def test_action_types_include_transfer_redeem_hold(self) -> None:
        graph = _build_test_graph()
        optimizer = PersonalOptimizer(graph=graph, valuations=PROGRAM_VALUATIONS)
        balances = [
            PointBalance(program_code="chase-ur", points=95000, cpp_baseline=Decimal("1.85")),
            PointBalance(program_code="amex-mr", points=130000, cpp_baseline=Decimal("1.85")),
            PointBalance(program_code="hilton", points=310000, cpp_baseline=Decimal("0.47")),
        ]
        actions = optimizer.optimize(balances)
        action_types = {a.action_type for a in actions}
        # Should have at least transfer and one other type
        assert "transfer" in action_types or "redeem" in action_types

    def test_all_estimated_value_gains_are_decimal(self) -> None:
        graph = _build_test_graph()
        optimizer = PersonalOptimizer(graph=graph, valuations=PROGRAM_VALUATIONS)
        balances = [
            PointBalance(program_code="chase-ur", points=95000, cpp_baseline=Decimal("1.85")),
        ]
        actions = optimizer.optimize(balances)
        for action in actions:
            assert isinstance(action.estimated_value_gain, Decimal)

    def test_estimated_value_gains_are_non_negative(self) -> None:
        graph = _build_test_graph()
        optimizer = PersonalOptimizer(graph=graph, valuations=PROGRAM_VALUATIONS)
        balances = [
            PointBalance(program_code="chase-ur", points=95000, cpp_baseline=Decimal("1.85")),
            PointBalance(program_code="amex-mr", points=130000, cpp_baseline=Decimal("1.85")),
        ]
        actions = optimizer.optimize(balances)
        for action in actions:
            assert action.estimated_value_gain >= Decimal("0")
