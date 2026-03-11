"""Strategy quiz — classify user's points strategy and recommend programs.

Fowler: Strategy pattern — scoring functions are pluggable.
Beck: Each question maps to exactly one dimension. No hidden coupling.

The quiz classifies users into one of four archetypes based on their
travel preferences and spending habits, then recommends programs and cards.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class StrategyArchetype(str, Enum):
    MAXIMIZER = "maximizer"  # Optimizes for highest CPP, willing to be flexible
    SIMPLIFIER = "simplifier"  # Values ease of use, prefers cash back or portal bookings
    ASPIRATIONAL = "aspirational"  # Targets luxury experiences (first class, top hotels)
    ACCUMULATOR = "accumulator"  # Focuses on earning, less on redeeming


class TravelFrequency(str, Enum):
    RARELY = "rarely"  # 0-1 trips/year
    OCCASIONAL = "occasional"  # 2-4 trips/year
    FREQUENT = "frequent"  # 5+ trips/year


class RedemptionPreference(str, Enum):
    CASH_BACK = "cash_back"
    TRAVEL_PORTAL = "travel_portal"
    TRANSFER_PARTNERS = "transfer_partners"
    NO_PREFERENCE = "no_preference"


class SpendLevel(str, Enum):
    LOW = "low"  # < $2K/month
    MEDIUM = "medium"  # $2K-5K/month
    HIGH = "high"  # > $5K/month


@dataclass(frozen=True)
class QuizAnswers:
    """User's quiz responses."""

    travel_frequency: TravelFrequency
    preferred_cabin: str  # economy, business, first
    redemption_preference: RedemptionPreference
    monthly_spend: SpendLevel
    flexibility: bool  # Willing to be flexible with dates/routes
    hotel_priority: str  # budget, midrange, luxury


@dataclass(frozen=True)
class QuizResult:
    """Quiz classification result with recommendations."""

    archetype: StrategyArchetype
    archetype_description: str
    recommended_programs: list[str]
    recommended_cards: list[str]
    top_strategy: str
    secondary_strategy: str
    score_breakdown: dict[str, int]


# Scoring matrix: each answer contributes points to each archetype
def _score_answers(answers: QuizAnswers) -> dict[StrategyArchetype, int]:
    scores: dict[StrategyArchetype, int] = {a: 0 for a in StrategyArchetype}

    # Travel frequency
    if answers.travel_frequency == TravelFrequency.FREQUENT:
        scores[StrategyArchetype.MAXIMIZER] += 3
        scores[StrategyArchetype.ASPIRATIONAL] += 2
    elif answers.travel_frequency == TravelFrequency.OCCASIONAL:
        scores[StrategyArchetype.SIMPLIFIER] += 2
        scores[StrategyArchetype.ACCUMULATOR] += 1
    else:
        scores[StrategyArchetype.SIMPLIFIER] += 3
        scores[StrategyArchetype.ACCUMULATOR] += 2

    # Preferred cabin
    if answers.preferred_cabin in ("first", "business"):
        scores[StrategyArchetype.ASPIRATIONAL] += 3
        scores[StrategyArchetype.MAXIMIZER] += 1
    else:
        scores[StrategyArchetype.SIMPLIFIER] += 2
        scores[StrategyArchetype.ACCUMULATOR] += 1

    # Redemption preference
    if answers.redemption_preference == RedemptionPreference.TRANSFER_PARTNERS:
        scores[StrategyArchetype.MAXIMIZER] += 3
    elif answers.redemption_preference == RedemptionPreference.CASH_BACK:
        scores[StrategyArchetype.SIMPLIFIER] += 3
    elif answers.redemption_preference == RedemptionPreference.TRAVEL_PORTAL:
        scores[StrategyArchetype.SIMPLIFIER] += 1
        scores[StrategyArchetype.ACCUMULATOR] += 2

    # Monthly spend
    if answers.monthly_spend == SpendLevel.HIGH:
        scores[StrategyArchetype.ACCUMULATOR] += 3
        scores[StrategyArchetype.MAXIMIZER] += 1
    elif answers.monthly_spend == SpendLevel.MEDIUM:
        scores[StrategyArchetype.ACCUMULATOR] += 1
    else:
        scores[StrategyArchetype.SIMPLIFIER] += 1

    # Flexibility
    if answers.flexibility:
        scores[StrategyArchetype.MAXIMIZER] += 2
    else:
        scores[StrategyArchetype.SIMPLIFIER] += 2

    # Hotel priority
    if answers.hotel_priority == "luxury":
        scores[StrategyArchetype.ASPIRATIONAL] += 3
    elif answers.hotel_priority == "midrange":
        scores[StrategyArchetype.ACCUMULATOR] += 1
    else:
        scores[StrategyArchetype.SIMPLIFIER] += 1

    return scores


ARCHETYPE_DESCRIPTIONS = {
    StrategyArchetype.MAXIMIZER: (
        "You optimize every point for maximum value. Transfer partners and sweet spots are your playground."
    ),
    StrategyArchetype.SIMPLIFIER: (
        "You value simplicity and predictability. Cash back and portal bookings keep things easy."
    ),
    StrategyArchetype.ASPIRATIONAL: (
        "You save up for luxury experiences. First class flights and top-tier hotels are your goal."
    ),
    StrategyArchetype.ACCUMULATOR: (
        "You focus on earning as many points as possible. High-spend categories are your strength."
    ),
}

ARCHETYPE_PROGRAMS = {
    StrategyArchetype.MAXIMIZER: ["chase-ur", "amex-mr", "citi-ty", "hyatt"],
    StrategyArchetype.SIMPLIFIER: ["capital-one", "wells-fargo", "southwest"],
    StrategyArchetype.ASPIRATIONAL: ["amex-mr", "chase-ur", "united", "american", "hyatt"],
    StrategyArchetype.ACCUMULATOR: ["amex-mr", "chase-ur", "bilt", "capital-one"],
}

ARCHETYPE_CARDS = {
    StrategyArchetype.MAXIMIZER: ["chase-sapphire-reserve", "amex-platinum", "citi-strata-premier"],
    StrategyArchetype.SIMPLIFIER: ["capital-one-venture-x", "chase-sapphire-preferred"],
    StrategyArchetype.ASPIRATIONAL: ["amex-platinum", "chase-sapphire-reserve", "amex-gold"],
    StrategyArchetype.ACCUMULATOR: ["amex-gold", "chase-ink-preferred", "bilt-mastercard"],
}

ARCHETYPE_STRATEGIES = {
    StrategyArchetype.MAXIMIZER: (
        "Transfer points to airline/hotel partners at sweet spot valuations",
        "Monitor transfer bonuses for 20-40% extra value",
    ),
    StrategyArchetype.SIMPLIFIER: (
        "Use cash back or portal bookings for consistent 1-2 CPP",
        "Keep one premium card for travel protections and lounge access",
    ),
    StrategyArchetype.ASPIRATIONAL: (
        "Accumulate transferable points for premium cabin redemptions",
        "Target off-peak award charts for luxury hotels",
    ),
    StrategyArchetype.ACCUMULATOR: (
        "Maximize category bonuses across 2-3 complementary cards",
        "Stockpile flexible currencies for future high-value redemptions",
    ),
}


def classify(answers: QuizAnswers) -> QuizResult:
    """Classify a user's strategy archetype based on quiz answers."""
    scores = _score_answers(answers)
    sorted_archetypes = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    primary = sorted_archetypes[0][0]
    top_strat, secondary_strat = ARCHETYPE_STRATEGIES[primary]

    return QuizResult(
        archetype=primary,
        archetype_description=ARCHETYPE_DESCRIPTIONS[primary],
        recommended_programs=ARCHETYPE_PROGRAMS[primary],
        recommended_cards=ARCHETYPE_CARDS[primary],
        top_strategy=top_strat,
        secondary_strategy=secondary_strat,
        score_breakdown={a.value: s for a, s in scores.items()},
    )
