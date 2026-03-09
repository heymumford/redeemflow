"""Community pool domain — collective point donation pools.

Beck: The simplest thing that could work.
Fowler: Mutable aggregate root (CommunityPool) with frozen value objects (Pledge).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum

from redeemflow.charity.donation_flow import DonationService
from redeemflow.valuations.seed_data import PROGRAM_VALUATIONS


class PoolStatus(str, Enum):
    OPEN = "open"
    ACTIVE = "active"
    GOAL_REACHED = "goal_reached"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class Pledge:
    id: str
    user_id: str
    pool_id: str
    program_code: str
    points_pledged: int
    dollar_value: Decimal
    pledged_at: str


@dataclass
class CommunityPool:
    """Mutable aggregate root — state holder for pool lifecycle."""

    id: str
    name: str
    creator_id: str
    target_charity_name: str
    target_charity_state: str
    goal_amount: Decimal
    status: PoolStatus
    pledges: list[Pledge] = field(default_factory=list)
    created_at: str = ""
    completed_at: str | None = None

    def total_pledged(self) -> Decimal:
        return sum((p.dollar_value for p in self.pledges), Decimal("0"))

    def progress_pct(self) -> Decimal:
        if self.goal_amount == Decimal("0"):
            return Decimal("100.00")
        pct = (self.total_pledged() / self.goal_amount * Decimal("100")).quantize(Decimal("0.01"))
        return pct

    def is_goal_reached(self) -> bool:
        return self.total_pledged() >= self.goal_amount

    def add_pledge(self, pledge: Pledge) -> None:
        self.pledges.append(pledge)


class PoolService:
    """Orchestrates community pool lifecycle — create, pledge, complete."""

    def __init__(self, donation_service: DonationService, repository: object | None = None) -> None:
        self._donation_service = donation_service
        self._repository = repository
        self._pools: dict[str, CommunityPool] = {}

    def create_pool(
        self,
        creator_id: str,
        name: str,
        target_charity_name: str,
        target_charity_state: str,
        goal_amount: Decimal,
    ) -> CommunityPool:
        if goal_amount <= Decimal("0"):
            raise ValueError("goal_amount must be greater than zero")
        pool_id = f"pool-{uuid.uuid4().hex[:12]}"
        now = datetime.now(UTC).isoformat()
        pool = CommunityPool(
            id=pool_id,
            name=name,
            creator_id=creator_id,
            target_charity_name=target_charity_name,
            target_charity_state=target_charity_state,
            goal_amount=goal_amount,
            status=PoolStatus.OPEN,
            pledges=[],
            created_at=now,
        )
        self._pools[pool_id] = pool
        if self._repository:
            self._repository.save(pool)
        return pool

    def pledge(self, pool_id: str, user_id: str, program_code: str, points: int) -> Pledge:
        pool = self._pools.get(pool_id)
        if pool is None:
            raise ValueError(f"Pool not found: {pool_id}")

        valuation = PROGRAM_VALUATIONS.get(program_code)
        if valuation is None:
            raise ValueError(f"Unknown program: {program_code}")

        dollar_value = valuation.dollar_value(points)
        now = datetime.now(UTC).isoformat()

        pledge = Pledge(
            id=f"pledge-{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            pool_id=pool_id,
            program_code=program_code,
            points_pledged=points,
            dollar_value=dollar_value,
            pledged_at=now,
        )
        pool.add_pledge(pledge)
        if self._repository:
            self._repository.save_pledge(pledge)

        if pool.is_goal_reached():
            pool.status = PoolStatus.GOAL_REACHED

        return pledge

    def complete_pool(self, pool_id: str) -> CommunityPool:
        pool = self._pools.get(pool_id)
        if pool is None:
            raise ValueError(f"Pool not found: {pool_id}")

        if not pool.is_goal_reached():
            raise ValueError(f"Pool goal not reached: {pool.total_pledged()} of {pool.goal_amount}")

        if not pool.pledges:
            raise ValueError("Cannot complete pool with no pledges")

        # Execute aggregate donation via DonationService
        total_points = sum(p.points_pledged for p in pool.pledges)
        program_code = pool.pledges[0].program_code

        self._donation_service.donate(
            user_id=pool.creator_id,
            charity_name=pool.target_charity_name,
            charity_state=pool.target_charity_state,
            program_code=program_code,
            points=total_points,
        )

        pool.status = PoolStatus.COMPLETED
        pool.completed_at = datetime.now(UTC).isoformat()
        return pool

    def get_pool(self, pool_id: str) -> CommunityPool | None:
        return self._pools.get(pool_id)

    def list_pools(self) -> list[CommunityPool]:
        return list(self._pools.values())
