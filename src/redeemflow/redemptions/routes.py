"""Redemptions API — car rental analysis, retail value comparison."""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter
from pydantic import BaseModel

from redeemflow.redemptions.car_rental import (
    analyze_car_rental,
    best_car_rental,
    find_car_rentals,
)
from redeemflow.redemptions.retail import (
    analyze_retail_redemption,
    find_retail_redemptions,
    worst_retail_redemption,
)

router = APIRouter()


class CarRentalRequest(BaseModel):
    program: str
    days: int = 3
    alternative_cpp: float = 1.5


@router.get("/api/car-rentals/{program}")
def get_car_rentals(program: str):
    """List car rental redemptions for a program."""
    rentals = find_car_rentals(program)
    return {
        "program": program,
        "count": len(rentals),
        "rentals": [
            {
                "provider": r.provider.value,
                "rental_class": r.rental_class.value,
                "points_per_day": r.points_per_day,
                "cash_equivalent_per_day": str(r.cash_equivalent_per_day),
                "cpp": str(r.cpp),
            }
            for r in rentals
        ],
    }


@router.post("/api/car-rentals/analyze")
def analyze_car(req: CarRentalRequest):
    """Analyze car rental redemption value vs alternatives."""
    rental = best_car_rental(req.program)
    if rental is None:
        return {"error": f"No car rental redemptions for program: {req.program}"}
    analysis = analyze_car_rental(rental, req.days, Decimal(str(req.alternative_cpp)))
    return {
        "provider": analysis.redemption.provider.value,
        "rental_class": analysis.redemption.rental_class.value,
        "days": analysis.days,
        "total_points": analysis.total_points,
        "total_cash_value": str(analysis.total_cash_value),
        "effective_cpp": str(analysis.effective_cpp),
        "alternative_cpp": str(analysis.alternative_cpp),
        "value_ratio": str(analysis.value_ratio),
        "recommendation": analysis.recommendation,
        "rationale": analysis.rationale,
    }


@router.get("/api/retail-redemptions/{program}")
def get_retail_redemptions(program: str):
    """List retail redemption options for a program."""
    redemptions = find_retail_redemptions(program)
    return {
        "program": program,
        "count": len(redemptions),
        "redemptions": [
            {
                "retail_type": r.retail_type.value,
                "description": r.description,
                "cpp": str(r.cpp),
                "value_rating": r.value_rating,
                "min_points": r.min_points,
            }
            for r in redemptions
        ],
    }


class RetailAnalysisRequest(BaseModel):
    program: str
    points: int = 50000
    best_travel_cpp: float = 1.5


@router.post("/api/retail-redemptions/analyze")
def analyze_retail(req: RetailAnalysisRequest):
    """Analyze retail redemption value destruction."""
    worst = worst_retail_redemption(req.program)
    if worst is None:
        return {"error": f"No retail redemptions for program: {req.program}"}
    analysis = analyze_retail_redemption(worst, req.points, Decimal(str(req.best_travel_cpp)))
    return {
        "retail_type": analysis.redemption.retail_type.value,
        "description": analysis.redemption.description,
        "points": analysis.points,
        "retail_value": str(analysis.retail_value),
        "travel_value": str(analysis.travel_value),
        "value_destroyed": str(analysis.value_destroyed),
        "destruction_pct": str(analysis.destruction_pct),
        "recommendation": analysis.recommendation,
        "rationale": analysis.rationale,
    }
