"""Notifications domain — alert generation engine.

Scans transfer graph for bonuses, wraps expiration tracker results,
and produces sorted alerts for a user's portfolio.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from redeemflow.notifications.models import Alert, AlertPriority, AlertType
from redeemflow.optimization.graph import TransferGraph
from redeemflow.portfolio.expiration import ExpirationPolicy, ExpirationTracker
from redeemflow.portfolio.models import PointBalance

_PRIORITY_ORDER = {
    AlertPriority.CRITICAL: 0,
    AlertPriority.HIGH: 1,
    AlertPriority.MEDIUM: 2,
    AlertPriority.LOW: 3,
}


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


class AlertEngine:
    """Generates alerts from transfer graph bonuses and expiration policies."""

    def check_transfer_bonuses(self, graph: TransferGraph) -> list[Alert]:
        """Scan all partners in the graph for active transfer bonuses."""
        alerts: list[Alert] = []
        for program in graph.programs:
            partners = graph.get_partners_from(program)
            for partner in partners:
                if partner.transfer_bonus > 0:
                    bonus_pct = int(partner.transfer_bonus * 100)
                    alerts.append(
                        Alert(
                            id=str(uuid.uuid4()),
                            alert_type=AlertType.TRANSFER_BONUS,
                            priority=AlertPriority.HIGH,
                            title=f"{bonus_pct}% transfer bonus: {partner.source_program} to {partner.target_program}",
                            message=(
                                f"Active {bonus_pct}% bonus when transferring from "
                                f"{partner.source_program} to {partner.target_program}. "
                                f"Effective ratio: {partner.effective_ratio:.2f}x."
                            ),
                            program_code=partner.source_program,
                            action_url=None,
                            created_at=_now_iso(),
                            expires_at=None,
                        )
                    )
        return alerts

    def check_expirations(
        self,
        balances: list[PointBalance],
        policies: list[ExpirationPolicy],
    ) -> list[Alert]:
        """Wrap ExpirationTracker results as Alert objects."""
        tracker = ExpirationTracker()
        expiration_alerts = tracker.check_expirations(balances, policies)
        alerts: list[Alert] = []
        for exp in expiration_alerts:
            if exp.alert_level <= 30:
                priority = AlertPriority.CRITICAL
            elif exp.alert_level <= 60:
                priority = AlertPriority.HIGH
            else:
                priority = AlertPriority.MEDIUM

            alerts.append(
                Alert(
                    id=str(uuid.uuid4()),
                    alert_type=AlertType.EXPIRATION,
                    priority=priority,
                    title=f"{exp.program_code} points expiring in ~{exp.days_until_expiry} days",
                    message=(
                        f"{exp.points_at_risk:,} {exp.program_code} points at risk of expiration. "
                        f"Estimated {exp.days_until_expiry} days remaining."
                    ),
                    program_code=exp.program_code,
                    action_url=None,
                    created_at=_now_iso(),
                    expires_at=None,
                )
            )
        return alerts

    def generate_alerts(
        self,
        balances: list[PointBalance],
        graph: TransferGraph,
        policies: list[ExpirationPolicy],
    ) -> list[Alert]:
        """Combined alert generation — bonuses + expirations, sorted by priority."""
        alerts = self.check_transfer_bonuses(graph) + self.check_expirations(balances, policies)
        return sorted(alerts, key=lambda a: _PRIORITY_ORDER.get(a.priority, 99))
