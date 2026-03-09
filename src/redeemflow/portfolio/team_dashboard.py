"""Team points dashboard — aggregate view of multi-member loyalty portfolios.

Beck: The simplest thing that could work.
Fowler: Frozen dataclasses for results, Protocol for fetcher dependency.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from redeemflow.portfolio.models import PointBalance
from redeemflow.portfolio.ports import BalanceFetcher
from redeemflow.valuations.models import ProgramValuation


@dataclass(frozen=True)
class TeamMember:
    user_id: str
    name: str
    cards: list[str]
    total_points: int
    total_value: Decimal


@dataclass(frozen=True)
class TeamDashboard:
    team_name: str
    members: list[TeamMember]
    total_points: int
    total_value: Decimal
    card_count: int


class TeamDashboardService:
    """Builds aggregate dashboards from individual member balances."""

    def __init__(self, fetcher: BalanceFetcher, valuations: dict[str, ProgramValuation]) -> None:
        self._fetcher = fetcher
        self._valuations = valuations

    def build_dashboard(self, team_name: str, member_ids: list[str]) -> TeamDashboard:
        members: list[TeamMember] = []
        total_points = 0
        total_value = Decimal("0")
        total_cards = 0

        for user_id in member_ids:
            balances = self._fetcher.fetch_balances(user_id)
            member = self._build_member(user_id, balances)
            members.append(member)
            total_points += member.total_points
            total_value += member.total_value
            total_cards += len(member.cards)

        return TeamDashboard(
            team_name=team_name,
            members=members,
            total_points=total_points,
            total_value=total_value,
            card_count=total_cards,
        )

    def _build_member(self, user_id: str, balances: list[PointBalance]) -> TeamMember:
        cards = [b.program_code for b in balances]
        member_points = sum(b.points for b in balances)
        member_value = sum(b.estimated_value_dollars for b in balances)

        return TeamMember(
            user_id=user_id,
            name=user_id,  # Name lookup deferred to identity service integration
            cards=cards,
            total_points=member_points,
            total_value=member_value,
        )
