"""Auto-donate rules engine — threshold-based automatic charitable giving.

Beck: The simplest thing that could work.
Fowler: Frozen dataclass for rules, mutable engine for state.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from redeemflow.charity.donation_flow import Donation, DonationService


@dataclass(frozen=True)
class AutoDonateRule:
    id: str
    user_id: str
    program_code: str
    charity_name: str
    charity_state: str
    days_unused_threshold: int
    is_active: bool


class AutoDonateEngine:
    """Evaluates inactivity rules and triggers auto-donations."""

    def __init__(self, donation_service: DonationService) -> None:
        self._donation_service = donation_service
        self._rules: dict[str, AutoDonateRule] = {}

    def add_rule(
        self,
        user_id: str,
        program_code: str,
        charity_name: str,
        charity_state: str,
        days_threshold: int,
    ) -> AutoDonateRule:
        rule_id = f"rule-{uuid.uuid4().hex[:12]}"
        rule = AutoDonateRule(
            id=rule_id,
            user_id=user_id,
            program_code=program_code,
            charity_name=charity_name,
            charity_state=charity_state,
            days_unused_threshold=days_threshold,
            is_active=True,
        )
        self._rules[rule_id] = rule
        return rule

    def get_user_rules(self, user_id: str) -> list[AutoDonateRule]:
        return [r for r in self._rules.values() if r.user_id == user_id]

    def remove_rule(self, rule_id: str) -> None:
        self._rules.pop(rule_id, None)

    def evaluate_rules(
        self,
        balances: dict[str, int],
        last_activity_days: dict[str, int],
    ) -> list[Donation]:
        """Evaluate all active rules against current balances and activity.

        For each rule where the program's days since activity >= threshold,
        auto-donate all points for that program.
        """
        donations: list[Donation] = []
        for rule in self._rules.values():
            if not rule.is_active:
                continue

            days_inactive = last_activity_days.get(rule.program_code, 0)
            points = balances.get(rule.program_code, 0)

            if days_inactive >= rule.days_unused_threshold and points > 0:
                donation = self._donation_service.donate(
                    user_id=rule.user_id,
                    charity_name=rule.charity_name,
                    charity_state=rule.charity_state,
                    program_code=rule.program_code,
                    points=points,
                )
                donations.append(donation)

        return donations
