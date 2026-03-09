"""Charity directory API — free-tier endpoints for browsing the partner network.

Beck: No auth required — these are free for everyone.
Fowler: Thin routes that delegate to domain objects.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from redeemflow.charity.models import CharityCategory
from redeemflow.charity.seed_data import CHARITY_NETWORK

router = APIRouter()


def _serialize(org) -> dict:
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
    results = CHARITY_NETWORK.charities

    if state:
        results = [c for c in results if c.state == state]

    if category:
        try:
            cat = CharityCategory(category.lower())
        except ValueError:
            results = []
        else:
            results = [c for c in results if c.category == cat]

    page_items, total = _paginate(results, page, per_page)

    return {
        "charities": [_serialize(c) for c in page_items],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.get("/api/charities/states")
def list_states():
    state_counts: dict[str, int] = {}
    for c in CHARITY_NETWORK.charities:
        state_counts[c.state] = state_counts.get(c.state, 0) + 1

    states = sorted(
        [{"state": s, "count": n} for s, n in state_counts.items()],
        key=lambda x: x["state"],
    )
    return {"states": states}


@router.get("/api/charities/categories")
def list_categories():
    cat_counts: dict[str, int] = {}
    for c in CHARITY_NETWORK.charities:
        cat_counts[c.category.value] = cat_counts.get(c.category.value, 0) + 1

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
    results = CHARITY_NETWORK.search(q)
    page_items, total = _paginate(results, page, per_page)

    return {
        "charities": [_serialize(c) for c in page_items],
        "total": total,
        "page": page,
        "per_page": per_page,
    }
