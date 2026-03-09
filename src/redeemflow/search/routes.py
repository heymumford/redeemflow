"""Search API — award availability search.

Award search endpoint requires Premium+ auth.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from redeemflow.identity.auth import get_current_user
from redeemflow.identity.models import User
from redeemflow.search.award_search import FakeAwardSearchProvider

router = APIRouter()

_SEARCH_PROVIDER = FakeAwardSearchProvider()


class AwardSearchRequest(BaseModel):
    origin: str
    destination: str
    date: str
    cabin: str


@router.post("/api/award-search")
def award_search(req: AwardSearchRequest, user: User = Depends(get_current_user)):
    results = _SEARCH_PROVIDER.search(
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
