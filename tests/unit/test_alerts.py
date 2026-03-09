"""Tests for the alert system — models and engine."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from redeemflow.notifications.alerts import AlertEngine
from redeemflow.notifications.models import Alert, AlertPriority, AlertType
from redeemflow.optimization.graph import TransferGraph
from redeemflow.optimization.models import RedemptionOption, TransferPartner
from redeemflow.portfolio.expiration import ExpirationPolicy
from redeemflow.portfolio.models import PointBalance


class TestAlertType:
    def test_enum_values(self) -> None:
        assert AlertType.DEVALUATION == "devaluation"
        assert AlertType.TRANSFER_BONUS == "transfer_bonus"
        assert AlertType.EXPIRATION == "expiration"
        assert AlertType.SWEET_SPOT == "sweet_spot"
        assert AlertType.PRICE_DROP == "price_drop"


class TestAlertPriority:
    def test_enum_values(self) -> None:
        assert AlertPriority.CRITICAL == "critical"
        assert AlertPriority.HIGH == "high"
        assert AlertPriority.MEDIUM == "medium"
        assert AlertPriority.LOW == "low"


class TestAlert:
    def test_frozen_dataclass(self) -> None:
        alert = Alert(
            id="alert-1",
            alert_type=AlertType.TRANSFER_BONUS,
            priority=AlertPriority.HIGH,
            title="30% Amex MR to ANA bonus",
            message="Transfer bonus active now.",
            program_code="amex-mr",
            action_url=None,
            created_at="2026-03-09T00:00:00Z",
            expires_at="2026-04-09T00:00:00Z",
        )
        with pytest.raises(FrozenInstanceError):
            alert.title = "modified"  # type: ignore[misc]

    def test_all_fields(self) -> None:
        alert = Alert(
            id="alert-2",
            alert_type=AlertType.EXPIRATION,
            priority=AlertPriority.CRITICAL,
            title="Points expiring",
            message="Your United miles expire in 30 days.",
            program_code="united",
            action_url="/api/portfolio",
            created_at="2026-03-09T00:00:00Z",
            expires_at=None,
        )
        assert alert.id == "alert-2"
        assert alert.alert_type == AlertType.EXPIRATION
        assert alert.priority == AlertPriority.CRITICAL
        assert alert.title == "Points expiring"
        assert alert.message == "Your United miles expire in 30 days."
        assert alert.program_code == "united"
        assert alert.action_url == "/api/portfolio"
        assert alert.expires_at is None

    def test_optional_fields_default_to_none(self) -> None:
        alert = Alert(
            id="alert-3",
            alert_type=AlertType.SWEET_SPOT,
            priority=AlertPriority.LOW,
            title="Sweet spot found",
            message="Great deal available.",
            program_code=None,
            action_url=None,
            created_at="2026-03-09T00:00:00Z",
            expires_at=None,
        )
        assert alert.program_code is None
        assert alert.action_url is None


def _build_bonus_graph() -> TransferGraph:
    """Build a graph with an active transfer bonus."""
    graph = TransferGraph()
    graph.add_partner(
        TransferPartner(source_program="amex-mr", target_program="ana", transfer_ratio=1.0, transfer_bonus=0.30)
    )
    graph.add_partner(TransferPartner(source_program="chase-ur", target_program="hyatt", transfer_ratio=1.0))
    graph.add_redemption(
        RedemptionOption(program="ana", description="ANA First SFO-NRT", points_required=110000, cash_value=16500.0)
    )
    return graph


class TestAlertEngine:
    def test_check_transfer_bonuses_finds_bonuses(self) -> None:
        graph = _build_bonus_graph()
        engine = AlertEngine()
        alerts = engine.check_transfer_bonuses(graph)
        assert len(alerts) >= 1
        bonus_alerts = [a for a in alerts if a.alert_type == AlertType.TRANSFER_BONUS]
        assert len(bonus_alerts) >= 1
        # The amex-mr -> ana 30% bonus should be found
        programs = [a.program_code for a in bonus_alerts]
        assert "amex-mr" in programs

    def test_check_transfer_bonuses_no_bonuses(self) -> None:
        graph = TransferGraph()
        graph.add_partner(TransferPartner(source_program="chase-ur", target_program="united", transfer_ratio=1.0))
        engine = AlertEngine()
        alerts = engine.check_transfer_bonuses(graph)
        assert len(alerts) == 0

    def test_check_expirations_wraps_alerts(self) -> None:
        engine = AlertEngine()
        balances = [
            PointBalance(program_code="hilton", points=310000, cpp_baseline=Decimal("0.47")),
        ]
        # Hilton expires after 12 months inactivity
        policies = [
            ExpirationPolicy(
                program_code="hilton", expires=True, months_inactivity=12, activity_types=["stay", "earn", "redeem"]
            ),
        ]
        alerts = engine.check_expirations(balances, policies)
        assert len(alerts) >= 1
        exp_alerts = [a for a in alerts if a.alert_type == AlertType.EXPIRATION]
        assert len(exp_alerts) >= 1

    def test_check_expirations_no_expiring_programs(self) -> None:
        engine = AlertEngine()
        balances = [
            PointBalance(program_code="chase-ur", points=95000, cpp_baseline=Decimal("1.85")),
        ]
        policies = [
            ExpirationPolicy(program_code="chase-ur", expires=False, months_inactivity=None, activity_types=[]),
        ]
        alerts = engine.check_expirations(balances, policies)
        assert len(alerts) == 0

    def test_generate_alerts_combines_and_sorts_by_priority(self) -> None:
        graph = _build_bonus_graph()
        engine = AlertEngine()
        balances = [
            PointBalance(program_code="hilton", points=310000, cpp_baseline=Decimal("0.47")),
        ]
        policies = [
            ExpirationPolicy(
                program_code="hilton", expires=True, months_inactivity=12, activity_types=["stay", "earn", "redeem"]
            ),
        ]
        alerts = engine.generate_alerts(balances, graph, policies)
        assert len(alerts) >= 2  # at least one bonus + one expiration
        # Verify sorted by priority order: CRITICAL > HIGH > MEDIUM > LOW
        priority_order = {
            AlertPriority.CRITICAL: 0,
            AlertPriority.HIGH: 1,
            AlertPriority.MEDIUM: 2,
            AlertPriority.LOW: 3,
        }
        priorities = [priority_order[a.priority] for a in alerts]
        assert priorities == sorted(priorities)
