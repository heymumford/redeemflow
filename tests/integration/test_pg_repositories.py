"""Repository roundtrip tests — save domain object, fetch, assert equality.

Beck: Red-green — verify each repository preserves domain data through SQL layer.
Fowler: Test at the boundary — repository is the integration seam.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from redeemflow.community.forum import ForumCategory
from redeemflow.community.founders_network import FounderStatus
from redeemflow.community.models import PoolStatus
from redeemflow.infra.pg_repositories import (
    PgAutoDonateRepository,
    PgCharityAlignmentRepository,
    PgDonationRepository,
    PgForumRepository,
    PgFounderRepository,
    PgPoolRepository,
    PgSubscriptionRepository,
)
from tests.fixtures.builders import (
    build_auto_donate_rule,
    build_charity_alignment,
    build_donation,
    build_forum_post,
    build_forum_reply,
    build_founder,
    build_pledge,
    build_pool,
    build_subscription,
)


@pytest.mark.integration
class TestPgDonationRepository:
    def test_save_and_fetch_roundtrip(self, session_factory):
        repo = PgDonationRepository(session_factory)
        donation = build_donation(user_id="user-alice")
        repo.save(donation)
        fetched = repo.get_by_user("user-alice")
        assert len(fetched) == 1
        assert fetched[0].id == donation.id
        assert fetched[0].charity_name == donation.charity_name
        assert fetched[0].status == donation.status

    def test_decimal_precision_survives(self, session_factory):
        repo = PgDonationRepository(session_factory)
        donation = build_donation(user_id="user-dec", dollar_value=Decimal("123.4567"))
        repo.save(donation)
        assert repo.get_by_user("user-dec")[0].dollar_value == Decimal("123.4567")

    def test_get_all(self, session_factory):
        repo = PgDonationRepository(session_factory)
        repo.save(build_donation(user_id="a"))
        repo.save(build_donation(user_id="b"))
        assert len(repo.get_all()) == 2

    def test_empty_result(self, session_factory):
        assert PgDonationRepository(session_factory).get_by_user("ghost") == []


@pytest.mark.integration
class TestPgSubscriptionRepository:
    def test_save_and_fetch(self, session_factory):
        repo = PgSubscriptionRepository(session_factory)
        sub = build_subscription(user_id="user-sub")
        repo.save(sub)
        fetched = repo.get_by_user("user-sub")
        assert fetched is not None
        assert fetched.tier == sub.tier
        assert fetched.status == sub.status

    def test_get_by_id(self, session_factory):
        repo = PgSubscriptionRepository(session_factory)
        sub = build_subscription()
        repo.save(sub)
        assert repo.get(sub.id) is not None

    def test_update_status(self, session_factory):
        repo = PgSubscriptionRepository(session_factory)
        sub = build_subscription(status="active")
        repo.save(sub)
        repo.update_status(sub.id, "cancelled")
        assert repo.get(sub.id).status == "cancelled"

    def test_not_found(self, session_factory):
        repo = PgSubscriptionRepository(session_factory)
        assert repo.get("nope") is None
        assert repo.get_by_user("nope") is None


@pytest.mark.integration
class TestPgPoolRepository:
    def test_save_and_fetch(self, session_factory):
        repo = PgPoolRepository(session_factory)
        pool = build_pool()
        repo.save(pool)
        fetched = repo.get(pool.id)
        assert fetched is not None
        assert fetched.name == pool.name
        assert fetched.pledges == []

    def test_decimal_goal_amount(self, session_factory):
        repo = PgPoolRepository(session_factory)
        pool = build_pool(goal_amount=Decimal("999.9999"))
        repo.save(pool)
        assert repo.get(pool.id).goal_amount == Decimal("999.9999")

    def test_pledge_roundtrip(self, session_factory):
        repo = PgPoolRepository(session_factory)
        pool = build_pool()
        pledge = build_pledge(pool_id=pool.id, dollar_value=Decimal("50.25"))
        repo.save(pool)
        repo.save_pledge(pledge)
        fetched = repo.get(pool.id)
        assert len(fetched.pledges) == 1
        assert fetched.pledges[0].dollar_value == Decimal("50.25")

    def test_list_all(self, session_factory):
        repo = PgPoolRepository(session_factory)
        repo.save(build_pool())
        repo.save(build_pool())
        assert len(repo.list_all()) == 2

    def test_update_status(self, session_factory):
        repo = PgPoolRepository(session_factory)
        pool = build_pool(status=PoolStatus.OPEN)
        repo.save(pool)
        pool.status = PoolStatus.COMPLETED
        pool.completed_at = "2026-03-09T00:00:00+00:00"
        repo.save(pool)
        assert repo.get(pool.id).status == PoolStatus.COMPLETED


@pytest.mark.integration
class TestPgForumRepository:
    def test_save_post_and_fetch(self, session_factory):
        repo = PgForumRepository(session_factory)
        post = build_forum_post()
        repo.save_post(post)
        fetched = repo.get_post(post.id)
        assert fetched is not None
        assert fetched.title == post.title
        assert fetched.category == post.category

    def test_reply_roundtrip(self, session_factory):
        repo = PgForumRepository(session_factory)
        post = build_forum_post()
        reply = build_forum_reply(post_id=post.id)
        repo.save_post(post)
        repo.save_reply(reply)
        fetched = repo.get_post(post.id)
        assert len(fetched.replies) == 1
        assert fetched.replies[0].content == reply.content

    def test_list_by_category(self, session_factory):
        repo = PgForumRepository(session_factory)
        repo.save_post(build_forum_post(category=ForumCategory.STRATEGIES))
        repo.save_post(build_forum_post(category=ForumCategory.DEALS))
        assert len(repo.list_posts(ForumCategory.STRATEGIES, page=1, per_page=10)) == 1

    def test_search(self, session_factory):
        repo = PgForumRepository(session_factory)
        repo.save_post(build_forum_post(title="Best credit card strategies"))
        assert len(repo.search("credit card")) == 1

    def test_delete(self, session_factory):
        repo = PgForumRepository(session_factory)
        post = build_forum_post()
        repo.save_post(post)
        assert repo.delete_post(post.id) is True
        assert repo.get_post(post.id) is None


@pytest.mark.integration
class TestPgFounderRepository:
    def test_save_and_fetch(self, session_factory):
        repo = PgFounderRepository(session_factory)
        founder = build_founder(travel_interests=["Paris"], mentor_topics=["growth"], is_mentor=True)
        repo.save(founder)
        fetched = repo.get(founder.user_id)
        assert fetched is not None
        assert fetched.name == founder.name
        assert fetched.travel_interests == ["Paris"]
        assert fetched.mentor_topics == ["growth"]
        assert fetched.is_mentor is True

    def test_update(self, session_factory):
        repo = PgFounderRepository(session_factory)
        founder = build_founder()
        repo.save(founder)
        founder.name = "Updated"
        repo.save(founder)
        assert repo.get(founder.user_id).name == "Updated"

    def test_list_by_status(self, session_factory):
        repo = PgFounderRepository(session_factory)
        repo.save(build_founder(status=FounderStatus.ACTIVE))
        repo.save(build_founder(status=FounderStatus.PENDING))
        assert len(repo.list_members(FounderStatus.ACTIVE)) == 1

    def test_search(self, session_factory):
        repo = PgFounderRepository(session_factory)
        repo.save(build_founder(name="Jane Doe"))
        assert len(repo.search("jane")) >= 1


@pytest.mark.integration
class TestPgAutoDonateRepository:
    def test_save_and_fetch(self, session_factory):
        repo = PgAutoDonateRepository(session_factory)
        rule = build_auto_donate_rule(user_id="user-auto")
        repo.save(rule)
        fetched = repo.get_by_user("user-auto")
        assert len(fetched) == 1
        assert fetched[0].id == rule.id
        assert fetched[0].is_active is True

    def test_delete(self, session_factory):
        repo = PgAutoDonateRepository(session_factory)
        rule = build_auto_donate_rule(user_id="user-del")
        repo.save(rule)
        repo.delete(rule.id)
        assert repo.get_by_user("user-del") == []

    def test_get_all_active(self, session_factory):
        repo = PgAutoDonateRepository(session_factory)
        repo.save(build_auto_donate_rule(is_active=True, user_id="a"))
        repo.save(build_auto_donate_rule(is_active=False, user_id="b"))
        assert len(repo.get_all_active()) == 1


@pytest.mark.integration
class TestPgCharityAlignmentRepository:
    def test_save_and_fetch(self, session_factory):
        repo = PgCharityAlignmentRepository(session_factory)
        alignment = build_charity_alignment(user_id="user-align")
        repo.save(alignment)
        fetched = repo.get("user-align")
        assert fetched is not None
        assert fetched.charity_name == alignment.charity_name

    def test_decimal_precision(self, session_factory):
        repo = PgCharityAlignmentRepository(session_factory)
        alignment = build_charity_alignment(
            user_id="user-dec",
            monthly_contribution=Decimal("1.25"),
            annual_contribution=Decimal("15.00"),
        )
        repo.save(alignment)
        fetched = repo.get("user-dec")
        assert fetched.monthly_contribution == Decimal("1.25")
        assert fetched.annual_contribution == Decimal("15.00")

    def test_upsert(self, session_factory):
        repo = PgCharityAlignmentRepository(session_factory)
        repo.save(build_charity_alignment(user_id="user-up", monthly_contribution=Decimal("1.00")))
        repo.save(
            build_charity_alignment(user_id="user-up", charity_name="Updated", monthly_contribution=Decimal("2.50"))
        )
        assert repo.get("user-up").charity_name == "Updated"
