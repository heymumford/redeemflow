"""Valuations API — free-tier calculator endpoints.

Beck: No auth required — these are free for everyone.
Fowler: Thin routes that delegate to domain objects.
"""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from redeemflow.optimization.graph import TransferGraph
from redeemflow.optimization.seed_data import ALL_PARTNERS, REDEMPTION_OPTIONS
from redeemflow.valuations.seed_data import CREDIT_CARDS, PROGRAM_VALUATIONS

router = APIRouter()


def _build_graph() -> TransferGraph:
    graph = TransferGraph()
    for p in ALL_PARTNERS:
        graph.add_partner(p)
    for r in REDEMPTION_OPTIONS:
        graph.add_redemption(r)
    return graph


_GRAPH = _build_graph()


# --- Request/Response Models ---


class CalculateRequest(BaseModel):
    program: str
    points: int = Field(ge=0)


class CardRecommendRequest(BaseModel):
    category: str
    monthly_spend: float = Field(gt=0)


class BalanceItem(BaseModel):
    program: str
    points: int = Field(ge=0)


class SavingsRequest(BaseModel):
    balances: list[BalanceItem]


class FeeAnalysisRequest(BaseModel):
    cards: list[str]
    annual_spend: dict[str, float]


# --- Endpoints ---


@router.post("/api/calculate")
def calculate(req: CalculateRequest):
    val = PROGRAM_VALUATIONS.get(req.program)
    if val is None:
        raise HTTPException(status_code=404, detail=f"Unknown program: {req.program}")

    low, high = val.dollar_value_range(req.points)
    return {
        "program": req.program,
        "program_name": val.program_name,
        "points": req.points,
        "min_value": str(low),
        "max_value": str(high),
        "median_value": str(val.dollar_value(req.points)),
        "cash_back_value": str(val.cash_back_value(req.points)),
        "opportunity_cost": str(val.opportunity_cost(req.points)),
        "valuations": {src.value: str(cpp) for src, cpp in val.valuations.items()},
    }


@router.get("/api/transfers/{program}")
def get_transfers(program: str):
    if program not in _GRAPH.programs:
        raise HTTPException(status_code=404, detail=f"Unknown program: {program}")

    partners = _GRAPH.get_partners_from(program)
    return {
        "program": program,
        "partners": [
            {
                "target_program": p.target_program,
                "transfer_ratio": p.transfer_ratio,
                "effective_ratio": p.effective_ratio,
                "transfer_bonus": p.transfer_bonus,
                "min_transfer": p.min_transfer,
                "is_instant": p.is_instant,
            }
            for p in partners
        ],
    }


@router.get("/api/programs")
def list_programs():
    programs = []
    for code, val in sorted(PROGRAM_VALUATIONS.items()):
        programs.append(
            {
                "code": val.program_code,
                "name": val.program_name,
                "median_cpp": str(val.median_cpp),
                "min_cpp": str(val.min_cpp),
                "max_cpp": str(val.max_cpp),
                "source_count": len(val.valuations),
            }
        )
    return {"programs": programs}


@router.post("/api/recommend-card")
def recommend_card(req: CardRecommendRequest):
    monthly = Decimal(str(req.monthly_spend))
    annual = monthly * 12
    recommendations = []

    for card_id, card in CREDIT_CARDS.items():
        rate = card.earn_rates.get(req.category, card.earn_rates.get("other", Decimal("1.0")))
        monthly_points = int(monthly * rate)
        annual_points = int(annual * rate)

        val = PROGRAM_VALUATIONS.get(card.currency)
        cpp = val.median_cpp if val else Decimal("1.0")
        annual_value = (Decimal(annual_points) * cpp / Decimal(100)).quantize(Decimal("0.01"))

        recommendations.append(
            {
                "card_id": card_id,
                "card_name": card.name,
                "issuer": card.issuer,
                "earn_rate": str(rate),
                "monthly_points": monthly_points,
                "annual_points": annual_points,
                "annual_value": str(annual_value),
                "currency": card.currency,
                "annual_fee": str(card.annual_fee),
            }
        )

    recommendations.sort(key=lambda r: float(r["annual_value"]), reverse=True)
    return {"category": req.category, "monthly_spend": req.monthly_spend, "recommendations": recommendations}


@router.post("/api/savings")
def savings_analysis(req: SavingsRequest):
    programs = []
    total_travel = Decimal("0")
    total_cash = Decimal("0")

    for item in req.balances:
        val = PROGRAM_VALUATIONS.get(item.program)
        if val is None:
            continue
        travel = val.dollar_value(item.points)
        cash = val.cash_back_value(item.points)
        opp = val.opportunity_cost(item.points)
        total_travel += travel
        total_cash += cash
        programs.append(
            {
                "program": item.program,
                "program_name": val.program_name,
                "points": item.points,
                "travel_value": str(travel),
                "cash_back_value": str(cash),
                "opportunity_cost": str(opp),
            }
        )

    return {
        "total_travel_value": str(total_travel),
        "total_cash_back_value": str(total_cash),
        "total_opportunity_cost": str(total_travel - total_cash),
        "programs": programs,
    }


@router.post("/api/fee-analysis")
def fee_analysis(req: FeeAnalysisRequest):
    cards_result = []
    spend = {k: Decimal(str(v)) for k, v in req.annual_spend.items()}

    for card_id in req.cards:
        card = CREDIT_CARDS.get(card_id)
        if card is None:
            continue

        val = PROGRAM_VALUATIONS.get(card.currency)
        cpp = val.median_cpp if val else Decimal("1.0")
        result = card.annual_value(spend, cpp)

        cards_result.append(
            {
                "card_id": card_id,
                "card_name": card.name,
                "annual_fee": str(card.annual_fee),
                "credits_value": str(sum(card.credits.values())),
                "net_annual_fee": str(card.net_annual_fee),
                "points_earned": result.total_points,
                "points_value": str(result.points_value),
                "net_value": str(result.net_value),
            }
        )

    return {"cards": cards_result}
