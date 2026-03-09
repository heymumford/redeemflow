"""Community API — pools, forum, and Women Founders Travel Network.

Beck: Thin routes that delegate to domain objects.
Fowler: Anti-corruption layer between HTTP and domain.
"""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from redeemflow.community.forum import ForumCategory, ForumPost, ForumReply, ForumService
from redeemflow.community.founders_network import FounderDirectory, FounderProfile
from redeemflow.community.models import CommunityPool, PoolService
from redeemflow.identity.auth import get_current_user
from redeemflow.identity.models import User

router = APIRouter()


class CreatePoolRequest(BaseModel):
    name: str = Field(..., description="Pool display name")
    target_charity_name: str = Field(..., description="Target charity name")
    target_charity_state: str = Field(..., description="Target charity 2-letter state code")
    goal_amount: str = Field(..., description="Dollar goal amount")


class PledgeRequest(BaseModel):
    program_code: str = Field(..., description="Loyalty program code")
    points: int = Field(..., description="Number of points to pledge")


def _get_pool_service(request: Request) -> PoolService:
    return request.app.state.pool_service


def _serialize_pool(pool: CommunityPool) -> dict:
    return {
        "id": pool.id,
        "name": pool.name,
        "creator_id": pool.creator_id,
        "target_charity_name": pool.target_charity_name,
        "target_charity_state": pool.target_charity_state,
        "goal_amount": str(pool.goal_amount),
        "status": pool.status.value,
        "total_pledged": str(pool.total_pledged()),
        "progress_pct": str(pool.progress_pct()),
        "pledge_count": len(pool.pledges),
        "created_at": pool.created_at,
        "completed_at": pool.completed_at,
    }


def _serialize_pledge(pledge) -> dict:
    return {
        "id": pledge.id,
        "user_id": pledge.user_id,
        "pool_id": pledge.pool_id,
        "program_code": pledge.program_code,
        "points_pledged": pledge.points_pledged,
        "dollar_value": str(pledge.dollar_value),
        "pledged_at": pledge.pledged_at,
    }


@router.post("/api/pools")
def create_pool(
    body: CreatePoolRequest,
    request: Request,
    user: User = Depends(get_current_user),
):
    service = _get_pool_service(request)
    try:
        pool = service.create_pool(
            creator_id=user.id,
            name=body.name,
            target_charity_name=body.target_charity_name,
            target_charity_state=body.target_charity_state,
            goal_amount=Decimal(body.goal_amount),
        )
    except ValueError as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})

    return {"pool": _serialize_pool(pool)}


@router.post("/api/pools/{pool_id}/pledge")
def pledge_to_pool(
    pool_id: str,
    body: PledgeRequest,
    request: Request,
    user: User = Depends(get_current_user),
):
    service = _get_pool_service(request)
    try:
        pledge = service.pledge(
            pool_id=pool_id,
            user_id=user.id,
            program_code=body.program_code,
            points=body.points,
        )
    except ValueError as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})

    return {"pledge": _serialize_pledge(pledge)}


@router.get("/api/pools")
def list_pools(request: Request):
    service = _get_pool_service(request)
    pools = service.list_pools()
    return {"pools": [_serialize_pool(p) for p in pools]}


@router.get("/api/pools/{pool_id}")
def get_pool(pool_id: str, request: Request):
    service = _get_pool_service(request)
    pool = service.get_pool(pool_id)
    if pool is None:
        return JSONResponse(status_code=404, content={"detail": f"Pool not found: {pool_id}"})
    return {"pool": _serialize_pool(pool)}


@router.post("/api/pools/{pool_id}/complete")
def complete_pool(
    pool_id: str,
    request: Request,
    user: User = Depends(get_current_user),
):
    service = _get_pool_service(request)
    try:
        pool = service.complete_pool(pool_id)
    except ValueError as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})

    return {"pool": _serialize_pool(pool)}


# ---------------------------------------------------------------------------
# Forum endpoints
# ---------------------------------------------------------------------------


class CreatePostRequest(BaseModel):
    category: str = Field(..., description="Forum category")
    title: str = Field(..., description="Post title")
    content: str = Field(..., description="Post content")


class ReplyRequest(BaseModel):
    content: str = Field(..., description="Reply content")


class FounderApplyRequest(BaseModel):
    company_name: str | None = Field(None, description="Company name")
    verification_source: str | None = Field(None, description="Verification source: NAWBO, WBENC, SBA, SELF")
    bio: str | None = Field(None, description="Short bio")
    travel_interests: list[str] = Field(default_factory=list, description="Travel interests")
    is_mentor: bool = Field(False, description="Available as mentor")
    mentor_topics: list[str] = Field(default_factory=list, description="Mentor topics")


def _get_forum_service(request: Request) -> ForumService:
    return request.app.state.forum_service


def _get_founder_directory(request: Request) -> FounderDirectory:
    return request.app.state.founder_directory


def _serialize_post(post: ForumPost, include_replies: bool = False) -> dict:
    result: dict = {
        "id": post.id,
        "author_id": post.author_id,
        "author_name": post.author_name,
        "category": post.category.value,
        "title": post.title,
        "content": post.content,
        "created_at": post.created_at,
        "updated_at": post.updated_at,
        "upvotes": post.upvotes,
        "is_pinned": post.is_pinned,
        "reply_count": post.reply_count(),
    }
    if include_replies:
        result["replies"] = [_serialize_reply(r) for r in post.replies]
    return result


def _serialize_reply(reply: ForumReply) -> dict:
    return {
        "id": reply.id,
        "post_id": reply.post_id,
        "author_id": reply.author_id,
        "author_name": reply.author_name,
        "content": reply.content,
        "created_at": reply.created_at,
        "upvotes": reply.upvotes,
    }


def _serialize_founder(profile: FounderProfile) -> dict:
    return {
        "user_id": profile.user_id,
        "name": profile.name,
        "email": profile.email,
        "company_name": profile.company_name,
        "industry": profile.industry,
        "verification_source": profile.verification_source,
        "status": profile.status.value,
        "joined_at": profile.joined_at,
        "bio": profile.bio,
        "travel_interests": profile.travel_interests,
        "is_mentor": profile.is_mentor,
        "mentor_topics": profile.mentor_topics,
    }


@router.post("/api/forum/posts")
def create_forum_post(
    body: CreatePostRequest,
    request: Request,
    user: User = Depends(get_current_user),
):
    service = _get_forum_service(request)
    try:
        category = ForumCategory(body.category)
    except ValueError:
        return JSONResponse(status_code=400, content={"detail": f"Invalid category: {body.category}"})

    post = service.create_post(
        author_id=user.id,
        author_name=user.name or "Anonymous",
        category=category,
        title=body.title,
        content=body.content,
    )
    return {"post": _serialize_post(post)}


@router.get("/api/forum/posts")
def list_forum_posts(
    request: Request,
    category: str | None = Query(None, description="Filter by category"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    service = _get_forum_service(request)
    cat = ForumCategory(category) if category else None
    posts = service.list_posts(category=cat, page=page, per_page=per_page)
    return {"posts": [_serialize_post(p) for p in posts]}


@router.get("/api/forum/search")
def search_forum_posts(
    request: Request,
    q: str = Query("", description="Search query"),
):
    service = _get_forum_service(request)
    posts = service.search_posts(q)
    return {"posts": [_serialize_post(p) for p in posts]}


@router.get("/api/forum/posts/{post_id}")
def get_forum_post(post_id: str, request: Request):
    service = _get_forum_service(request)
    post = service.get_post(post_id)
    if post is None:
        return JSONResponse(status_code=404, content={"detail": f"Post not found: {post_id}"})
    return {"post": _serialize_post(post, include_replies=True)}


@router.post("/api/forum/posts/{post_id}/reply")
def reply_to_forum_post(
    post_id: str,
    body: ReplyRequest,
    request: Request,
    user: User = Depends(get_current_user),
):
    service = _get_forum_service(request)
    try:
        reply = service.reply_to_post(
            post_id=post_id,
            author_id=user.id,
            author_name=user.name or "Anonymous",
            content=body.content,
        )
    except ValueError as e:
        return JSONResponse(status_code=404, content={"detail": str(e)})

    return {"reply": _serialize_reply(reply)}


@router.post("/api/forum/posts/{post_id}/upvote")
def upvote_forum_post(
    post_id: str,
    request: Request,
    user: User = Depends(get_current_user),
):
    service = _get_forum_service(request)
    try:
        post = service.upvote_post(post_id)
    except ValueError as e:
        return JSONResponse(status_code=404, content={"detail": str(e)})

    return {"post": _serialize_post(post)}


# ---------------------------------------------------------------------------
# Women Founders Travel Network endpoints
# ---------------------------------------------------------------------------


@router.post("/api/founders/apply")
def apply_for_founders(
    body: FounderApplyRequest,
    request: Request,
    user: User = Depends(get_current_user),
):
    directory = _get_founder_directory(request)
    profile = directory.apply(
        user_id=user.id,
        name=user.name or "Anonymous",
        email=user.email,
        company_name=body.company_name,
        verification_source=body.verification_source,
        bio=body.bio,
        travel_interests=body.travel_interests,
    )
    # Apply mentor fields if provided
    if body.is_mentor:
        profile.is_mentor = body.is_mentor
        profile.mentor_topics = body.mentor_topics
    return {"profile": _serialize_founder(profile)}


@router.get("/api/founders/members")
def list_founders(request: Request):
    directory = _get_founder_directory(request)
    from redeemflow.community.founders_network import FounderStatus

    members = directory.list_members(status=FounderStatus.ACTIVE)
    return {"members": [_serialize_founder(m) for m in members]}


@router.get("/api/founders/members/{user_id:path}")
def get_founder_profile(user_id: str, request: Request):
    directory = _get_founder_directory(request)
    profile = directory.get_profile(user_id)
    if profile is None:
        return JSONResponse(status_code=404, content={"detail": f"Member not found: {user_id}"})
    return {"profile": _serialize_founder(profile)}


@router.post("/api/founders/verify/{user_id:path}")
def verify_founder(
    user_id: str,
    request: Request,
    _user: User = Depends(get_current_user),
):
    directory = _get_founder_directory(request)
    try:
        profile = directory.verify(user_id)
    except ValueError as e:
        return JSONResponse(status_code=404, content={"detail": str(e)})

    return {"profile": _serialize_founder(profile)}


@router.get("/api/founders/companions/{city}")
def find_companions(city: str, request: Request):
    directory = _get_founder_directory(request)
    companions = directory.find_travel_companions(city)
    return {"companions": [_serialize_founder(c) for c in companions]}


@router.get("/api/founders/mentors/{topic}")
def find_mentors(topic: str, request: Request):
    directory = _get_founder_directory(request)
    mentors = directory.find_mentors(topic)
    return {"mentors": [_serialize_founder(m) for m in mentors]}
