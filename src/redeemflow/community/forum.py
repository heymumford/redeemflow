"""Community forum domain — posts, replies, search.

Beck: The simplest thing that could work.
Fowler: Mutable aggregate root (ForumPost) with frozen value objects (ForumReply).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class ForumCategory(str, Enum):
    STRATEGIES = "strategies"
    DEALS = "deals"
    TRAVEL_COMPANIONS = "travel_companions"
    LOCAL_RECOMMENDATIONS = "local_recommendations"
    TRIP_REPORTS = "trip_reports"
    GENERAL = "general"


@dataclass(frozen=True)
class ForumReply:
    id: str
    post_id: str
    author_id: str
    author_name: str
    content: str
    created_at: str
    upvotes: int = 0


@dataclass
class ForumPost:
    """Mutable aggregate root — state holder for forum post lifecycle."""

    id: str
    author_id: str
    author_name: str
    category: ForumCategory
    title: str
    content: str
    created_at: str
    updated_at: str | None = None
    replies: list[ForumReply] = field(default_factory=list)
    upvotes: int = 0
    is_pinned: bool = False

    def add_reply(self, reply: ForumReply) -> None:
        self.replies.append(reply)

    def upvote(self) -> None:
        self.upvotes += 1

    def reply_count(self) -> int:
        return len(self.replies)


class ForumService:
    """Orchestrates forum lifecycle — create, reply, search, delete."""

    def __init__(self, repository: object | None = None) -> None:
        self._repository = repository
        self._posts: dict[str, ForumPost] = {}

    def create_post(
        self,
        author_id: str,
        author_name: str,
        category: ForumCategory,
        title: str,
        content: str,
    ) -> ForumPost:
        post_id = f"post-{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        post = ForumPost(
            id=post_id,
            author_id=author_id,
            author_name=author_name,
            category=category,
            title=title,
            content=content,
            created_at=now,
        )
        self._posts[post_id] = post
        if self._repository:
            self._repository.save_post(post)
        return post

    def get_post(self, post_id: str) -> ForumPost | None:
        return self._posts.get(post_id)

    def reply_to_post(
        self,
        post_id: str,
        author_id: str,
        author_name: str,
        content: str,
    ) -> ForumReply:
        post = self._posts.get(post_id)
        if post is None:
            raise ValueError(f"Post not found: {post_id}")

        reply_id = f"reply-{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        reply = ForumReply(
            id=reply_id,
            post_id=post_id,
            author_id=author_id,
            author_name=author_name,
            content=content,
            created_at=now,
        )
        post.add_reply(reply)
        if self._repository:
            self._repository.save_reply(reply)
        return reply

    def list_posts(
        self,
        category: ForumCategory | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> list[ForumPost]:
        posts = list(self._posts.values())
        if category is not None:
            posts = [p for p in posts if p.category == category]
        start = (page - 1) * per_page
        end = start + per_page
        return posts[start:end]

    def upvote_post(self, post_id: str) -> ForumPost:
        post = self._posts.get(post_id)
        if post is None:
            raise ValueError(f"Post not found: {post_id}")
        post.upvote()
        if self._repository:
            self._repository.save_post(post)
        return post

    def search_posts(self, query: str) -> list[ForumPost]:
        if not query:
            return []
        q = query.lower()
        return [p for p in self._posts.values() if q in p.title.lower() or q in p.content.lower()]

    def delete_post(self, post_id: str, user_id: str) -> bool:
        post = self._posts.get(post_id)
        if post is None:
            return False
        if post.author_id != user_id:
            return False
        del self._posts[post_id]
        return True
