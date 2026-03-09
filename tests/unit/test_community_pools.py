"""Community pools tests — TDD: written before implementation.

Tests the community pool domain: value objects, pool service, pledge lifecycle.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from redeemflow.charity.donation_flow import DonationService, FakeDonationProvider
from redeemflow.charity.seed_data import CHARITY_NETWORK
from redeemflow.community.models import (
    CommunityPool,
    Pledge,
    PoolService,
    PoolStatus,
)
from redeemflow.valuations.seed_data import PROGRAM_VALUATIONS


class TestPoolStatus:
    def test_enum_values(self):
        assert PoolStatus.OPEN == "open"
        assert PoolStatus.ACTIVE == "active"
        assert PoolStatus.GOAL_REACHED == "goal_reached"
        assert PoolStatus.COMPLETED == "completed"
        assert PoolStatus.CANCELLED == "cancelled"

    def test_all_statuses_present(self):
        names = {s.value for s in PoolStatus}
        assert names == {"open", "active", "goal_reached", "completed", "cancelled"}


class TestPledge:
    def test_frozen_dataclass(self):
        p = Pledge(
            id="pledge-1",
            user_id="auth0|eric",
            pool_id="pool-1",
            program_code="chase-ur",
            points_pledged=10000,
            dollar_value=Decimal("170.00"),
            pledged_at="2026-03-09T00:00:00Z",
        )
        with pytest.raises(AttributeError):
            p.id = "pledge-2"  # type: ignore[misc]

    def test_dollar_value_is_decimal(self):
        p = Pledge(
            id="pledge-1",
            user_id="auth0|eric",
            pool_id="pool-1",
            program_code="chase-ur",
            points_pledged=10000,
            dollar_value=Decimal("170.00"),
            pledged_at="2026-03-09T00:00:00Z",
        )
        assert isinstance(p.dollar_value, Decimal)


class TestCommunityPool:
    def _make_pool(self) -> CommunityPool:
        return CommunityPool(
            id="pool-1",
            name="Girl Scout Cookie Drive",
            creator_id="auth0|eric",
            target_charity_name="Girl Scouts of the USA",
            target_charity_state="TX",
            goal_amount=Decimal("500.00"),
            status=PoolStatus.OPEN,
            pledges=[],
            created_at="2026-03-09T00:00:00Z",
        )

    def test_total_pledged_empty(self):
        pool = self._make_pool()
        assert pool.total_pledged() == Decimal("0")

    def test_total_pledged_with_pledges(self):
        pool = self._make_pool()
        pool.add_pledge(
            Pledge(
                id="p1",
                user_id="auth0|eric",
                pool_id="pool-1",
                program_code="chase-ur",
                points_pledged=10000,
                dollar_value=Decimal("170.00"),
                pledged_at="2026-03-09T00:00:00Z",
            )
        )
        pool.add_pledge(
            Pledge(
                id="p2",
                user_id="auth0|steve",
                pool_id="pool-1",
                program_code="amex-mr",
                points_pledged=5000,
                dollar_value=Decimal("85.00"),
                pledged_at="2026-03-09T00:00:00Z",
            )
        )
        assert pool.total_pledged() == Decimal("255.00")

    def test_progress_pct_zero(self):
        pool = self._make_pool()
        assert pool.progress_pct() == Decimal("0")

    def test_progress_pct_partial(self):
        pool = self._make_pool()
        pool.add_pledge(
            Pledge(
                id="p1",
                user_id="auth0|eric",
                pool_id="pool-1",
                program_code="chase-ur",
                points_pledged=10000,
                dollar_value=Decimal("250.00"),
                pledged_at="2026-03-09T00:00:00Z",
            )
        )
        assert pool.progress_pct() == Decimal("50.00")

    def test_is_goal_reached_false(self):
        pool = self._make_pool()
        assert pool.is_goal_reached() is False

    def test_is_goal_reached_true(self):
        pool = self._make_pool()
        pool.add_pledge(
            Pledge(
                id="p1",
                user_id="auth0|eric",
                pool_id="pool-1",
                program_code="chase-ur",
                points_pledged=10000,
                dollar_value=Decimal("500.00"),
                pledged_at="2026-03-09T00:00:00Z",
            )
        )
        assert pool.is_goal_reached() is True

    def test_is_goal_reached_over(self):
        pool = self._make_pool()
        pool.add_pledge(
            Pledge(
                id="p1",
                user_id="auth0|eric",
                pool_id="pool-1",
                program_code="chase-ur",
                points_pledged=10000,
                dollar_value=Decimal("600.00"),
                pledged_at="2026-03-09T00:00:00Z",
            )
        )
        assert pool.is_goal_reached() is True

    def test_add_pledge_updates_list(self):
        pool = self._make_pool()
        assert len(pool.pledges) == 0
        pool.add_pledge(
            Pledge(
                id="p1",
                user_id="auth0|eric",
                pool_id="pool-1",
                program_code="chase-ur",
                points_pledged=10000,
                dollar_value=Decimal("170.00"),
                pledged_at="2026-03-09T00:00:00Z",
            )
        )
        assert len(pool.pledges) == 1


def _make_donation_service() -> DonationService:
    return DonationService(
        provider=FakeDonationProvider(),
        valuations=PROGRAM_VALUATIONS,
        charity_network=CHARITY_NETWORK,
    )


class TestPoolService:
    def test_create_pool(self):
        service = PoolService(donation_service=_make_donation_service())
        pool = service.create_pool(
            creator_id="auth0|eric",
            name="Girl Scout Drive",
            target_charity_name="Girl Scouts of the USA",
            target_charity_state="TX",
            goal_amount=Decimal("500.00"),
        )
        assert isinstance(pool, CommunityPool)
        assert pool.name == "Girl Scout Drive"
        assert pool.status == PoolStatus.OPEN
        assert pool.goal_amount == Decimal("500.00")

    def test_pledge_to_pool(self):
        service = PoolService(donation_service=_make_donation_service())
        pool = service.create_pool(
            creator_id="auth0|eric",
            name="Girl Scout Drive",
            target_charity_name="Girl Scouts of the USA",
            target_charity_state="TX",
            goal_amount=Decimal("500.00"),
        )
        pledge = service.pledge(
            pool_id=pool.id,
            user_id="auth0|steve",
            program_code="chase-ur",
            points=10000,
        )
        assert isinstance(pledge, Pledge)
        assert pledge.pool_id == pool.id
        assert pledge.user_id == "auth0|steve"
        assert pledge.points_pledged == 10000
        assert isinstance(pledge.dollar_value, Decimal)

    def test_complete_pool_executes_donation_when_goal_met(self):
        service = PoolService(donation_service=_make_donation_service())
        pool = service.create_pool(
            creator_id="auth0|eric",
            name="Girl Scout Drive",
            target_charity_name="Girl Scouts of the USA",
            target_charity_state="TX",
            goal_amount=Decimal("10.00"),
        )
        service.pledge(
            pool_id=pool.id,
            user_id="auth0|eric",
            program_code="chase-ur",
            points=10000,
        )
        completed = service.complete_pool(pool.id)
        assert completed.status == PoolStatus.COMPLETED
        assert completed.completed_at is not None

    def test_complete_pool_goal_not_met_raises(self):
        service = PoolService(donation_service=_make_donation_service())
        pool = service.create_pool(
            creator_id="auth0|eric",
            name="Girl Scout Drive",
            target_charity_name="Girl Scouts of the USA",
            target_charity_state="TX",
            goal_amount=Decimal("999999.00"),
        )
        with pytest.raises(ValueError, match="goal"):
            service.complete_pool(pool.id)

    def test_list_pools(self):
        service = PoolService(donation_service=_make_donation_service())
        service.create_pool(
            creator_id="auth0|eric",
            name="Pool A",
            target_charity_name="Girl Scouts of the USA",
            target_charity_state="TX",
            goal_amount=Decimal("100.00"),
        )
        service.create_pool(
            creator_id="auth0|steve",
            name="Pool B",
            target_charity_name="AAUW",
            target_charity_state="CA",
            goal_amount=Decimal("200.00"),
        )
        pools = service.list_pools()
        assert len(pools) == 2

    def test_get_pool(self):
        service = PoolService(donation_service=_make_donation_service())
        pool = service.create_pool(
            creator_id="auth0|eric",
            name="Pool A",
            target_charity_name="Girl Scouts of the USA",
            target_charity_state="TX",
            goal_amount=Decimal("100.00"),
        )
        found = service.get_pool(pool.id)
        assert found is not None
        assert found.id == pool.id

    def test_get_pool_not_found(self):
        service = PoolService(donation_service=_make_donation_service())
        assert service.get_pool("nonexistent-pool") is None

    def test_pledge_to_nonexistent_pool_raises(self):
        service = PoolService(donation_service=_make_donation_service())
        with pytest.raises(ValueError, match="[Pp]ool"):
            service.pledge(
                pool_id="nonexistent-pool",
                user_id="auth0|eric",
                program_code="chase-ur",
                points=10000,
            )

    def test_create_pool_zero_goal_raises(self):
        service = PoolService(donation_service=_make_donation_service())
        with pytest.raises(ValueError, match="goal_amount"):
            service.create_pool(
                creator_id="auth0|eric",
                name="Bad Pool",
                target_charity_name="Girl Scouts of the USA",
                target_charity_state="TX",
                goal_amount=Decimal("0"),
            )

    def test_create_pool_negative_goal_raises(self):
        service = PoolService(donation_service=_make_donation_service())
        with pytest.raises(ValueError, match="goal_amount"):
            service.create_pool(
                creator_id="auth0|eric",
                name="Bad Pool",
                target_charity_name="Girl Scouts of the USA",
                target_charity_state="TX",
                goal_amount=Decimal("-10.00"),
            )
