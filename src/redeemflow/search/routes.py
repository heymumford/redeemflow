"""Search API — award availability, safety scores, conference planner.

Award search and conference planning endpoints require Premium+ auth.
Safety endpoints are public (no auth required).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from redeemflow.identity.auth import get_current_user
from redeemflow.identity.models import User
from redeemflow.optimization.graph import TransferGraph
from redeemflow.optimization.seed_data import ALL_PARTNERS, REDEMPTION_OPTIONS
from redeemflow.portfolio.awardwallet import FakeAwardWalletAdapter
from redeemflow.search.award_search import AwardSearchProvider, FakeAwardSearchProvider
from redeemflow.search.conference_planner import WOMEN_CONFERENCES, ConferencePlanner
from redeemflow.search.safety_scores import FakeSafetyDataProvider
from redeemflow.search.sweet_spots import SweetSpotCategory, ValueRating, find_sweet_spots
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
        return {"error": "Hotel not found", "hotel_name": hotel_name}
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
        return {"error": f"Conference not found: {req.conference_name}"}

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
            return {"error": f"Invalid category: {category}", "valid": [c.value for c in SweetSpotCategory]}

    try:
        rating = ValueRating(min_rating)
    except ValueError:
        return {"error": f"Invalid rating: {min_rating}", "valid": [r.value for r in ValueRating]}

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
