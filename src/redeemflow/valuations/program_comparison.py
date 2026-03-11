"""Program comparison — side-by-side loyalty program evaluation.

Beck: Comparison is a projection — programs in, ranked assessment out.
Fowler: Value Object for each comparison dimension.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class ComparisonDimension(str, Enum):
    VALUE = "value"
    FLEXIBILITY = "flexibility"
    PARTNERS = "partners"
    EARNING = "earning"
    REDEMPTION = "redemption"


@dataclass(frozen=True)
class ProgramProfile:
    """Profile of a loyalty program for comparison."""

    program_code: str
    program_name: str
    cpp: Decimal
    transfer_partners: int
    sweet_spot_count: int
    earn_categories: int  # Number of bonus earn categories
    redemption_options: int  # Number of redemption types
    annual_fee: Decimal = Decimal("0")
    sign_up_bonus: int = 0


@dataclass(frozen=True)
class DimensionScore:
    """Score for a single comparison dimension."""

    dimension: ComparisonDimension
    score: Decimal  # 0-100
    rank: int  # 1 = best
    detail: str


@dataclass(frozen=True)
class ProgramComparison:
    """Complete comparison of a program against peers."""

    program_code: str
    program_name: str
    overall_score: Decimal
    overall_rank: int
    dimension_scores: list[DimensionScore]


@dataclass(frozen=True)
class ComparisonReport:
    """Full comparison report across multiple programs."""

    programs: list[ProgramComparison]
    best_overall: str
    best_by_dimension: dict[str, str]  # dimension -> program_code


# Default program profiles
PROGRAM_PROFILES: dict[str, ProgramProfile] = {
    "chase-ur": ProgramProfile(
        "chase-ur", "Chase Ultimate Rewards", Decimal("1.50"), 14, 8, 3, 5, Decimal("550"), 60000
    ),
    "amex-mr": ProgramProfile(
        "amex-mr", "Amex Membership Rewards", Decimal("1.30"), 21, 6, 4, 6, Decimal("695"), 80000
    ),
    "citi-typ": ProgramProfile("citi-typ", "Citi ThankYou Points", Decimal("1.20"), 16, 4, 3, 4, Decimal("95"), 60000),
    "united": ProgramProfile("united", "United MileagePlus", Decimal("1.30"), 3, 5, 2, 3, Decimal("0")),
    "aa": ProgramProfile("aa", "AAdvantage", Decimal("1.40"), 3, 4, 2, 3, Decimal("0")),
    "delta": ProgramProfile("delta", "Delta SkyMiles", Decimal("1.20"), 2, 3, 2, 3, Decimal("0")),
    "hyatt": ProgramProfile("hyatt", "World of Hyatt", Decimal("1.70"), 2, 6, 1, 2, Decimal("0")),
    "marriott": ProgramProfile("marriott", "Marriott Bonvoy", Decimal("0.80"), 40, 3, 1, 3, Decimal("0")),
}


def _score_value(profile: ProgramProfile, max_cpp: Decimal) -> Decimal:
    if max_cpp <= 0:
        return Decimal("0")
    return (profile.cpp / max_cpp * 100).quantize(Decimal("0.1"))


def _score_flexibility(profile: ProgramProfile, max_partners: int) -> Decimal:
    if max_partners <= 0:
        return Decimal("0")
    return (Decimal(str(profile.transfer_partners)) / Decimal(str(max_partners)) * 100).quantize(Decimal("0.1"))


def _score_partners(profile: ProgramProfile, max_sweet: int) -> Decimal:
    if max_sweet <= 0:
        return Decimal("0")
    return (Decimal(str(profile.sweet_spot_count)) / Decimal(str(max_sweet)) * 100).quantize(Decimal("0.1"))


def compare_programs(program_codes: list[str] | None = None) -> ComparisonReport:
    """Compare loyalty programs across multiple dimensions."""
    codes = program_codes or list(PROGRAM_PROFILES.keys())
    profiles = [PROGRAM_PROFILES[c] for c in codes if c in PROGRAM_PROFILES]

    if not profiles:
        return ComparisonReport(programs=[], best_overall="", best_by_dimension={})

    max_cpp = max(p.cpp for p in profiles)
    max_partners = max(p.transfer_partners for p in profiles)
    max_sweet = max(p.sweet_spot_count for p in profiles)

    comparisons: list[ProgramComparison] = []
    for profile in profiles:
        value_score = _score_value(profile, max_cpp)
        flex_score = _score_flexibility(profile, max_partners)
        partner_score = _score_partners(profile, max_sweet)

        overall = ((value_score + flex_score + partner_score) / 3).quantize(Decimal("0.1"))
        comparisons.append(
            ProgramComparison(
                program_code=profile.program_code,
                program_name=profile.program_name,
                overall_score=overall,
                overall_rank=0,
                dimension_scores=[
                    DimensionScore(ComparisonDimension.VALUE, value_score, 0, f"CPP: {profile.cpp}"),
                    DimensionScore(
                        ComparisonDimension.FLEXIBILITY, flex_score, 0, f"{profile.transfer_partners} transfer partners"
                    ),
                    DimensionScore(
                        ComparisonDimension.PARTNERS, partner_score, 0, f"{profile.sweet_spot_count} sweet spots"
                    ),
                ],
            )
        )

    # Assign ranks
    comparisons.sort(key=lambda c: c.overall_score, reverse=True)
    ranked = []
    for i, c in enumerate(comparisons, 1):
        ranked.append(
            ProgramComparison(
                program_code=c.program_code,
                program_name=c.program_name,
                overall_score=c.overall_score,
                overall_rank=i,
                dimension_scores=c.dimension_scores,
            )
        )

    best_overall = ranked[0].program_code if ranked else ""

    # Best per dimension
    best_by_dim: dict[str, str] = {}
    for dim in ComparisonDimension:
        dim_scores = []
        for c in ranked:
            for ds in c.dimension_scores:
                if ds.dimension == dim:
                    dim_scores.append((c.program_code, ds.score))
        if dim_scores:
            best_by_dim[dim.value] = max(dim_scores, key=lambda x: x[1])[0]

    return ComparisonReport(
        programs=ranked,
        best_overall=best_overall,
        best_by_dimension=best_by_dim,
    )
