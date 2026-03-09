"""Optimization domain — personalized action optimizer.

Analyzes a user's portfolio and produces ranked actions:
transfer, redeem, hold, or earn recommendations based on
graph analysis, bonus opportunities, and valuation data.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from redeemflow.optimization.graph import TransferGraph
from redeemflow.portfolio.models import PointBalance
from redeemflow.valuations.models import ProgramValuation


@dataclass(frozen=True)
class PersonalizedAction:
    """A single recommended action for a user's loyalty program balance."""

    program_code: str
    action_type: str  # "transfer", "redeem", "hold", "earn"
    description: str
    estimated_value_gain: Decimal
    urgency: str  # "immediate", "soon", "opportunity"
    confidence: str  # "high", "medium", "low"
    details: dict


class PersonalOptimizer:
    """Produces personalized optimization actions for a portfolio."""

    def __init__(self, graph: TransferGraph, valuations: dict[str, ProgramValuation]) -> None:
        self._graph = graph
        self._valuations = valuations

    def optimize(self, balances: list[PointBalance]) -> list[PersonalizedAction]:
        """Analyze all balances and produce ranked actions."""
        if not balances:
            return []

        actions: list[PersonalizedAction] = []
        for balance in balances:
            actions.extend(self._analyze_balance(balance))

        return sorted(actions, key=lambda a: a.estimated_value_gain, reverse=True)

    def top_actions(self, balances: list[PointBalance], n: int = 5) -> list[PersonalizedAction]:
        """Return the top N actions by estimated value gain."""
        return self.optimize(balances)[:n]

    def _analyze_balance(self, balance: PointBalance) -> list[PersonalizedAction]:
        """Generate all possible actions for a single balance."""
        actions: list[PersonalizedAction] = []

        # Check transfer paths with bonuses
        transfer_actions = self._check_transfers(balance)
        actions.extend(transfer_actions)

        # Check direct redemption sweet spots
        redeem_actions = self._check_redemptions(balance)
        actions.extend(redeem_actions)

        # If no transfer or redeem actions found, suggest hold
        if not transfer_actions and not redeem_actions:
            actions.append(self._hold_action(balance))

        return actions

    def _check_transfers(self, balance: PointBalance) -> list[PersonalizedAction]:
        """Check for beneficial transfer paths, prioritizing active bonuses."""
        actions: list[PersonalizedAction] = []
        partners = self._graph.get_partners_from(balance.program_code)

        for partner in partners:
            if partner.transfer_bonus > 0:
                bonus_pct = int(partner.transfer_bonus * 100)
                bonus_points = int(balance.points * partner.transfer_bonus)
                effective_points = int(balance.points * partner.effective_ratio)

                # Estimate value gain from the bonus points
                target_val = self._valuations.get(partner.target_program)
                if target_val:
                    bonus_value = (Decimal(bonus_points) * target_val.median_cpp / Decimal(100)).quantize(
                        Decimal("0.01")
                    )
                else:
                    bonus_value = (Decimal(bonus_points) * balance.cpp_baseline / Decimal(100)).quantize(
                        Decimal("0.01")
                    )

                actions.append(
                    PersonalizedAction(
                        program_code=balance.program_code,
                        action_type="transfer",
                        description=(
                            f"Transfer {balance.points:,} {balance.program_code} to "
                            f"{partner.target_program} -- {bonus_pct}% bonus active = "
                            f"{effective_points:,} {partner.target_program} miles"
                        ),
                        estimated_value_gain=bonus_value,
                        urgency="immediate",
                        confidence="high",
                        details={
                            "target": partner.target_program,
                            "bonus_pct": bonus_pct,
                            "effective_points": effective_points,
                        },
                    )
                )

        # Check graph for best transfer path (non-bonus)
        best_path = self._graph.find_best_path(balance.program_code, balance.points)
        if best_path is not None:
            effective_cpp = Decimal(str(round(best_path.effective_cpp, 2)))
            cpp_gain = effective_cpp - balance.cpp_baseline
            if cpp_gain > 0:
                value_gain = (Decimal(balance.points) * cpp_gain / Decimal(100)).quantize(Decimal("0.01"))
                target = best_path.steps[-1].target_program if best_path.steps else balance.program_code
                actions.append(
                    PersonalizedAction(
                        program_code=balance.program_code,
                        action_type="transfer",
                        description=(
                            f"Transfer to {target} for {best_path.redemption.description} "
                            f"({effective_cpp} CPP vs {balance.cpp_baseline} baseline)"
                        ),
                        estimated_value_gain=value_gain,
                        urgency="soon",
                        confidence="medium",
                        details={
                            "target": target,
                            "redemption": best_path.redemption.description,
                            "effective_cpp": str(effective_cpp),
                            "hops": best_path.total_hops,
                        },
                    )
                )

        return actions

    def _check_redemptions(self, balance: PointBalance) -> list[PersonalizedAction]:
        """Check for direct redemption sweet spots at the program."""
        actions: list[PersonalizedAction] = []
        redemptions = self._graph.get_redemptions(balance.program_code)

        for redemption in redemptions:
            if balance.points >= redemption.points_required:
                cpp = Decimal(str(round(redemption.cpp, 2)))
                cpp_gain = cpp - balance.cpp_baseline
                if cpp_gain > 0:
                    value_gain = (Decimal(redemption.points_required) * cpp_gain / Decimal(100)).quantize(
                        Decimal("0.01")
                    )
                    actions.append(
                        PersonalizedAction(
                            program_code=balance.program_code,
                            action_type="redeem",
                            description=(
                                f"Redeem {redemption.points_required:,} {balance.program_code} for "
                                f"{redemption.description}"
                            ),
                            estimated_value_gain=value_gain,
                            urgency="soon",
                            confidence="high",
                            details={
                                "redemption": redemption.description,
                                "points_required": redemption.points_required,
                                "cash_value": redemption.cash_value,
                                "cpp": str(cpp),
                            },
                        )
                    )

        return actions

    def _hold_action(self, balance: PointBalance) -> PersonalizedAction:
        """Generate a hold action when no transfer/redeem is beneficial."""
        val = self._valuations.get(balance.program_code)
        if val:
            rationale = f"No active bonuses. {val.program_name} CPP median {val.median_cpp} is solid."
        else:
            rationale = f"No active bonuses or known sweet spots for {balance.program_code}."

        return PersonalizedAction(
            program_code=balance.program_code,
            action_type="hold",
            description=f"Hold {balance.points:,} {balance.program_code} -- {rationale}",
            estimated_value_gain=Decimal("0.00"),
            urgency="opportunity",
            confidence="medium",
            details={"rationale": rationale},
        )
