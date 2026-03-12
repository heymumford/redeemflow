"""Search API — award availability, safety scores, conference planner.

Award search and conference planning endpoints require Premium+ auth.
Safety endpoints are public (no auth required).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from redeemflow.identity.auth import get_current_user
from redeemflow.identity.models import User
from redeemflow.optimization.graph import TransferGraph
from redeemflow.optimization.seed_data import ALL_PARTNERS, REDEMPTION_OPTIONS
from redeemflow.portfolio.awardwallet import FakeAwardWalletAdapter
from redeemflow.search.award_search import AwardSearchProvider, FakeAwardSearchProvider
from redeemflow.search.conference_planner import WOMEN_CONFERENCES, ConferencePlanner
from redeemflow.search.filters import SearchFilters, SortDirection, SortField, apply_filters, search_summary
from redeemflow.search.safety_scores import FakeSafetyDataProvider
from redeemflow.search.saved_searches import SearchCriteria, get_saved_search_store
from redeemflow.search.seasonal_pricing import seasonal_advisory
from redeemflow.search.sweet_spots import SweetSpotCategory, ValueRating, find_sweet_spots
from redeemflow.search.trip_comparison import RedemptionOption, compare_options, rank_options
from redeemflow.search.trip_planner import build_trip_from_segments, get_trip, get_trips, next_trip_id, save_trip
from redeemflow.search.trip_sharing import SharePermission, get_trip_share_store
from redeemflow.valuations.seed_data import PROGRAM_VALUATIONS

router = APIRouter()

_SAFETY_PROVIDER = FakeSafetyDataProvider()
_FETCHER = FakeAwardWalletAdapter()


def _get_search_provider(request: Request) -> AwardSearchProvider:
    """Get award search provider from app state, fallback to fake."""
    provider = getattr(request.app.state, "award_search_provider", None)
    if provider is not None:
        return provider
    return FakeAwardSearchProvider()


def _build_graph() -> TransferGraph:
    graph = TransferGraph()
    for p in ALL_PARTNERS:
        graph.add_partner(p)
    for r in REDEMPTION_OPTIONS:
        graph.add_redemption(r)
    return graph


_GRAPH = _build_graph()


class AwardSearchRequest(BaseModel):
    origin: str
    destination: str
    date: str
    cabin: str


class FilteredSearchRequest(BaseModel):
    origin: str
    destination: str
    date: str
    cabins: list[str] = []
    programs: list[str] = []
    max_points: int | None = None
    min_points: int | None = None
    direct_only: bool = False
    min_seats: int | None = None
    min_cpp: float | None = None
    max_cpp: float | None = None
    sort_by: str = "points"
    sort_direction: str = "asc"
    limit: int = 50


class ConferencePlanRequest(BaseModel):
    conference_name: str
    origin_city: str


@router.post("/api/award-search")
def award_search(
    req: AwardSearchRequest,
    user: User = Depends(get_current_user),
    provider: AwardSearchProvider = Depends(_get_search_provider),
):
    results = provider.search(
        origin=req.origin,
        destination=req.destination,
        date=req.date,
        cabin=req.cabin,
    )
    return {
        "results": [
            {
                "program": r.program,
                "origin": r.origin,
                "destination": r.destination,
                "date": r.date,
                "cabin": r.cabin,
                "points_required": r.points_required,
                "cash_value": str(r.cash_value),
                "source": r.source,
                "direct": r.direct,
                "available_seats": r.available_seats,
            }
            for r in results
        ]
    }


@router.post("/api/award-search/filtered")
def filtered_award_search(
    req: FilteredSearchRequest,
    user: User = Depends(get_current_user),
    provider: AwardSearchProvider = Depends(_get_search_provider),
):
    """Search with multi-dimension filtering, sorting, and value analysis."""
    # Search across requested cabins (or all if none specified)
    cabins_to_search = req.cabins if req.cabins else ["economy", "premium_economy", "business", "first"]
    all_results = []
    for cabin in cabins_to_search:
        results = provider.search(
            origin=req.origin,
            destination=req.destination,
            date=req.date,
            cabin=cabin,
        )
        all_results.extend(results)

    # Build filters
    from decimal import Decimal

    filters = SearchFilters(
        cabins=req.cabins,
        programs=req.programs,
        max_points=req.max_points,
        min_points=req.min_points,
        direct_only=req.direct_only,
        min_seats=req.min_seats,
        min_cpp=Decimal(str(req.min_cpp)) if req.min_cpp is not None else None,
        max_cpp=Decimal(str(req.max_cpp)) if req.max_cpp is not None else None,
        sort_by=SortField(req.sort_by) if req.sort_by in [f.value for f in SortField] else SortField.POINTS,
        sort_direction=(
            SortDirection(req.sort_direction)
            if req.sort_direction in [d.value for d in SortDirection]
            else SortDirection.ASC
        ),
        limit=req.limit,
    )

    filtered = apply_filters(all_results, filters)
    summary = search_summary(filtered)

    return {
        "results": [
            {
                "program": f.result.program,
                "origin": f.result.origin,
                "destination": f.result.destination,
                "date": f.result.date,
                "cabin": f.result.cabin,
                "points_required": f.result.points_required,
                "cash_value": str(f.result.cash_value),
                "direct": f.result.direct,
                "available_seats": f.result.available_seats,
                "cpp": str(f.cpp),
                "value_rating": f.value_rating,
            }
            for f in filtered
        ],
        "summary": summary,
    }


@router.get("/api/safety/{city}")
def destination_safety(city: str):
    """Get safety information for a destination city."""
    # Try common country mappings for convenience
    dest = _SAFETY_PROVIDER.get_destination_safety(city, "")
    # If no data with empty country, try known cities
    if not dest.neighborhoods:
        for country in ["Japan", "UK", "France", "US", "Thailand", "Singapore", "UAE", "Portugal"]:
            candidate = _SAFETY_PROVIDER.get_destination_safety(city, country)
            if candidate.neighborhoods:
                dest = candidate
                break

    return {
        "city": dest.city,
        "country": dest.country,
        "overall_rating": dest.overall_rating.value,
        "neighborhoods": [
            {
                "name": n.name,
                "rating": n.rating.value,
                "walkability": n.walkability,
                "women_traveler_notes": n.women_traveler_notes,
            }
            for n in dest.neighborhoods
        ],
        "women_travel_advisory": dest.women_travel_advisory,
        "emergency_number": dest.emergency_number,
        "recommended_hotels": [
            {
                "hotel_name": h.hotel_name,
                "overall_rating": h.overall_rating.value,
                "walkability_score": h.walkability_score,
                "women_recommend": h.women_recommend,
                "women_recommend_count": h.women_recommend_count,
                "lighting_score": h.lighting_score,
                "transit_access_score": h.transit_access_score,
                "notes": h.notes,
            }
            for h in dest.recommended_hotels
        ],
    }


@router.get("/api/safety/hotel/{hotel_name}")
def hotel_safety(hotel_name: str, city: str = ""):
    """Get safety score for a specific hotel."""
    score = _SAFETY_PROVIDER.get_hotel_safety(hotel_name, city)
    if score is None:
        return JSONResponse(status_code=404, content={"detail": "Hotel not found", "hotel_name": hotel_name})
    return {
        "hotel_name": score.hotel_name,
        "city": score.city,
        "country": score.country,
        "overall_rating": score.overall_rating.value,
        "walkability_score": score.walkability_score,
        "neighborhood_safety": score.neighborhood_safety.value,
        "women_recommend": score.women_recommend,
        "women_recommend_count": score.women_recommend_count,
        "lighting_score": score.lighting_score,
        "transit_access_score": score.transit_access_score,
        "notes": score.notes,
    }


@router.get("/api/conferences")
def list_conferences():
    """List women's conferences with travel planning support."""
    return {
        "conferences": [
            {
                "name": c.name,
                "city": c.city,
                "country": c.country,
                "start_date": c.start_date,
                "end_date": c.end_date,
                "category": c.category,
                "typical_attendees": c.typical_attendees,
                "website": c.website,
            }
            for c in WOMEN_CONFERENCES
        ]
    }


@router.post("/api/conference-plan")
def conference_plan(req: ConferencePlanRequest, user: User = Depends(get_current_user)):
    """Plan travel to a conference using points optimization."""
    # Find the conference by name
    conference = None
    for c in WOMEN_CONFERENCES:
        if c.name.lower() == req.conference_name.lower():
            conference = c
            break

    if conference is None:
        return JSONResponse(status_code=404, content={"detail": f"Conference not found: {req.conference_name}"})

    balances = _FETCHER.fetch_balances(user.id)
    planner = ConferencePlanner(
        graph=_GRAPH,
        valuations=PROGRAM_VALUATIONS,
        safety_provider=_SAFETY_PROVIDER,
    )
    plan = planner.plan(conference, origin_city=req.origin_city, balances=balances)
    return {
        "conference": {
            "name": plan.conference.name,
            "city": plan.conference.city,
            "start_date": plan.conference.start_date,
            "end_date": plan.conference.end_date,
        },
        "origin_city": plan.origin_city,
        "recommended_flights": plan.recommended_flights,
        "recommended_hotels": plan.recommended_hotels,
        "points_options": plan.points_options,
        "estimated_savings": str(plan.estimated_savings),
        "safety_info": {
            "overall_rating": plan.safety_info.overall_rating.value,
            "women_travel_advisory": plan.safety_info.women_travel_advisory,
            "emergency_number": plan.safety_info.emergency_number,
        }
        if plan.safety_info
        else None,
    }


@router.get("/api/sweet-spots")
def list_sweet_spots(
    category: str | None = None,
    program: str | None = None,
    min_rating: str = "fair",
):
    """Find high-value redemption sweet spots."""
    cat = None
    if category:
        try:
            cat = SweetSpotCategory(category)
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={"detail": f"Invalid category: {category}", "valid": [c.value for c in SweetSpotCategory]},
            )

    try:
        rating = ValueRating(min_rating)
    except ValueError:
        return JSONResponse(
            status_code=400,
            content={"detail": f"Invalid rating: {min_rating}", "valid": [r.value for r in ValueRating]},
        )

    spots = find_sweet_spots(category=cat, program=program, min_rating=rating)
    return {
        "count": len(spots),
        "sweet_spots": [
            {
                "program": s.program,
                "program_name": s.program_name,
                "category": s.category.value,
                "description": s.description,
                "points_required": s.points_required,
                "cash_equivalent": str(s.cash_equivalent),
                "effective_cpp": str(s.effective_cpp),
                "baseline_cpp": str(s.baseline_cpp),
                "value_multiplier": str(s.value_multiplier),
                "rating": s.rating.value,
                "route": s.route,
                "cabin": s.cabin,
                "hotel_category": s.hotel_category,
                "notes": s.notes,
            }
            for s in spots
        ],
    }


class TripCompareOptionInput(BaseModel):
    program_code: str
    program_name: str
    points_required: int
    cash_price: str
    cpp: str
    cabin_class: str = "economy"
    stops: int = 0
    transfer_required: bool = False
    transfer_from: str = ""
    availability: str = "available"


class TripCompareRequest(BaseModel):
    route: str
    options: list[TripCompareOptionInput]


@router.post("/api/trip-compare")
def trip_compare(req: TripCompareRequest, user: User = Depends(get_current_user)):
    """Compare redemption options for the same route side-by-side."""
    from decimal import Decimal

    if not req.options:
        return JSONResponse(status_code=400, content={"detail": "At least one option is required"})

    options = [
        RedemptionOption(
            program_code=o.program_code,
            program_name=o.program_name,
            points_required=o.points_required,
            cash_price=Decimal(o.cash_price),
            cpp=Decimal(o.cpp),
            cabin_class=o.cabin_class,
            route=req.route,
            stops=o.stops,
            transfer_required=o.transfer_required,
            transfer_from=o.transfer_from,
            availability=o.availability,
        )
        for o in req.options
    ]

    result = compare_options(req.route, options)
    ranked = rank_options(options)

    return {
        "route": result.route,
        "best_value": {
            "program_code": result.best_value.program_code,
            "program_name": result.best_value.program_name,
            "cpp": str(result.best_value.cpp),
        },
        "cheapest_points": {
            "program_code": result.cheapest_points.program_code,
            "points_required": result.cheapest_points.points_required,
        },
        "value_spread": str(result.value_spread),
        "options": [
            {
                "program_code": o.program_code,
                "program_name": o.program_name,
                "points_required": o.points_required,
                "cash_price": str(o.cash_price),
                "cpp": str(o.cpp),
                "cabin_class": o.cabin_class,
                "availability": o.availability,
            }
            for o in result.options
        ],
        "rankings": ranked,
    }


@router.get("/api/seasonal/{route}")
def get_seasonal_pricing(route: str, month: int = 1, user: User = Depends(get_current_user)):
    """Get seasonal pricing intelligence for a route."""
    adv = seasonal_advisory(route, month)
    return {
        "route": adv.route,
        "current_season": adv.current_season.value,
        "current_month": adv.current_month,
        "price_index": str(adv.price_index),
        "best_value_months": adv.best_value_months,
        "worst_value_months": adv.worst_value_months,
        "booking_window": {
            "ideal_book_months_ahead": adv.booking_window.ideal_book_months_ahead,
            "urgency": adv.booking_window.urgency.value,
            "reason": adv.booking_window.reason,
            "savings_vs_last_minute_pct": adv.booking_window.savings_vs_last_minute_pct,
        },
        "patterns": [
            {
                "season": p.season.value,
                "months": p.months,
                "avg_points": p.avg_points,
                "avg_cash": str(p.avg_cash),
                "availability_rating": p.availability_rating,
                "demand_level": p.demand_level,
                "notes": p.notes,
            }
            for p in adv.patterns
        ],
    }


class CreateTripRequest(BaseModel):
    name: str
    segments: list[dict] = []


@router.get("/api/trips")
def list_trips(user: User = Depends(get_current_user)):
    """List all trips for the user."""
    trips = get_trips(user.id)
    return {
        "trips": [
            {
                "trip_id": t.trip_id,
                "name": t.name,
                "segment_count": len(t.segments),
                "total_points": sum(s.points_cost for s in t.segments),
            }
            for t in trips
        ],
    }


@router.post("/api/trips")
def create_trip(req: CreateTripRequest, user: User = Depends(get_current_user)):
    """Create a new trip with segments."""
    trip_id = next_trip_id(user.id)
    trip = build_trip_from_segments(trip_id, req.name, req.segments)
    save_trip(user.id, trip)
    summary = trip.summarize()
    return {
        "trip_id": trip_id,
        "name": trip.name,
        "total_segments": summary.total_segments,
        "total_points": summary.total_points,
        "total_cash": str(summary.total_cash),
        "avg_cpp": str(summary.avg_cpp),
        "value_vs_cash": str(summary.value_vs_cash),
        "programs_used": summary.programs_used,
    }


@router.get("/api/trips/{trip_id}")
def get_trip_detail(trip_id: str, user: User = Depends(get_current_user)):
    """Get detailed trip with all segments and metrics."""
    trip = get_trip(user.id, trip_id)
    if trip is None:
        return JSONResponse(status_code=404, content={"detail": "Trip not found"})

    summary = trip.summarize()
    return {
        "trip_id": trip.trip_id,
        "name": trip.name,
        "total_segments": summary.total_segments,
        "total_points": summary.total_points,
        "total_cash": str(summary.total_cash),
        "total_value": str(summary.total_value),
        "avg_cpp": str(summary.avg_cpp),
        "value_vs_cash": str(summary.value_vs_cash),
        "programs_used": summary.programs_used,
        "segments": [
            {
                "segment_id": s.segment_id,
                "segment_type": s.segment_type.value,
                "description": s.description,
                "origin": s.origin,
                "destination": s.destination,
                "date": s.date,
                "points_cost": s.points_cost,
                "cash_cost": str(s.cash_cost),
                "program_code": s.program_code,
                "booking_method": s.booking_method.value,
                "cpp": str(s.cpp),
            }
            for s in summary.segments
        ],
    }


# ---------------------------------------------------------------------------
# Trip sharing endpoints
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Saved searches endpoints
# ---------------------------------------------------------------------------


class SaveSearchRequest(BaseModel):
    name: str
    origin: str
    destination: str
    cabin: str = "economy"
    programs: list[str] = []
    max_points: int | None = None
    direct_only: bool = False
    alert_on_change: bool = False


@router.post("/api/saved-searches")
def save_search(req: SaveSearchRequest, user: User = Depends(get_current_user)):
    """Save search criteria for later replay."""
    store = get_saved_search_store()
    criteria = SearchCriteria(
        origin=req.origin,
        destination=req.destination,
        cabin=req.cabin,
        programs=req.programs,
        max_points=req.max_points,
        direct_only=req.direct_only,
    )
    saved = store.save(user.id, req.name, criteria, alert_on_change=req.alert_on_change)
    return {
        "search_id": saved.search_id,
        "name": saved.name,
        "created_at": saved.created_at,
        "criteria": {
            "origin": saved.criteria.origin,
            "destination": saved.criteria.destination,
            "cabin": saved.criteria.cabin,
        },
    }


@router.get("/api/saved-searches")
def list_saved_searches(user: User = Depends(get_current_user)):
    """List all saved searches for the current user."""
    store = get_saved_search_store()
    searches = store.list_searches(user.id)
    return {
        "searches": [
            {
                "search_id": s.search_id,
                "name": s.name,
                "origin": s.criteria.origin,
                "destination": s.criteria.destination,
                "cabin": s.criteria.cabin,
                "run_count": s.run_count,
                "last_run_at": s.last_run_at,
                "alert_on_change": s.alert_on_change,
            }
            for s in searches
        ],
    }


@router.delete("/api/saved-searches/{search_id}")
def delete_saved_search(search_id: str, user: User = Depends(get_current_user)):
    """Delete a saved search."""
    store = get_saved_search_store()
    deleted = store.delete(search_id, user.id)
    if deleted is None:
        return JSONResponse(status_code=404, content={"detail": "Search not found"})
    return {
        "search": {
            "search_id": deleted.search_id,
            "name": deleted.name,
            "is_active": deleted.is_active,
        },
    }


# ---------------------------------------------------------------------------
# Trip sharing endpoints
# ---------------------------------------------------------------------------


class CreateShareRequest(BaseModel):
    permission: str = "view"


def _serialize_share(share) -> dict:
    return {
        "share_id": share.share_id,
        "trip_id": share.trip_id,
        "permission": share.permission.value,
        "created_at": share.created_at,
        "is_active": share.is_active,
        "view_count": share.view_count,
        "last_viewed_at": share.last_viewed_at,
    }


@router.post("/api/trips/{trip_id}/share")
def share_trip(trip_id: str, req: CreateShareRequest, user: User = Depends(get_current_user)):
    """Create a shareable link for a trip."""
    store = get_trip_share_store()
    try:
        perm = SharePermission(req.permission)
    except ValueError:
        return JSONResponse(status_code=400, content={"detail": f"Invalid permission: {req.permission}"})

    link = store.create_share(trip_id, user.id, perm)
    return {"token": link.token, "share": _serialize_share(link)}


@router.get("/api/shared/{token}")
def view_shared_trip(token: str):
    """View a shared trip (public — no auth required)."""
    store = get_trip_share_store()
    share = store.record_view(token)
    if share is None:
        return JSONResponse(status_code=404, content={"detail": "Share not found or expired"})

    return {
        "trip_id": share.trip_id,
        "permission": share.permission.value,
        "view_count": share.view_count,
    }


@router.get("/api/shares")
def list_shares(user: User = Depends(get_current_user)):
    """List all shares for the current user."""
    store = get_trip_share_store()
    shares = store.list_shares(user.id)
    return {"shares": [_serialize_share(s) for s in shares]}


@router.delete("/api/shares/{share_id}")
def revoke_share(share_id: str, user: User = Depends(get_current_user)):
    """Revoke a share link."""
    store = get_trip_share_store()
    revoked = store.revoke_share(share_id, user.id)
    if revoked is None:
        return JSONResponse(status_code=404, content={"detail": "Share not found"})

    return {"share": _serialize_share(revoked)}
