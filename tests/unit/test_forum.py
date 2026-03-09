"""Unit tests for community forum domain.

TDD: These tests define the contract for ForumService, ForumPost, ForumReply.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from redeemflow.community.forum import ForumCategory, ForumPost, ForumReply, ForumService


class TestForumCategory:
    def test_strategies_value(self):
        assert ForumCategory.STRATEGIES == "strategies"

    def test_deals_value(self):
        assert ForumCategory.DEALS == "deals"

    def test_travel_companions_value(self):
        assert ForumCategory.TRAVEL_COMPANIONS == "travel_companions"

    def test_local_recommendations_value(self):
        assert ForumCategory.LOCAL_RECOMMENDATIONS == "local_recommendations"

    def test_trip_reports_value(self):
        assert ForumCategory.TRIP_REPORTS == "trip_reports"

    def test_general_value(self):
        assert ForumCategory.GENERAL == "general"

    def test_all_categories_count(self):
        assert len(ForumCategory) == 6


class TestForumReply:
    def test_creation(self):
        reply = ForumReply(
            id="reply-1",
            post_id="post-1",
            author_id="auth0|eric",
            author_name="Eric",
            content="Great post!",
            created_at="2026-01-01T00:00:00+00:00",
            upvotes=0,
        )
        assert reply.id == "reply-1"
        assert reply.post_id == "post-1"
        assert reply.author_id == "auth0|eric"
        assert reply.author_name == "Eric"
        assert reply.content == "Great post!"
        assert reply.upvotes == 0

    def test_frozen(self):
        reply = ForumReply(
            id="reply-1",
            post_id="post-1",
            author_id="auth0|eric",
            author_name="Eric",
            content="Great post!",
            created_at="2026-01-01T00:00:00+00:00",
            upvotes=0,
        )
        with pytest.raises(FrozenInstanceError):
            reply.content = "changed"


class TestForumPost:
    def test_creation(self):
        post = ForumPost(
            id="post-1",
            author_id="auth0|eric",
            author_name="Eric",
            category=ForumCategory.STRATEGIES,
            title="Best Transfer Strategies",
            content="Here are my top picks...",
            created_at="2026-01-01T00:00:00+00:00",
        )
        assert post.id == "post-1"
        assert post.author_id == "auth0|eric"
        assert post.category == ForumCategory.STRATEGIES
        assert post.title == "Best Transfer Strategies"
        assert post.upvotes == 0
        assert post.is_pinned is False
        assert post.replies == []
        assert post.updated_at is None

    def test_add_reply(self):
        post = ForumPost(
            id="post-1",
            author_id="auth0|eric",
            author_name="Eric",
            category=ForumCategory.GENERAL,
            title="Hello",
            content="World",
            created_at="2026-01-01T00:00:00+00:00",
        )
        reply = ForumReply(
            id="reply-1",
            post_id="post-1",
            author_id="auth0|steve",
            author_name="Steve",
            content="Nice!",
            created_at="2026-01-01T01:00:00+00:00",
            upvotes=0,
        )
        post.add_reply(reply)
        assert len(post.replies) == 1
        assert post.replies[0].id == "reply-1"

    def test_upvote(self):
        post = ForumPost(
            id="post-1",
            author_id="auth0|eric",
            author_name="Eric",
            category=ForumCategory.GENERAL,
            title="Hello",
            content="World",
            created_at="2026-01-01T00:00:00+00:00",
        )
        post.upvote()
        assert post.upvotes == 1
        post.upvote()
        assert post.upvotes == 2

    def test_reply_count(self):
        post = ForumPost(
            id="post-1",
            author_id="auth0|eric",
            author_name="Eric",
            category=ForumCategory.GENERAL,
            title="Hello",
            content="World",
            created_at="2026-01-01T00:00:00+00:00",
        )
        assert post.reply_count() == 0
        reply = ForumReply(
            id="reply-1",
            post_id="post-1",
            author_id="auth0|steve",
            author_name="Steve",
            content="Nice!",
            created_at="2026-01-01T01:00:00+00:00",
            upvotes=0,
        )
        post.add_reply(reply)
        assert post.reply_count() == 1


class TestForumService:
    def setup_method(self):
        self.service = ForumService()

    def test_create_post(self):
        post = self.service.create_post(
            author_id="auth0|eric",
            author_name="Eric",
            category=ForumCategory.STRATEGIES,
            title="Transfer Tips",
            content="Always check CPP before transferring.",
        )
        assert post.id.startswith("post-")
        assert post.author_id == "auth0|eric"
        assert post.author_name == "Eric"
        assert post.category == ForumCategory.STRATEGIES
        assert post.title == "Transfer Tips"
        assert post.content == "Always check CPP before transferring."
        assert post.created_at  # non-empty

    def test_get_post(self):
        post = self.service.create_post(
            author_id="auth0|eric",
            author_name="Eric",
            category=ForumCategory.GENERAL,
            title="Hello",
            content="World",
        )
        found = self.service.get_post(post.id)
        assert found is not None
        assert found.id == post.id

    def test_get_post_not_found(self):
        assert self.service.get_post("nonexistent") is None

    def test_reply_to_post(self):
        post = self.service.create_post(
            author_id="auth0|eric",
            author_name="Eric",
            category=ForumCategory.GENERAL,
            title="Hello",
            content="World",
        )
        reply = self.service.reply_to_post(
            post_id=post.id,
            author_id="auth0|steve",
            author_name="Steve",
            content="Great post!",
        )
        assert reply.id.startswith("reply-")
        assert reply.post_id == post.id
        assert reply.author_id == "auth0|steve"
        assert reply.content == "Great post!"

        # Verify reply is added to the post
        refreshed = self.service.get_post(post.id)
        assert refreshed is not None
        assert refreshed.reply_count() == 1

    def test_reply_to_nonexistent_post_raises(self):
        with pytest.raises(ValueError, match="Post not found"):
            self.service.reply_to_post(
                post_id="nonexistent",
                author_id="auth0|steve",
                author_name="Steve",
                content="Great post!",
            )

    def test_list_posts_all(self):
        self.service.create_post("auth0|eric", "Eric", ForumCategory.STRATEGIES, "Post 1", "Content 1")
        self.service.create_post("auth0|steve", "Steve", ForumCategory.DEALS, "Post 2", "Content 2")
        posts = self.service.list_posts()
        assert len(posts) == 2

    def test_list_posts_with_category_filter(self):
        self.service.create_post("auth0|eric", "Eric", ForumCategory.STRATEGIES, "Post 1", "Content 1")
        self.service.create_post("auth0|steve", "Steve", ForumCategory.DEALS, "Post 2", "Content 2")
        self.service.create_post("auth0|eric", "Eric", ForumCategory.STRATEGIES, "Post 3", "Content 3")
        posts = self.service.list_posts(category=ForumCategory.STRATEGIES)
        assert len(posts) == 2
        assert all(p.category == ForumCategory.STRATEGIES for p in posts)

    def test_list_posts_pagination(self):
        for i in range(25):
            self.service.create_post("auth0|eric", "Eric", ForumCategory.GENERAL, f"Post {i}", f"Content {i}")
        page1 = self.service.list_posts(page=1, per_page=10)
        assert len(page1) == 10
        page2 = self.service.list_posts(page=2, per_page=10)
        assert len(page2) == 10
        page3 = self.service.list_posts(page=3, per_page=10)
        assert len(page3) == 5

    def test_upvote_post(self):
        post = self.service.create_post("auth0|eric", "Eric", ForumCategory.GENERAL, "Hello", "World")
        updated = self.service.upvote_post(post.id)
        assert updated.upvotes == 1
        updated = self.service.upvote_post(post.id)
        assert updated.upvotes == 2

    def test_upvote_nonexistent_post_raises(self):
        with pytest.raises(ValueError, match="Post not found"):
            self.service.upvote_post("nonexistent")

    def test_search_posts_matches_title(self):
        self.service.create_post("auth0|eric", "Eric", ForumCategory.STRATEGIES, "Transfer Tips", "Some content")
        self.service.create_post("auth0|steve", "Steve", ForumCategory.DEALS, "Best Deals", "Other content")
        results = self.service.search_posts("Transfer")
        assert len(results) == 1
        assert results[0].title == "Transfer Tips"

    def test_search_posts_matches_content(self):
        self.service.create_post("auth0|eric", "Eric", ForumCategory.GENERAL, "Title A", "Amex points are great")
        self.service.create_post("auth0|steve", "Steve", ForumCategory.GENERAL, "Title B", "Chase is better")
        results = self.service.search_posts("Amex")
        assert len(results) == 1
        assert results[0].content == "Amex points are great"

    def test_search_posts_case_insensitive(self):
        self.service.create_post("auth0|eric", "Eric", ForumCategory.GENERAL, "Amex Tips", "Content")
        results = self.service.search_posts("amex")
        assert len(results) == 1

    def test_delete_post_by_author(self):
        post = self.service.create_post("auth0|eric", "Eric", ForumCategory.GENERAL, "Hello", "World")
        result = self.service.delete_post(post.id, "auth0|eric")
        assert result is True
        assert self.service.get_post(post.id) is None

    def test_delete_post_by_non_author_fails(self):
        post = self.service.create_post("auth0|eric", "Eric", ForumCategory.GENERAL, "Hello", "World")
        result = self.service.delete_post(post.id, "auth0|steve")
        assert result is False
        assert self.service.get_post(post.id) is not None

    def test_delete_nonexistent_post(self):
        result = self.service.delete_post("nonexistent", "auth0|eric")
        assert result is False
