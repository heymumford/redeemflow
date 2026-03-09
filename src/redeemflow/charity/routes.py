"""Charity directory API — free-tier endpoints for browsing the partner network.

Beck: No auth required — these are free for everyone.
Fowler: Thin routes that delegate to domain objects.
"""

from __future__ import annotations

from collections import Counter

from fastapi import APIRouter, Query

from redeemflow.charity.models import CharityCategory, CharityOrganization
from redeemflow.charity.seed_data import CHARITY_NETWORK

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
