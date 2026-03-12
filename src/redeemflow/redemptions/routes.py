"""Redemptions API — car rental analysis, retail value comparison, exchange platforms."""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from redeemflow.identity.auth import get_current_user
from redeemflow.identity.models import User
from redeemflow.redemptions.car_rental import (
    analyze_car_rental,
    best_car_rental,
    find_car_rentals,
)
from redeemflow.redemptions.exchange import (
    analyze_buy,
    analyze_sell,
    find_exchange_rates,
    find_swap_rates,
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
def get_car_rentals(program: str, user: User = Depends(get_current_user)):
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
def analyze_car(req: CarRentalRequest, user: User = Depends(get_current_user)):
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
def get_retail_redemptions(program: str, user: User = Depends(get_current_user)):
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
def analyze_retail(req: RetailAnalysisRequest, user: User = Depends(get_current_user)):
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


# --- Exchange Platform Endpoints ---


@router.get("/api/exchange-rates/{program}")
def get_exchange_rates(program: str, user: User = Depends(get_current_user)):
    """List buy/sell exchange rates for a program."""
    rates = find_exchange_rates(program)
    return {
        "program": program,
        "count": len(rates),
        "rates": [
            {
                "platform": r.platform,
                "exchange_type": r.exchange_type.value,
                "rate": str(r.rate),
                "effective_rate": str(r.effective_rate),
                "fee_pct": str(r.fee_pct),
                "min_transaction": r.min_transaction,
                "max_transaction": r.max_transaction,
            }
            for r in rates
        ],
    }


class BuyAnalysisRequest(BaseModel):
    program: str
    points: int = 50000
    target_redemption_cpp: float = 1.5


@router.post("/api/exchange/buy-analysis")
def exchange_buy_analysis(req: BuyAnalysisRequest, user: User = Depends(get_current_user)):
    """Analyze whether buying points is worthwhile."""
    analysis = analyze_buy(req.program, req.points, Decimal(str(req.target_redemption_cpp)))
    if analysis is None:
        return {"error": f"No buy rates available for: {req.program}"}
    return {
        "program": analysis.program_code,
        "points": analysis.points,
        "cash_cost": str(analysis.cash_cost_or_value),
        "break_even_cpp": str(analysis.break_even_redemption_cpp),
        "target_redemption_cpp": str(analysis.baseline_cpp),
        "recommendation": analysis.recommendation,
        "rationale": analysis.rationale,
    }


class SellAnalysisRequest(BaseModel):
    program: str
    points: int = 50000


@router.post("/api/exchange/sell-analysis")
def exchange_sell_analysis(req: SellAnalysisRequest, user: User = Depends(get_current_user)):
    """Analyze the value of selling points for cash."""
    analysis = analyze_sell(req.program, req.points)
    if analysis is None:
        return {"error": f"No sell rates available for: {req.program}"}
    return {
        "program": analysis.program_code,
        "points": analysis.points,
        "cash_value": str(analysis.cash_cost_or_value),
        "sell_cpp": str(analysis.effective_cpp_impact),
        "recommendation": analysis.recommendation,
        "rationale": analysis.rationale,
    }


@router.get("/api/exchange/swaps/{program}")
def get_swap_rates(program: str, user: User = Depends(get_current_user)):
    """List available point swap rates from a program."""
    swaps = find_swap_rates(program)
    return {
        "source_program": program,
        "count": len(swaps),
        "swaps": [
            {
                "platform": s.platform,
                "target_program": s.target_program,
                "swap_ratio": str(s.swap_ratio),
                "effective_ratio": str(s.effective_ratio),
                "fee_pct": str(s.fee_pct),
                "min_points": s.min_points,
            }
            for s in swaps
        ],
    }
