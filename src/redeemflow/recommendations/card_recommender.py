"""Card recommender — spend-pattern-aware card scoring and combination optimization.

Fowler: Strategy pattern — scoring is pluggable. Aggregate Root — CardRecommendation owns its data.
Beck: Each method answers one question. No hidden coupling.

Given a user's monthly spending by category, recommends the optimal card or card combo
by scoring each card's earn rate × CPP against the spend profile.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from redeemflow.valuations.models import CreditCard, ProgramValuation


@dataclass(frozen=True)
class CardScore:
    """Scored card for a given spend profile."""

    card_id: str
    card_name: str
    issuer: str
    currency: str
    annual_fee: Decimal
    net_annual_fee: Decimal
    total_points_earned: int
    points_value: Decimal
    net_value: Decimal
    category_breakdown: dict[str, int]
    first_year_bonus_value: Decimal = Decimal("0")


@dataclass(frozen=True)
class CardComboRecommendation:
    """Optimal combination of cards for a spend profile."""

    primary_card: CardScore
    secondary_card: CardScore | None
    combined_net_value: Decimal
    combined_points: int
    strategy_summary: str


def score_card(
    card: CreditCard,
    card_id: str,
    spend_by_category: dict[str, Decimal],
    valuation: ProgramValuation | None,
) -> CardScore:
    """Score a single card against a spending profile."""
    cpp = valuation.median_cpp if valuation else Decimal("1.0")

    category_breakdown: dict[str, int] = {}
    total_points = 0

    for category, monthly_amount in spend_by_category.items():
        annual = monthly_amount * 12
        points = card.points_earned(category, annual)
        category_breakdown[category] = points
        total_points += points

    points_value = (Decimal(total_points) * cpp / Decimal(100)).quantize(Decimal("0.01"))
    net_value = points_value - card.net_annual_fee

    return CardScore(
        card_id=card_id,
        card_name=card.name,
        issuer=card.issuer,
        currency=card.currency,
        annual_fee=card.annual_fee,
        net_annual_fee=card.net_annual_fee,
        total_points_earned=total_points,
        points_value=points_value,
        net_value=net_value,
        category_breakdown=category_breakdown,
    )


def recommend_cards(
    spend_by_category: dict[str, Decimal],
    cards: dict[str, CreditCard],
    valuations: dict[str, ProgramValuation],
    max_results: int = 5,
) -> list[CardScore]:
    """Rank all cards by net value for a given spend profile."""
    scores: list[CardScore] = []
    for card_id, card in cards.items():
        val = valuations.get(card.currency)
        score = score_card(card, card_id, spend_by_category, val)
        scores.append(score)

    scores.sort(key=lambda s: s.net_value, reverse=True)
    return scores[:max_results]


def recommend_combo(
    spend_by_category: dict[str, Decimal],
    cards: dict[str, CreditCard],
    valuations: dict[str, ProgramValuation],
) -> CardComboRecommendation:
    """Find the optimal primary + secondary card combination.

    The primary card covers the highest-earning categories.
    The secondary card (different issuer) covers remaining spend.
    """
    all_scores = recommend_cards(spend_by_category, cards, valuations, max_results=len(cards))

    if not all_scores:
        raise ValueError("No cards available to recommend")

    primary = all_scores[0]

    # Find best secondary from a different issuer
    secondary = None
    for score in all_scores[1:]:
        if score.issuer != primary.issuer:
            secondary = score
            break

    combined_value = primary.net_value + (secondary.net_value if secondary else Decimal("0"))
    combined_points = primary.total_points_earned + (secondary.total_points_earned if secondary else 0)

    if secondary:
        summary = f"Use {primary.card_name} as primary, {secondary.card_name} for complementary categories"
    else:
        summary = f"Use {primary.card_name} as your primary card"

    return CardComboRecommendation(
        primary_card=primary,
        secondary_card=secondary,
        combined_net_value=combined_value,
        combined_points=combined_points,
        strategy_summary=summary,
    )
