"""Charity directory and donation API — browsing, donating, and impact tracking.

Beck: No auth for browsing, auth required for donations.
Fowler: Thin routes that delegate to domain objects.

IRS Disclosure: Point donations are NOT tax-deductible. The IRS treats loyalty
points as rebates, not income. The dollar value is calculated from median CPP.
"""

from __future__ import annotations

from collections import Counter

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from redeemflow.charity.donation_flow import DonationService
from redeemflow.charity.impact import ImpactTracker
from redeemflow.charity.models import CharityCategory, CharityOrganization
from redeemflow.charity.seed_data import CHARITY_NETWORK
from redeemflow.identity.auth import get_current_user
from redeemflow.identity.models import User

router = APIRouter()


def _serialize(org: CharityOrganization) -> dict:
    return {
        "name": org.name,
        "category": org.category.value,
        "state": org.state,
        "chapter_name": org.chapter_name,
        "chapter_url": org.chapter_url,
        "national_url": org.national_url,
        "donation_url": org.donation_url,
        "is_501c3": org.is_501c3,
        "accepts_points_donation": org.accepts_points_donation,
        "ein": org.ein,
        "description": org.description,
    }


def _sort_key(org: CharityOrganization) -> tuple[str, str, str]:
    return (org.state, org.name, org.chapter_name or "")


def _paginate(items: list, page: int, per_page: int) -> tuple[list, int]:
    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page
    return items[start:end], total


@router.get("/api/charities")
def list_charities(
    state: str | None = Query(None, description="Filter by 2-letter state code"),
    category: str | None = Query(None, description="Filter by category"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=200, description="Items per page"),
):
    if state and category:
        try:
            cat = CharityCategory(category.lower())
        except ValueError:
            results: list[CharityOrganization] = []
        else:
            results = CHARITY_NETWORK.by_state_and_category(state, cat)
    elif state:
        results = CHARITY_NETWORK.by_state(state)
    elif category:
        try:
            cat = CharityCategory(category.lower())
        except ValueError:
            results = []
        else:
            results = CHARITY_NETWORK.by_category(cat)
    else:
        results = CHARITY_NETWORK.charities

    results = sorted(results, key=_sort_key)
    page_items, total = _paginate(results, page, per_page)

    return {
        "charities": [_serialize(c) for c in page_items],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.get("/api/charities/states")
def list_states():
    state_counts = Counter(c.state for c in CHARITY_NETWORK.charities)
    states = sorted(
        [{"state": s, "count": n} for s, n in state_counts.items()],
        key=lambda x: x["state"],
    )
    return {"states": states}


@router.get("/api/charities/categories")
def list_categories():
    cat_counts = Counter(c.category.value for c in CHARITY_NETWORK.charities)
    categories = sorted(
        [{"category": cat, "count": n} for cat, n in cat_counts.items()],
        key=lambda x: x["category"],
    )
    return {"categories": categories}


@router.get("/api/charities/search")
def search_charities(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
):
    results = sorted(CHARITY_NETWORK.search(q), key=_sort_key)
    page_items, total = _paginate(results, page, per_page)

    return {
        "charities": [_serialize(c) for c in page_items],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


# --- Donation and Impact Endpoints ---

_TAX_NOTICE = (
    "Point-based donations are NOT tax-deductible. The IRS treats loyalty points "
    "as rebates, not income. The dollar value shown is calculated from the median "
    "cents-per-point valuation and represents the economic value converted, not a "
    "tax-deductible charitable contribution."
)


class DonateRequest(BaseModel):
    program_code: str = Field(..., description="Loyalty program code")
    points: int = Field(..., description="Number of points to donate")
    charity_name: str = Field(..., description="Name of charity organization")
    charity_state: str = Field(..., description="2-letter state code of charity chapter")


def _get_donation_service(request: Request) -> DonationService:
    return request.app.state.donation_service


def _serialize_donation(d) -> dict:
    return {
        "id": d.id,
        "user_id": d.user_id,
        "charity_name": d.charity_name,
        "charity_state": d.charity_state,
        "program_code": d.program_code,
        "points_donated": d.points_donated,
        "dollar_value": str(d.dollar_value),
        "status": d.status.value,
        "created_at": d.created_at,
        "completed_at": d.completed_at,
        "change_api_reference": d.change_api_reference,
    }


@router.post("/api/donate")
def donate(
    body: DonateRequest,
    request: Request,
    user: User = Depends(get_current_user),
):
    service = _get_donation_service(request)
    try:
        donation = service.donate(
            user_id=user.id,
            charity_name=body.charity_name,
            charity_state=body.charity_state,
            program_code=body.program_code,
            points=body.points,
        )
    except ValueError as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})

    return {
        "donation": _serialize_donation(donation),
        "tax_notice": _TAX_NOTICE,
    }


@router.get("/api/donations")
def get_donations(
    request: Request,
    user: User = Depends(get_current_user),
):
    service = _get_donation_service(request)
    donations = service.get_user_donations(user.id)
    return {
        "donations": [_serialize_donation(d) for d in donations],
        "tax_notice": _TAX_NOTICE,
    }


@router.get("/api/impact")
def get_user_impact(
    request: Request,
    user: User = Depends(get_current_user),
):
    service = _get_donation_service(request)
    tracker = ImpactTracker(service.get_all_donations())
    impact = tracker.user_impact(user.id)
    return {
        "user_id": impact.user_id,
        "total_donated": str(impact.total_donated),
        "donation_count": impact.donation_count,
        "charities_supported": impact.charities_supported,
        "states_reached": impact.states_reached,
        "top_charity": impact.top_charity,
    }


@router.get("/api/impact/community")
def get_community_impact(request: Request):
    service = _get_donation_service(request)
    tracker = ImpactTracker(service.get_all_donations())
    community = tracker.community_impact()
    return {
        "total_donated": str(community.total_donated),
        "total_donors": community.total_donors,
        "total_donations": community.total_donations,
        "unique_charities": community.unique_charities,
        "unique_states": community.unique_states,
        "top_charities": [{"name": name, "total_donated": str(amount)} for name, amount in community.top_charities],
    }
