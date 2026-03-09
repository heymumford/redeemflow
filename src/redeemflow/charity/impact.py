"""Impact tracking — aggregation of donation data for users and community.

Beck: The simplest thing that could work.
Fowler: Frozen dataclasses for value objects, pure functions for aggregation.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal

from redeemflow.charity.donation_flow import Donation, DonationStatus


@dataclass(frozen=True)
class ImpactMetric:
    user_id: str
    total_donated: Decimal
    donation_count: int
    charities_supported: int
    states_reached: int
    top_charity: str | None = None


@dataclass(frozen=True)
class CommunityImpact:
    total_donated: Decimal
    total_donors: int
    total_donations: int
    unique_charities: int
    unique_states: int
    top_charities: list[tuple[str, Decimal]] = field(default_factory=list)


class ImpactTracker:
    """Aggregates donation data into impact metrics."""

    def __init__(self, donations: list[Donation]) -> None:
        self._donations = donations

    def _completed(self) -> list[Donation]:
        return [d for d in self._donations if d.status == DonationStatus.COMPLETED]

    def user_impact(self, user_id: str) -> ImpactMetric:
        user_donations = [d for d in self._completed() if d.user_id == user_id]

        if not user_donations:
            return ImpactMetric(
                user_id=user_id,
                total_donated=Decimal("0"),
                donation_count=0,
                charities_supported=0,
                states_reached=0,
                top_charity=None,
            )

        total = sum((d.dollar_value for d in user_donations), Decimal("0"))
        charities = {d.charity_name for d in user_donations}
        states = {d.charity_state for d in user_donations}

        # Find top charity by total donated
        by_charity: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        for d in user_donations:
            by_charity[d.charity_name] += d.dollar_value
        top_charity = max(by_charity, key=lambda k: by_charity[k])

        return ImpactMetric(
            user_id=user_id,
            total_donated=total,
            donation_count=len(user_donations),
            charities_supported=len(charities),
            states_reached=len(states),
            top_charity=top_charity,
        )

    def community_impact(self) -> CommunityImpact:
        completed = self._completed()

        if not completed:
            return CommunityImpact(
                total_donated=Decimal("0"),
                total_donors=0,
                total_donations=0,
                unique_charities=0,
                unique_states=0,
                top_charities=[],
            )

        total = sum((d.dollar_value for d in completed), Decimal("0"))
        donors = {d.user_id for d in completed}
        charities = {d.charity_name for d in completed}
        states = {d.charity_state for d in completed}

        by_charity: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        for d in completed:
            by_charity[d.charity_name] += d.dollar_value
        top_charities = sorted(by_charity.items(), key=lambda x: x[1], reverse=True)

        return CommunityImpact(
            total_donated=total,
            total_donors=len(donors),
            total_donations=len(completed),
            unique_charities=len(charities),
            unique_states=len(states),
            top_charities=top_charities,
        )

    def impact_by_state(self) -> dict[str, Decimal]:
        result: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        for d in self._completed():
            result[d.charity_state] += d.dollar_value
        return dict(result)

    def impact_by_charity(self) -> dict[str, Decimal]:
        result: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        for d in self._completed():
            result[d.charity_name] += d.dollar_value
        return dict(result)
