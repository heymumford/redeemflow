"""Postgres repository implementations — sync, SQLAlchemy Core.

Each repository maps between domain frozen dataclasses and SQL rows.
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select, delete, update
from sqlalchemy.orm import Session, sessionmaker

from redeemflow.billing.charity_alignment import CharityAlignment
from redeemflow.billing.models import Subscription, SubscriptionTier
from redeemflow.charity.auto_donate import AutoDonateRule
from redeemflow.charity.donation_flow import Donation, DonationStatus
from redeemflow.community.forum import ForumCategory, ForumPost, ForumReply
from redeemflow.community.founders_network import FounderProfile, FounderStatus
from redeemflow.community.models import CommunityPool, Pledge, PoolStatus
from redeemflow.infra.db_models import (
    auto_donate_rules,
    charity_alignments,
    community_pools,
    donations,
    forum_posts,
    forum_replies,
    founder_profiles,
    pledges,
    subscriptions,
)


class PgSubscriptionRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._sf = session_factory

    def save(self, sub: Subscription) -> None:
        with self._sf() as s:
            s.execute(
                subscriptions.insert().values(
                    id=sub.id,
                    user_id=sub.user_id,
                    tier=sub.tier.value,
                    status=sub.status,
                    current_period_start=sub.current_period_start,
                    current_period_end=sub.current_period_end,
                    stripe_subscription_id=sub.stripe_subscription_id,
                )
            )
            s.commit()

    def get_by_user(self, user_id: str) -> Subscription | None:
        with self._sf() as s:
            row = s.execute(select(subscriptions).where(subscriptions.c.user_id == user_id)).first()
            return self._to_domain(row) if row else None

    def get(self, sub_id: str) -> Subscription | None:
        with self._sf() as s:
            row = s.execute(select(subscriptions).where(subscriptions.c.id == sub_id)).first()
            return self._to_domain(row) if row else None

    def update_status(self, sub_id: str, status: str) -> None:
        with self._sf() as s:
            s.execute(update(subscriptions).where(subscriptions.c.id == sub_id).values(status=status))
            s.commit()

    @staticmethod
    def _to_domain(row) -> Subscription:
        return Subscription(
            id=row.id,
            user_id=row.user_id,
            tier=SubscriptionTier(row.tier),
            status=row.status,
            current_period_start=row.current_period_start,
            current_period_end=row.current_period_end,
            stripe_subscription_id=row.stripe_subscription_id,
        )


class PgDonationRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._sf = session_factory

    def save(self, donation: Donation) -> None:
        with self._sf() as s:
            s.execute(
                donations.insert().values(
                    id=donation.id,
                    user_id=donation.user_id,
                    charity_name=donation.charity_name,
                    charity_state=donation.charity_state,
                    program_code=donation.program_code,
                    points_donated=donation.points_donated,
                    dollar_value=donation.dollar_value,
                    status=donation.status.value,
                    created_at=donation.created_at,
                    completed_at=donation.completed_at,
                    change_api_reference=donation.change_api_reference,
                )
            )
            s.commit()

    def get_by_user(self, user_id: str) -> list[Donation]:
        with self._sf() as s:
            rows = s.execute(select(donations).where(donations.c.user_id == user_id)).fetchall()
            return [self._to_domain(r) for r in rows]

    def get_all(self) -> list[Donation]:
        with self._sf() as s:
            rows = s.execute(select(donations)).fetchall()
            return [self._to_domain(r) for r in rows]

    @staticmethod
    def _to_domain(row) -> Donation:
        return Donation(
            id=row.id,
            user_id=row.user_id,
            charity_name=row.charity_name,
            charity_state=row.charity_state,
            program_code=row.program_code,
            points_donated=row.points_donated,
            dollar_value=Decimal(str(row.dollar_value)),
            status=DonationStatus(row.status),
            created_at=row.created_at,
            completed_at=row.completed_at,
            change_api_reference=row.change_api_reference,
        )


class PgPoolRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._sf = session_factory

    def save(self, pool: CommunityPool) -> None:
        with self._sf() as s:
            existing = s.execute(select(community_pools).where(community_pools.c.id == pool.id)).first()
            if existing:
                s.execute(
                    update(community_pools)
                    .where(community_pools.c.id == pool.id)
                    .values(
                        status=pool.status.value,
                        completed_at=pool.completed_at,
                    )
                )
            else:
                s.execute(
                    community_pools.insert().values(
                        id=pool.id,
                        name=pool.name,
                        creator_id=pool.creator_id,
                        target_charity_name=pool.target_charity_name,
                        target_charity_state=pool.target_charity_state,
                        goal_amount=pool.goal_amount,
                        status=pool.status.value,
                        created_at=pool.created_at,
                        completed_at=pool.completed_at,
                    )
                )
            s.commit()

    def save_pledge(self, pledge: Pledge) -> None:
        with self._sf() as s:
            s.execute(
                pledges.insert().values(
                    id=pledge.id,
                    user_id=pledge.user_id,
                    pool_id=pledge.pool_id,
                    program_code=pledge.program_code,
                    points_pledged=pledge.points_pledged,
                    dollar_value=pledge.dollar_value,
                    pledged_at=pledge.pledged_at,
                )
            )
            s.commit()

    def get(self, pool_id: str) -> CommunityPool | None:
        with self._sf() as s:
            row = s.execute(select(community_pools).where(community_pools.c.id == pool_id)).first()
            if not row:
                return None
            pledge_rows = s.execute(select(pledges).where(pledges.c.pool_id == pool_id)).fetchall()
            return self._to_domain(row, pledge_rows)

    def list_all(self) -> list[CommunityPool]:
        with self._sf() as s:
            rows = s.execute(select(community_pools)).fetchall()
            result = []
            for row in rows:
                pledge_rows = s.execute(select(pledges).where(pledges.c.pool_id == row.id)).fetchall()
                result.append(self._to_domain(row, pledge_rows))
            return result

    @staticmethod
    def _to_domain(row, pledge_rows) -> CommunityPool:
        pool_pledges = [
            Pledge(
                id=p.id,
                user_id=p.user_id,
                pool_id=p.pool_id,
                program_code=p.program_code,
                points_pledged=p.points_pledged,
                dollar_value=Decimal(str(p.dollar_value)),
                pledged_at=p.pledged_at,
            )
            for p in pledge_rows
        ]
        return CommunityPool(
            id=row.id,
            name=row.name,
            creator_id=row.creator_id,
            target_charity_name=row.target_charity_name,
            target_charity_state=row.target_charity_state,
            goal_amount=Decimal(str(row.goal_amount)),
            status=PoolStatus(row.status),
            pledges=pool_pledges,
            created_at=row.created_at,
            completed_at=row.completed_at,
        )


class PgForumRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._sf = session_factory

    def save_post(self, post: ForumPost) -> None:
        with self._sf() as s:
            existing = s.execute(select(forum_posts).where(forum_posts.c.id == post.id)).first()
            if existing:
                s.execute(
                    update(forum_posts)
                    .where(forum_posts.c.id == post.id)
                    .values(
                        upvotes=post.upvotes,
                        updated_at=post.updated_at,
                        is_pinned=post.is_pinned,
                    )
                )
            else:
                s.execute(
                    forum_posts.insert().values(
                        id=post.id,
                        author_id=post.author_id,
                        author_name=post.author_name,
                        category=post.category.value,
                        title=post.title,
                        content=post.content,
                        created_at=post.created_at,
                        updated_at=post.updated_at,
                        upvotes=post.upvotes,
                        is_pinned=post.is_pinned,
                    )
                )
            s.commit()

    def save_reply(self, reply: ForumReply) -> None:
        with self._sf() as s:
            s.execute(
                forum_replies.insert().values(
                    id=reply.id,
                    post_id=reply.post_id,
                    author_id=reply.author_id,
                    author_name=reply.author_name,
                    content=reply.content,
                    created_at=reply.created_at,
                    upvotes=reply.upvotes,
                )
            )
            s.commit()

    def get_post(self, post_id: str) -> ForumPost | None:
        with self._sf() as s:
            row = s.execute(select(forum_posts).where(forum_posts.c.id == post_id)).first()
            if not row:
                return None
            reply_rows = s.execute(select(forum_replies).where(forum_replies.c.post_id == post_id)).fetchall()
            return self._to_domain(row, reply_rows)

    def list_posts(self, category: ForumCategory | None, page: int, per_page: int) -> list[ForumPost]:
        with self._sf() as s:
            q = select(forum_posts)
            if category is not None:
                q = q.where(forum_posts.c.category == category.value)
            offset = (page - 1) * per_page
            q = q.offset(offset).limit(per_page)
            rows = s.execute(q).fetchall()
            result = []
            for row in rows:
                reply_rows = s.execute(select(forum_replies).where(forum_replies.c.post_id == row.id)).fetchall()
                result.append(self._to_domain(row, reply_rows))
            return result

    def search(self, query: str) -> list[ForumPost]:
        with self._sf() as s:
            q_lower = f"%{query.lower()}%"
            rows = s.execute(
                select(forum_posts).where(forum_posts.c.title.ilike(q_lower) | forum_posts.c.content.ilike(q_lower))
            ).fetchall()
            result = []
            for row in rows:
                reply_rows = s.execute(select(forum_replies).where(forum_replies.c.post_id == row.id)).fetchall()
                result.append(self._to_domain(row, reply_rows))
            return result

    def delete_post(self, post_id: str) -> bool:
        with self._sf() as s:
            result = s.execute(delete(forum_posts).where(forum_posts.c.id == post_id))
            s.commit()
            return result.rowcount > 0

    @staticmethod
    def _to_domain(row, reply_rows) -> ForumPost:
        replies = [
            ForumReply(
                id=r.id,
                post_id=r.post_id,
                author_id=r.author_id,
                author_name=r.author_name,
                content=r.content,
                created_at=r.created_at,
                upvotes=r.upvotes,
            )
            for r in reply_rows
        ]
        return ForumPost(
            id=row.id,
            author_id=row.author_id,
            author_name=row.author_name,
            category=ForumCategory(row.category),
            title=row.title,
            content=row.content,
            created_at=row.created_at,
            updated_at=row.updated_at,
            replies=replies,
            upvotes=row.upvotes,
            is_pinned=row.is_pinned,
        )


class PgFounderRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._sf = session_factory

    def save(self, profile: FounderProfile) -> None:
        with self._sf() as s:
            existing = s.execute(select(founder_profiles).where(founder_profiles.c.user_id == profile.user_id)).first()
            if existing:
                s.execute(
                    update(founder_profiles)
                    .where(founder_profiles.c.user_id == profile.user_id)
                    .values(
                        name=profile.name,
                        email=profile.email,
                        status=profile.status.value,
                        company_name=profile.company_name,
                        industry=profile.industry,
                        verification_source=profile.verification_source,
                        bio=profile.bio,
                        travel_interests=profile.travel_interests,
                        is_mentor=profile.is_mentor,
                        mentor_topics=profile.mentor_topics,
                    )
                )
            else:
                s.execute(
                    founder_profiles.insert().values(
                        user_id=profile.user_id,
                        name=profile.name,
                        email=profile.email,
                        status=profile.status.value,
                        joined_at=profile.joined_at,
                        company_name=profile.company_name,
                        industry=profile.industry,
                        verification_source=profile.verification_source,
                        bio=profile.bio,
                        travel_interests=profile.travel_interests,
                        is_mentor=profile.is_mentor,
                        mentor_topics=profile.mentor_topics,
                    )
                )
            s.commit()

    def get(self, user_id: str) -> FounderProfile | None:
        with self._sf() as s:
            row = s.execute(select(founder_profiles).where(founder_profiles.c.user_id == user_id)).first()
            return self._to_domain(row) if row else None

    def list_members(self, status: FounderStatus | None) -> list[FounderProfile]:
        with self._sf() as s:
            q = select(founder_profiles)
            if status is not None:
                q = q.where(founder_profiles.c.status == status.value)
            rows = s.execute(q).fetchall()
            return [self._to_domain(r) for r in rows]

    def search(self, query: str) -> list[FounderProfile]:
        with self._sf() as s:
            q_lower = f"%{query.lower()}%"
            rows = s.execute(
                select(founder_profiles).where(
                    founder_profiles.c.name.ilike(q_lower) | founder_profiles.c.company_name.ilike(q_lower)
                )
            ).fetchall()
            return [self._to_domain(r) for r in rows]

    @staticmethod
    def _to_domain(row) -> FounderProfile:
        return FounderProfile(
            user_id=row.user_id,
            name=row.name,
            email=row.email,
            status=FounderStatus(row.status),
            joined_at=row.joined_at,
            company_name=row.company_name,
            industry=row.industry,
            verification_source=row.verification_source,
            bio=row.bio,
            travel_interests=row.travel_interests or [],
            is_mentor=row.is_mentor,
            mentor_topics=row.mentor_topics or [],
        )


class PgAutoDonateRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._sf = session_factory

    def save(self, rule: AutoDonateRule) -> None:
        with self._sf() as s:
            s.execute(
                auto_donate_rules.insert().values(
                    id=rule.id,
                    user_id=rule.user_id,
                    program_code=rule.program_code,
                    charity_name=rule.charity_name,
                    charity_state=rule.charity_state,
                    days_unused_threshold=rule.days_unused_threshold,
                    is_active=rule.is_active,
                )
            )
            s.commit()

    def get_by_user(self, user_id: str) -> list[AutoDonateRule]:
        with self._sf() as s:
            rows = s.execute(select(auto_donate_rules).where(auto_donate_rules.c.user_id == user_id)).fetchall()
            return [self._to_domain(r) for r in rows]

    def delete(self, rule_id: str) -> None:
        with self._sf() as s:
            s.execute(delete(auto_donate_rules).where(auto_donate_rules.c.id == rule_id))
            s.commit()

    def get_all_active(self) -> list[AutoDonateRule]:
        with self._sf() as s:
            rows = s.execute(select(auto_donate_rules).where(auto_donate_rules.c.is_active.is_(True))).fetchall()
            return [self._to_domain(r) for r in rows]

    @staticmethod
    def _to_domain(row) -> AutoDonateRule:
        return AutoDonateRule(
            id=row.id,
            user_id=row.user_id,
            program_code=row.program_code,
            charity_name=row.charity_name,
            charity_state=row.charity_state,
            days_unused_threshold=row.days_unused_threshold,
            is_active=row.is_active,
        )


class PgCharityAlignmentRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._sf = session_factory

    def save(self, alignment: CharityAlignment) -> None:
        with self._sf() as s:
            existing = s.execute(
                select(charity_alignments).where(charity_alignments.c.user_id == alignment.user_id)
            ).first()
            if existing:
                s.execute(
                    update(charity_alignments)
                    .where(charity_alignments.c.user_id == alignment.user_id)
                    .values(
                        charity_name=alignment.charity_name,
                        charity_state=alignment.charity_state,
                        subscription_tier=alignment.subscription_tier.value,
                        monthly_contribution=alignment.monthly_contribution,
                        annual_contribution=alignment.annual_contribution,
                    )
                )
            else:
                s.execute(
                    charity_alignments.insert().values(
                        user_id=alignment.user_id,
                        charity_name=alignment.charity_name,
                        charity_state=alignment.charity_state,
                        subscription_tier=alignment.subscription_tier.value,
                        monthly_contribution=alignment.monthly_contribution,
                        annual_contribution=alignment.annual_contribution,
                    )
                )
            s.commit()

    def get(self, user_id: str) -> CharityAlignment | None:
        with self._sf() as s:
            row = s.execute(select(charity_alignments).where(charity_alignments.c.user_id == user_id)).first()
            if not row:
                return None
            return CharityAlignment(
                user_id=row.user_id,
                charity_name=row.charity_name,
                charity_state=row.charity_state,
                subscription_tier=SubscriptionTier(row.subscription_tier),
                monthly_contribution=Decimal(str(row.monthly_contribution)),
                annual_contribution=Decimal(str(row.annual_contribution)),
            )
