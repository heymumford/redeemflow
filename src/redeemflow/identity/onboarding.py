"""Onboarding flow — guided new user setup.

Beck: Step-by-step value object chain — each step produces the next step's input.
Fowler: Aggregates program detection, goal suggestions, and recommendations into a
single onboarding report without tight coupling to those modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum


class OnboardingStep(str, Enum):
    PROGRAMS = "programs"
    GOALS = "goals"
    PREFERENCES = "preferences"
    COMPLETE = "complete"


class TravelStyle(str, Enum):
    BUDGET = "budget"
    COMFORT = "comfort"
    LUXURY = "luxury"
    BUSINESS = "business"


@dataclass(frozen=True)
class ProgramSelection:
    """A program the user has selected during onboarding."""

    program_code: str
    estimated_balance: int = 0
    is_primary: bool = False


@dataclass(frozen=True)
class GoalSuggestion:
    """A suggested savings goal based on the user's programs."""

    goal_name: str
    program_code: str
    target_points: int
    estimated_value: Decimal
    category: str
    rationale: str


@dataclass(frozen=True)
class OnboardingProfile:
    """User preferences collected during onboarding."""

    travel_style: TravelStyle
    home_airport: str
    preferred_cabins: list[str] = field(default_factory=list)
    travel_frequency: int = 4  # trips per year
    interested_in_hotels: bool = True
    interested_in_flights: bool = True


@dataclass(frozen=True)
class OnboardingReport:
    """Complete onboarding summary with setup recommendations."""

    user_id: str
    programs: list[ProgramSelection]
    suggested_goals: list[GoalSuggestion]
    profile: OnboardingProfile
    quick_wins: list[str]
    next_actions: list[str]
    estimated_portfolio_value: Decimal
    completed_at: str
    current_step: OnboardingStep


# Known program metadata for goal suggestions
_PROGRAM_INFO: dict[str, dict] = {
    "chase-ur": {"name": "Chase Ultimate Rewards", "cpp": Decimal("1.5"), "type": "bank"},
    "amex-mr": {"name": "Amex Membership Rewards", "cpp": Decimal("1.6"), "type": "bank"},
    "citi-typ": {"name": "Citi ThankYou Points", "cpp": Decimal("1.4"), "type": "bank"},
    "capital-one": {"name": "Capital One Miles", "cpp": Decimal("1.3"), "type": "bank"},
    "bilt": {"name": "Bilt Rewards", "cpp": Decimal("1.5"), "type": "bank"},
    "united": {"name": "United MileagePlus", "cpp": Decimal("1.3"), "type": "airline"},
    "aa": {"name": "AAdvantage", "cpp": Decimal("1.4"), "type": "airline"},
    "delta": {"name": "Delta SkyMiles", "cpp": Decimal("1.2"), "type": "airline"},
    "southwest": {"name": "Southwest Rapid Rewards", "cpp": Decimal("1.4"), "type": "airline"},
    "hyatt": {"name": "World of Hyatt", "cpp": Decimal("1.7"), "type": "hotel"},
    "marriott": {"name": "Marriott Bonvoy", "cpp": Decimal("0.7"), "type": "hotel"},
    "hilton": {"name": "Hilton Honors", "cpp": Decimal("0.5"), "type": "hotel"},
}


def suggest_goals(programs: list[ProgramSelection], profile: OnboardingProfile) -> list[GoalSuggestion]:
    """Generate goal suggestions based on selected programs and preferences."""
    suggestions: list[GoalSuggestion] = []

    for prog in programs:
        info = _PROGRAM_INFO.get(prog.program_code)
        if info is None:
            continue

        cpp = info["cpp"]
        prog_type = info["type"]

        if prog_type == "airline" and profile.interested_in_flights:
            if profile.travel_style in (TravelStyle.LUXURY, TravelStyle.BUSINESS):
                target = 80000
                category = "flight"
                name = f"Business class flight with {info['name']}"
                rationale = "Premium cabin redemptions offer the best CPP for your travel style"
            else:
                target = 25000
                category = "flight"
                name = f"Domestic round-trip with {info['name']}"
                rationale = "Start with an achievable domestic redemption"

            suggestions.append(
                GoalSuggestion(
                    goal_name=name,
                    program_code=prog.program_code,
                    target_points=target,
                    estimated_value=(Decimal(str(target)) * cpp / Decimal("100")).quantize(Decimal("0.01")),
                    category=category,
                    rationale=rationale,
                )
            )

        elif prog_type == "hotel" and profile.interested_in_hotels:
            target = 25000 if cpp >= Decimal("1.0") else 50000
            suggestions.append(
                GoalSuggestion(
                    goal_name=f"Free night at {info['name']} property",
                    program_code=prog.program_code,
                    target_points=target,
                    estimated_value=(Decimal(str(target)) * cpp / Decimal("100")).quantize(Decimal("0.01")),
                    category="hotel",
                    rationale="Hotel redemptions are a great way to maximize point value",
                )
            )

        elif prog_type == "bank":
            if profile.travel_style in (TravelStyle.LUXURY, TravelStyle.BUSINESS):
                target = 100000
            else:
                target = 50000
            suggestions.append(
                GoalSuggestion(
                    goal_name=f"Transfer bonus target for {info['name']}",
                    program_code=prog.program_code,
                    target_points=target,
                    estimated_value=(Decimal(str(target)) * cpp / Decimal("100")).quantize(Decimal("0.01")),
                    category="transfer",
                    rationale="Bank points are most valuable when transferred to partners during bonuses",
                )
            )

    return suggestions


def generate_quick_wins(programs: list[ProgramSelection], profile: OnboardingProfile) -> list[str]:
    """Generate quick win suggestions for new users."""
    wins: list[str] = []

    bank_programs = [p for p in programs if _PROGRAM_INFO.get(p.program_code, {}).get("type") == "bank"]
    airline_programs = [p for p in programs if _PROGRAM_INFO.get(p.program_code, {}).get("type") == "airline"]
    hotel_programs = [p for p in programs if _PROGRAM_INFO.get(p.program_code, {}).get("type") == "hotel"]

    if bank_programs:
        wins.append("Set up transfer bonus alerts — bonuses can increase value by 25-40%")
    if airline_programs:
        wins.append("Check seasonal pricing for your home airport — off-peak redemptions save 30-50%")
    if hotel_programs:
        wins.append("Compare hotel point values — Hyatt points are worth 2-3x more than Hilton/Marriott")
    if len(programs) >= 3:
        wins.append("Run a portfolio rebalance check to optimize your point distribution")
    if profile.travel_frequency >= 6:
        wins.append("Set up saved searches for your frequent routes to catch availability drops")

    wins.append("Enable expiration alerts to protect your points from inactivity")
    return wins


def complete_onboarding(
    user_id: str,
    programs: list[ProgramSelection],
    profile: OnboardingProfile,
) -> OnboardingReport:
    """Complete the onboarding flow and generate the final report."""
    goals = suggest_goals(programs, profile)
    quick_wins = generate_quick_wins(programs, profile)

    total_value = Decimal("0")
    for prog in programs:
        info = _PROGRAM_INFO.get(prog.program_code)
        if info and prog.estimated_balance > 0:
            total_value += (Decimal(str(prog.estimated_balance)) * info["cpp"] / Decimal("100")).quantize(
                Decimal("0.01")
            )

    next_actions = [
        "Sync your loyalty program accounts for accurate balances",
        "Review and customize your suggested savings goals",
        "Set up notification preferences for alerts that matter to you",
    ]
    if len(programs) >= 2:
        next_actions.append("Explore transfer partner options between your programs")

    return OnboardingReport(
        user_id=user_id,
        programs=programs,
        suggested_goals=goals,
        profile=profile,
        quick_wins=quick_wins,
        next_actions=next_actions,
        estimated_portfolio_value=total_value,
        completed_at=datetime.now(UTC).isoformat(),
        current_step=OnboardingStep.COMPLETE,
    )
