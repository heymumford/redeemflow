"""Program health scores — reliability, stability, and devaluation risk.

Beck: Each program gets a composite score from multiple signals.
Fowler: Fitness function — quantified measure of program quality.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class HealthGrade(str, Enum):
    EXCELLENT = "excellent"  # 80-100
    GOOD = "good"  # 60-79
    FAIR = "fair"  # 40-59
    POOR = "poor"  # 20-39
    CRITICAL = "critical"  # 0-19


class DevalRisk(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    IMMINENT = "imminent"


@dataclass(frozen=True)
class ProgramHealthScore:
    """Composite health assessment for a loyalty program."""

    program_code: str
    program_name: str
    overall_score: int  # 0-100
    grade: HealthGrade
    devaluation_risk: DevalRisk
    stability_score: int  # 0-100 based on CPP variance
    liquidity_score: int  # 0-100 based on transfer partner count
    value_score: int  # 0-100 based on CPP vs peers
    redemption_score: int  # 0-100 based on sweet spot count
    trend_direction: str  # "up", "down", "stable"
    recommendation: str


def _grade_from_score(score: int) -> HealthGrade:
    if score >= 80:
        return HealthGrade.EXCELLENT
    if score >= 60:
        return HealthGrade.GOOD
    if score >= 40:
        return HealthGrade.FAIR
    if score >= 20:
        return HealthGrade.POOR
    return HealthGrade.CRITICAL


def _deval_risk(stability: int, trend: str) -> DevalRisk:
    if stability < 30 and trend == "down":
        return DevalRisk.IMMINENT
    if stability < 50 or trend == "down":
        return DevalRisk.HIGH
    if stability < 70:
        return DevalRisk.MODERATE
    return DevalRisk.LOW


def assess_program_health(
    program_code: str,
    program_name: str,
    cpp_values: dict[str, Decimal],  # source -> cpp
    transfer_partner_count: int = 0,
    sweet_spot_count: int = 0,
    trend_direction: str = "stable",
    peer_median_cpp: Decimal = Decimal("1.2"),
) -> ProgramHealthScore:
    """Compute composite health score for a program.

    Signals:
    - Stability: Low variance across sources = stable
    - Liquidity: More transfer partners = more flexibility
    - Value: CPP relative to peer median
    - Redemption: More sweet spots = better options
    """
    # Stability: based on CPP spread across sources
    if len(cpp_values) >= 2:
        vals = list(cpp_values.values())
        spread = max(vals) - min(vals)
        avg = sum(vals) / len(vals)
        if avg > 0:
            cv = float(spread / avg)  # coefficient of variation
            stability = max(0, min(100, int(100 - cv * 200)))
        else:
            stability = 50
    else:
        stability = 50  # No spread data

    # Liquidity: transfer partners (0 = 0, 1-2 = 40, 3-5 = 70, 6+ = 100)
    if transfer_partner_count >= 6:
        liquidity = 100
    elif transfer_partner_count >= 3:
        liquidity = 70
    elif transfer_partner_count >= 1:
        liquidity = 40
    else:
        liquidity = 0

    # Value: CPP vs peer median
    if cpp_values:
        avg_cpp = sum(cpp_values.values()) / len(cpp_values)
        ratio = float(avg_cpp / peer_median_cpp) if peer_median_cpp > 0 else 1.0
        value = max(0, min(100, int(ratio * 60)))
    else:
        value = 50

    # Redemption: sweet spots (0 = 20, 1 = 50, 2+ = 80, 3+ = 100)
    if sweet_spot_count >= 3:
        redemption = 100
    elif sweet_spot_count >= 2:
        redemption = 80
    elif sweet_spot_count >= 1:
        redemption = 50
    else:
        redemption = 20

    # Overall: weighted average
    overall = int(stability * 0.3 + liquidity * 0.25 + value * 0.25 + redemption * 0.2)

    # Trend adjustment
    if trend_direction == "down":
        overall = max(0, overall - 10)
    elif trend_direction == "up":
        overall = min(100, overall + 5)

    grade = _grade_from_score(overall)
    risk = _deval_risk(stability, trend_direction)

    # Generate recommendation
    if grade in (HealthGrade.EXCELLENT, HealthGrade.GOOD):
        rec = "Hold and use — strong program with stable value."
    elif grade == HealthGrade.FAIR:
        if risk in (DevalRisk.HIGH, DevalRisk.IMMINENT):
            rec = "Consider redeeming soon — devaluation risk is elevated."
        else:
            rec = "Acceptable value — monitor for changes."
    else:
        rec = "Redeem or transfer out — poor program health."

    return ProgramHealthScore(
        program_code=program_code,
        program_name=program_name,
        overall_score=overall,
        grade=grade,
        devaluation_risk=risk,
        stability_score=stability,
        liquidity_score=liquidity,
        value_score=value,
        redemption_score=redemption,
        trend_direction=trend_direction,
        recommendation=rec,
    )


def assess_all_programs(
    programs: dict,
    transfer_counts: dict[str, int],
    sweet_spot_counts: dict[str, int],
    trend_directions: dict[str, str] | None = None,
) -> list[ProgramHealthScore]:
    """Assess health for all programs."""
    trends = trend_directions or {}
    results = []

    # Compute peer median
    all_cpps = []
    for prog in programs.values():
        if hasattr(prog, "valuations") and prog.valuations:
            avg = sum(prog.valuations.values()) / len(prog.valuations)
            all_cpps.append(avg)
    peer_median = sorted(all_cpps)[len(all_cpps) // 2] if all_cpps else Decimal("1.2")

    for code, prog in programs.items():
        name = prog.program_name if hasattr(prog, "program_name") else code
        cpp_vals = {}
        if hasattr(prog, "valuations"):
            cpp_vals = {str(k): v for k, v in prog.valuations.items()}

        score = assess_program_health(
            program_code=code,
            program_name=name,
            cpp_values=cpp_vals,
            transfer_partner_count=transfer_counts.get(code, 0),
            sweet_spot_count=sweet_spot_counts.get(code, 0),
            trend_direction=trends.get(code, "stable"),
            peer_median_cpp=peer_median,
        )
        results.append(score)

    results.sort(key=lambda s: s.overall_score, reverse=True)
    return results
