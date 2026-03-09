"""Community pool API — create, pledge, complete, and browse pools.

Beck: Thin routes that delegate to domain objects.
Fowler: Anti-corruption layer between HTTP and domain.
"""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

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
