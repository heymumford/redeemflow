"""Repository roundtrip tests — save domain object, fetch, assert equality.

Beck: Red-green — verify each repository preserves domain data through SQL layer.
Fowler: Test at the boundary — repository is the integration seam.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from redeemflow.charity.models import CharityCategory
from redeemflow.community.forum import ForumCategory
from redeemflow.community.founders_network import FounderStatus
from redeemflow.community.models import PoolStatus
from redeemflow.infra.pg_repositories import (
    PgAutoDonateRepository,
    PgCharityAlignmentRepository,
    PgCharityPartnerRepository,
    PgDonationRepository,
    PgForumRepository,
    PgFounderRepository,
    PgLoyaltyProgramRepository,
    PgPoolRepository,
    PgSubscriptionRepository,
    PgTransferPartnerRepository,
    PgUserPortfolioRepository,
    Repository,
)
from redeemflow.portfolio.models import ProgramCategory
from tests.fixtures.builders import (
    build_auto_donate_rule,
    build_charity,
    build_charity_alignment,
    build_donation,
    build_forum_post,
    build_forum_reply,
    build_founder,
    build_pledge,
    build_pool,
    build_program,
    build_subscription,
    build_transfer_partner,
)

# --- Repository Protocol ---


@pytest.mark.integration
class TestRepositoryProtocol:
    def test_loyalty_program_repo_satisfies_protocol(self, session_factory):
        repo = PgLoyaltyProgramRepository(session_factory)
        assert isinstance(repo, Repository)

    def test_subscription_repo_satisfies_protocol(self, session_factory):
        repo = PgSubscriptionRepository(session_factory)
        assert isinstance(repo, Repository)

    def test_donation_repo_satisfies_protocol(self, session_factory):
        repo = PgDonationRepository(session_factory)
        assert isinstance(repo, Repository)

    def test_pool_repo_satisfies_protocol(self, session_factory):
        repo = PgPoolRepository(session_factory)
        assert isinstance(repo, Repository)


# --- Loyalty Program Repository ---


@pytest.mark.integration
class TestPgLoyaltyProgramRepository:
    def test_save_and_fetch(self, session_factory):
        repo = PgLoyaltyProgramRepository(session_factory)
        program = build_program(code="amex-mr", name="Amex Membership Rewards")
        repo.save(program)
        fetched = repo.get("amex-mr")
        assert fetched is not None
        assert fetched.name == "Amex Membership Rewards"
        assert fetched.category == ProgramCategory.CREDIT_CARD

    def test_upsert(self, session_factory):
        repo = PgLoyaltyProgramRepository(session_factory)
        repo.save(build_program(code="test-prog", name="Original"))
        repo.save(build_program(code="test-prog", name="Updated"))
        assert repo.get("test-prog").name == "Updated"

    def test_list_all(self, session_factory):
        repo = PgLoyaltyProgramRepository(session_factory)
        repo.save(build_program(code="p1", name="Program 1"))
        repo.save(build_program(code="p2", name="Program 2"))
        assert len(repo.list_all()) == 2

    def test_delete(self, session_factory):
        repo = PgLoyaltyProgramRepository(session_factory)
        repo.save(build_program(code="del-me", name="Delete Me"))
        assert repo.delete("del-me") is True
        assert repo.get("del-me") is None

    def test_delete_nonexistent(self, session_factory):
        repo = PgLoyaltyProgramRepository(session_factory)
        assert repo.delete("no-such") is False

    def test_not_found(self, session_factory):
        repo = PgLoyaltyProgramRepository(session_factory)
        assert repo.get("ghost") is None

    def test_cpp_range_preserved(self, session_factory):
        repo = PgLoyaltyProgramRepository(session_factory)
        program = build_program(code="cpp-test", name="CPP Test", cpp_min=0.5, cpp_max=3.5)
        repo.save(program)
        fetched = repo.get("cpp-test")
        assert fetched.cpp_min == pytest.approx(0.5)
        assert fetched.cpp_max == pytest.approx(3.5)


# --- Transfer Partner Repository ---


@pytest.mark.integration
class TestPgTransferPartnerRepository:
    def test_save_and_fetch_by_source(self, session_factory):
        repo = PgTransferPartnerRepository(session_factory)
        partner = build_transfer_partner(source_program="chase-ur", target_program="hyatt")
        repo.save(partner)
        fetched = repo.get_by_source("chase-ur")
        assert len(fetched) == 1
        assert fetched[0].target_program == "hyatt"

    def test_list_all(self, session_factory):
        repo = PgTransferPartnerRepository(session_factory)
        repo.save(build_transfer_partner(source_program="a", target_program="b"))
        repo.save(build_transfer_partner(source_program="c", target_program="d"))
        assert len(repo.list_all()) == 2

    def test_transfer_ratio_preserved(self, session_factory):
        repo = PgTransferPartnerRepository(session_factory)
        partner = build_transfer_partner(
            source_program="x", target_program="y", transfer_ratio=1.5, transfer_bonus=0.25
        )
        repo.save(partner)
        fetched = repo.get_by_source("x")
        assert fetched[0].transfer_ratio == pytest.approx(1.5)
        assert fetched[0].transfer_bonus == pytest.approx(0.25)

    def test_delete_by_source_target(self, session_factory):
        repo = PgTransferPartnerRepository(session_factory)
        repo.save(build_transfer_partner(source_program="del-s", target_program="del-t"))
        assert repo.delete_by_source_target("del-s", "del-t") is True
        assert repo.get_by_source("del-s") == []


# --- User Portfolio Repository ---


@pytest.mark.integration
class TestPgUserPortfolioRepository:
    def test_save_and_fetch(self, session_factory):
        from redeemflow.portfolio.models import PointBalance, UserPortfolio

        repo = PgUserPortfolioRepository(session_factory)
        portfolio = UserPortfolio(
            user_id="user-port-1",
            balances=(
                PointBalance(program_code="chase-ur", points=50000, cpp_baseline=Decimal("1.5")),
                PointBalance(program_code="amex-mr", points=30000, cpp_baseline=Decimal("2.0")),
            ),
        )
        repo.save(portfolio)
        fetched = repo.get("user-port-1")
        assert fetched is not None
        assert fetched.user_id == "user-port-1"
        assert len(fetched.balances) == 2

    def test_balance_decimal_precision(self, session_factory):
        from redeemflow.portfolio.models import PointBalance, UserPortfolio

        repo = PgUserPortfolioRepository(session_factory)
        portfolio = UserPortfolio(
            user_id="user-dec-port",
            balances=(PointBalance(program_code="test", points=10000, cpp_baseline=Decimal("1.2345")),),
        )
        repo.save(portfolio)
        fetched = repo.get("user-dec-port")
        assert fetched.balances[0].cpp_baseline == Decimal("1.2345")

    def test_update_replaces_balances(self, session_factory):
        from redeemflow.portfolio.models import PointBalance, UserPortfolio

        repo = PgUserPortfolioRepository(session_factory)
        # Save initial
        repo.save(
            UserPortfolio(
                user_id="user-upd",
                balances=(PointBalance(program_code="old", points=1000, cpp_baseline=Decimal("1.0")),),
            )
        )
        # Update with new balances
        repo.save(
            UserPortfolio(
                user_id="user-upd",
                balances=(PointBalance(program_code="new", points=2000, cpp_baseline=Decimal("2.0")),),
            )
        )
        fetched = repo.get("user-upd")
        assert len(fetched.balances) == 1
        assert fetched.balances[0].program_code == "new"

    def test_list_all(self, session_factory):
        from redeemflow.portfolio.models import UserPortfolio

        repo = PgUserPortfolioRepository(session_factory)
        repo.save(UserPortfolio(user_id="u1"))
        repo.save(UserPortfolio(user_id="u2"))
        assert len(repo.list_all()) == 2

    def test_delete(self, session_factory):
        from redeemflow.portfolio.models import UserPortfolio

        repo = PgUserPortfolioRepository(session_factory)
        repo.save(UserPortfolio(user_id="del-port"))
        assert repo.delete("del-port") is True
        assert repo.get("del-port") is None

    def test_empty_portfolio(self, session_factory):
        from redeemflow.portfolio.models import UserPortfolio

        repo = PgUserPortfolioRepository(session_factory)
        repo.save(UserPortfolio(user_id="empty-port"))
        fetched = repo.get("empty-port")
        assert fetched is not None
        assert len(fetched.balances) == 0

    def test_not_found(self, session_factory):
        repo = PgUserPortfolioRepository(session_factory)
        assert repo.get("ghost") is None


# --- Charity Partner Repository ---


@pytest.mark.integration
class TestPgCharityPartnerRepository:
    def test_save_and_fetch(self, session_factory):
        repo = PgCharityPartnerRepository(session_factory)
        charity = build_charity(name="Local Charity", state="TX")
        repo.save(charity)
        fetched = repo.get_by_name_state("Local Charity", "TX")
        assert fetched is not None
        assert fetched.name == "Local Charity"
        assert fetched.state == "TX"
        assert fetched.is_501c3 is True

    def test_by_state(self, session_factory):
        repo = PgCharityPartnerRepository(session_factory)
        repo.save(build_charity(name="CA Charity", state="CA"))
        repo.save(build_charity(name="TX Charity", state="TX"))
        ca_charities = repo.by_state("CA")
        assert len(ca_charities) == 1
        assert ca_charities[0].name == "CA Charity"

    def test_by_category(self, session_factory):
        repo = PgCharityPartnerRepository(session_factory)
        repo.save(build_charity(name="Ed Charity", category=CharityCategory.EDUCATION))
        repo.save(build_charity(name="Art Charity", category=CharityCategory.ARTS))
        ed = repo.by_category(CharityCategory.EDUCATION)
        assert len(ed) == 1
        assert ed[0].name == "Ed Charity"

    def test_list_all(self, session_factory):
        repo = PgCharityPartnerRepository(session_factory)
        repo.save(build_charity(name="C1", state="CA"))
        repo.save(build_charity(name="C2", state="TX"))
        assert len(repo.list_all()) == 2

    def test_delete(self, session_factory):
        repo = PgCharityPartnerRepository(session_factory)
        repo.save(build_charity(name="Del Me", state="NY"))
        assert repo.delete_by_name_state("Del Me", "NY") is True
        assert repo.get_by_name_state("Del Me", "NY") is None

    def test_not_found(self, session_factory):
        repo = PgCharityPartnerRepository(session_factory)
        assert repo.get_by_name_state("Ghost", "XX") is None

    def test_optional_fields_preserved(self, session_factory):
        repo = PgCharityPartnerRepository(session_factory)
        charity = build_charity(
            name="Full Charity",
            state="CA",
            chapter_name="Bay Area Chapter",
            ein="12-3456789",
            description="A great charity",
        )
        repo.save(charity)
        fetched = repo.get_by_name_state("Full Charity", "CA")
        assert fetched.chapter_name == "Bay Area Chapter"
        assert fetched.ein == "12-3456789"
        assert fetched.description == "A great charity"


# --- Existing repository tests (preserved from Sprint 3) ---


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

    def test_get_by_id(self, session_factory):
        repo = PgDonationRepository(session_factory)
        donation = build_donation()
        repo.save(donation)
        assert repo.get(donation.id) is not None

    def test_delete(self, session_factory):
        repo = PgDonationRepository(session_factory)
        donation = build_donation()
        repo.save(donation)
        assert repo.delete(donation.id) is True
        assert repo.get(donation.id) is None


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

    def test_delete(self, session_factory):
        repo = PgSubscriptionRepository(session_factory)
        sub = build_subscription()
        repo.save(sub)
        assert repo.delete(sub.id) is True
        assert repo.get(sub.id) is None

    def test_list_all(self, session_factory):
        repo = PgSubscriptionRepository(session_factory)
        repo.save(build_subscription())
        repo.save(build_subscription())
        assert len(repo.list_all()) == 2


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

    def test_delete(self, session_factory):
        repo = PgPoolRepository(session_factory)
        pool = build_pool()
        repo.save(pool)
        assert repo.delete(pool.id) is True
        assert repo.get(pool.id) is None


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
