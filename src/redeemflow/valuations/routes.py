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
from redeemflow.recommendations.card_recommender import recommend_cards, recommend_combo
from redeemflow.recommendations.strategy_quiz import (
    QuizAnswers,
    RedemptionPreference,
    SpendLevel,
    TravelFrequency,
    classify,
)
from redeemflow.valuations.aggregator import AggregationStrategy, aggregate_cpp, batch_aggregate
from redeemflow.valuations.program_health import assess_all_programs
from redeemflow.valuations.savings import analyze_savings
from redeemflow.valuations.seed_data import CREDIT_CARDS, PROGRAM_VALUATIONS
from redeemflow.valuations.trends import get_trend_tracker, seed_trends

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


class StrategyQuizRequest(BaseModel):
    travel_frequency: str
    preferred_cabin: str = "economy"
    redemption_preference: str = "no_preference"
    monthly_spend: str = "medium"
    flexibility: bool = False
    hotel_priority: str = "midrange"


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
    for _code, val in sorted(PROGRAM_VALUATIONS.items()):
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


@router.post("/api/strategy-quiz")
def strategy_quiz(req: StrategyQuizRequest):
    """Classify user's points strategy and recommend programs/cards."""
    try:
        answers = QuizAnswers(
            travel_frequency=TravelFrequency(req.travel_frequency),
            preferred_cabin=req.preferred_cabin,
            redemption_preference=RedemptionPreference(req.redemption_preference),
            monthly_spend=SpendLevel(req.monthly_spend),
            flexibility=req.flexibility,
            hotel_priority=req.hotel_priority,
        )
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err

    result = classify(answers)
    return {
        "archetype": result.archetype.value,
        "description": result.archetype_description,
        "recommended_programs": result.recommended_programs,
        "recommended_cards": result.recommended_cards,
        "top_strategy": result.top_strategy,
        "secondary_strategy": result.secondary_strategy,
        "score_breakdown": result.score_breakdown,
    }


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


class SpendProfileRequest(BaseModel):
    monthly_spend: dict[str, float]
    max_results: int = Field(default=5, ge=1, le=20)


@router.post("/api/recommend-cards")
def recommend_cards_endpoint(req: SpendProfileRequest):
    """Recommend cards based on full monthly spend profile across categories."""
    spend = {k: Decimal(str(v)) for k, v in req.monthly_spend.items()}
    scores = recommend_cards(spend, CREDIT_CARDS, PROGRAM_VALUATIONS, max_results=req.max_results)
    return {
        "recommendations": [
            {
                "card_id": s.card_id,
                "card_name": s.card_name,
                "issuer": s.issuer,
                "currency": s.currency,
                "annual_fee": str(s.annual_fee),
                "net_annual_fee": str(s.net_annual_fee),
                "total_points_earned": s.total_points_earned,
                "points_value": str(s.points_value),
                "net_value": str(s.net_value),
                "category_breakdown": s.category_breakdown,
            }
            for s in scores
        ],
    }


@router.post("/api/recommend-combo")
def recommend_combo_endpoint(req: SpendProfileRequest):
    """Recommend optimal primary + secondary card combination."""
    spend = {k: Decimal(str(v)) for k, v in req.monthly_spend.items()}
    combo = recommend_combo(spend, CREDIT_CARDS, PROGRAM_VALUATIONS)

    def _card_to_dict(s):
        return {
            "card_id": s.card_id,
            "card_name": s.card_name,
            "issuer": s.issuer,
            "net_value": str(s.net_value),
            "total_points_earned": s.total_points_earned,
        }

    return {
        "primary_card": _card_to_dict(combo.primary_card),
        "secondary_card": _card_to_dict(combo.secondary_card) if combo.secondary_card else None,
        "combined_net_value": str(combo.combined_net_value),
        "combined_points": combo.combined_points,
        "strategy_summary": combo.strategy_summary,
    }


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


@router.post("/api/savings-dashboard")
def savings_dashboard(req: SavingsRequest, strategy: str = "median"):
    """Enhanced savings analysis with optimization hints and portfolio summary."""
    try:
        strat = AggregationStrategy(strategy)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=f"Unknown strategy: {strategy}") from err

    balances = {item.program: item.points for item in req.balances}
    analysis = analyze_savings(balances, PROGRAM_VALUATIONS, strat)

    return {
        "total_points": analysis.total_points,
        "total_travel_value": str(analysis.total_travel_value),
        "total_cash_back_value": str(analysis.total_cash_back_value),
        "total_opportunity_cost": str(analysis.total_opportunity_cost),
        "weighted_avg_cpp": str(analysis.weighted_avg_cpp),
        "best_program": analysis.best_program,
        "worst_program": analysis.worst_program,
        "strategy": strat.value,
        "programs": [
            {
                "program_code": p.program_code,
                "program_name": p.program_name,
                "points": p.points,
                "travel_value": str(p.travel_value),
                "cash_back_value": str(p.cash_back_value),
                "opportunity_cost": str(p.opportunity_cost),
                "aggregated_cpp": str(p.aggregated_cpp),
                "confidence": p.confidence,
                "optimization_hint": p.optimization_hint,
            }
            for p in analysis.programs
        ],
    }


@router.get("/api/valuations/{program}")
def get_valuation(program: str, strategy: str = "median"):
    """Get aggregated CPP valuation for a single program."""
    val = PROGRAM_VALUATIONS.get(program)
    if val is None:
        raise HTTPException(status_code=404, detail=f"Unknown program: {program}")

    try:
        strat = AggregationStrategy(strategy)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=f"Unknown strategy: {strategy}") from err

    agg = aggregate_cpp(val, strat)
    return {
        "program_code": agg.program_code,
        "program_name": agg.program_name,
        "aggregated_cpp": str(agg.aggregated_cpp),
        "strategy": agg.strategy.value,
        "source_count": agg.source_count,
        "min_cpp": str(agg.min_cpp),
        "max_cpp": str(agg.max_cpp),
        "spread": str(agg.spread),
        "confidence": agg.confidence,
        "sources": {k: str(v) for k, v in agg.sources.items()},
    }


@router.get("/api/valuations")
def list_valuations(strategy: str = "median"):
    """Get aggregated CPP valuations for all programs."""
    try:
        strat = AggregationStrategy(strategy)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=f"Unknown strategy: {strategy}") from err

    results = batch_aggregate(PROGRAM_VALUATIONS, strat)
    return {
        "strategy": strat.value,
        "programs": [
            {
                "program_code": agg.program_code,
                "program_name": agg.program_name,
                "aggregated_cpp": str(agg.aggregated_cpp),
                "source_count": agg.source_count,
                "confidence": agg.confidence,
                "spread": str(agg.spread),
            }
            for agg in sorted(results.values(), key=lambda a: a.aggregated_cpp, reverse=True)
        ],
    }


@router.get("/api/trends")
def market_trends():
    """Market-wide valuation trends across all programs."""
    tracker = get_trend_tracker()
    if not tracker.tracked_programs:
        seed_trends(PROGRAM_VALUATIONS)

    names = {code: prog.program_name for code, prog in PROGRAM_VALUATIONS.items()}
    summary = tracker.market_summary(names)

    def _trend_dict(t):
        return {
            "program_code": t.program_code,
            "program_name": t.program_name,
            "current_cpp": str(t.current_cpp),
            "previous_cpp": str(t.previous_cpp),
            "change_pct": str(t.change_pct),
            "direction": t.direction.value,
            "period_days": t.period_days,
            "alert": t.alert,
        }

    return {
        "total_programs": summary.total_programs,
        "programs_up": summary.programs_up,
        "programs_down": summary.programs_down,
        "programs_stable": summary.programs_stable,
        "avg_change_pct": str(summary.avg_change_pct),
        "biggest_gain": _trend_dict(summary.biggest_gain) if summary.biggest_gain else None,
        "biggest_loss": _trend_dict(summary.biggest_loss) if summary.biggest_loss else None,
        "trends": [_trend_dict(t) for t in summary.trends],
    }


@router.get("/api/trends/{program}")
def program_trend(program: str):
    """Valuation trend for a specific program."""
    tracker = get_trend_tracker()
    if not tracker.tracked_programs:
        seed_trends(PROGRAM_VALUATIONS)

    val = PROGRAM_VALUATIONS.get(program)
    name = val.program_name if val else program
    trend = tracker.analyze(program, name)

    return {
        "program_code": trend.program_code,
        "program_name": trend.program_name,
        "current_cpp": str(trend.current_cpp),
        "previous_cpp": str(trend.previous_cpp),
        "change_cpp": str(trend.change_cpp),
        "change_pct": str(trend.change_pct),
        "direction": trend.direction.value,
        "period_days": trend.period_days,
        "alert": trend.alert,
        "snapshots": [{"date": s.date, "cpp": str(s.cpp), "source": s.source} for s in trend.snapshots],
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


@router.get("/api/program-health")
def program_health():
    """Health scores for all loyalty programs."""
    from collections import Counter

    from redeemflow.optimization.seed_data import ALL_PARTNERS
    from redeemflow.search.sweet_spots import ALL_SWEET_SPOTS

    transfer_counts: dict[str, int] = Counter()
    for p in ALL_PARTNERS:
        transfer_counts[p.source_program] += 1

    sweet_spot_counts: dict[str, int] = Counter()
    for s in ALL_SWEET_SPOTS:
        sweet_spot_counts[s.program] += 1

    scores = assess_all_programs(
        programs=PROGRAM_VALUATIONS,
        transfer_counts=dict(transfer_counts),
        sweet_spot_counts=dict(sweet_spot_counts),
    )

    return {
        "programs": [
            {
                "program_code": s.program_code,
                "program_name": s.program_name,
                "overall_score": s.overall_score,
                "grade": s.grade.value,
                "devaluation_risk": s.devaluation_risk.value,
                "stability_score": s.stability_score,
                "liquidity_score": s.liquidity_score,
                "value_score": s.value_score,
                "redemption_score": s.redemption_score,
                "trend_direction": s.trend_direction,
                "recommendation": s.recommendation,
            }
            for s in scores
        ],
    }
