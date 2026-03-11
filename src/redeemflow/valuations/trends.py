"""Points valuation trend tracking — historical CPP changes.

Beck: Simple data in, simple data out. Trends are derived facts.
Fowler: Temporal query — value changes over time windows.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum


class TrendDirection(str, Enum):
    UP = "up"
    DOWN = "down"
    STABLE = "stable"


@dataclass(frozen=True)
class ValuationSnapshot:
    """A point-in-time CPP valuation for a program."""

    program_code: str
    cpp: Decimal
    date: str  # ISO date
    source: str = "aggregate"


@dataclass(frozen=True)
class TrendAnalysis:
    """Computed trend for a single program."""

    program_code: str
    program_name: str
    current_cpp: Decimal
    previous_cpp: Decimal
    change_cpp: Decimal
    change_pct: Decimal
    direction: TrendDirection
    period_days: int
    snapshots: list[ValuationSnapshot]
    alert: str = ""


@dataclass(frozen=True)
class MarketSummary:
    """Market-wide trend overview."""

    total_programs: int
    programs_up: int
    programs_down: int
    programs_stable: int
    avg_change_pct: Decimal
    biggest_gain: TrendAnalysis | None
    biggest_loss: TrendAnalysis | None
    trends: list[TrendAnalysis]


@dataclass
class TrendTracker:
    """Tracks valuation snapshots over time."""

    _history: dict[str, list[ValuationSnapshot]] = field(default_factory=dict)

    def record(self, program_code: str, cpp: Decimal, date: str, source: str = "aggregate") -> ValuationSnapshot:
        """Record a valuation snapshot."""
        snap = ValuationSnapshot(program_code=program_code, cpp=cpp, date=date, source=source)
        if program_code not in self._history:
            self._history[program_code] = []
        self._history[program_code].append(snap)
        return snap

    def get_history(self, program_code: str) -> list[ValuationSnapshot]:
        """Get all snapshots for a program, oldest first."""
        return list(self._history.get(program_code, []))

    def analyze(self, program_code: str, program_name: str = "") -> TrendAnalysis:
        """Compute trend for a single program."""
        history = self.get_history(program_code)
        if not history:
            return TrendAnalysis(
                program_code=program_code,
                program_name=program_name,
                current_cpp=Decimal("0"),
                previous_cpp=Decimal("0"),
                change_cpp=Decimal("0"),
                change_pct=Decimal("0"),
                direction=TrendDirection.STABLE,
                period_days=0,
                snapshots=[],
            )

        if len(history) == 1:
            return TrendAnalysis(
                program_code=program_code,
                program_name=program_name,
                current_cpp=history[0].cpp,
                previous_cpp=history[0].cpp,
                change_cpp=Decimal("0"),
                change_pct=Decimal("0"),
                direction=TrendDirection.STABLE,
                period_days=0,
                snapshots=history,
            )

        current = history[-1]
        previous = history[0]
        change = current.cpp - previous.cpp
        pct = Decimal("0")
        if previous.cpp > 0:
            pct = (change / previous.cpp * 100).quantize(Decimal("0.1"))

        if change > Decimal("0.01"):
            direction = TrendDirection.UP
        elif change < Decimal("-0.01"):
            direction = TrendDirection.DOWN
        else:
            direction = TrendDirection.STABLE

        # Compute period in days
        period = _days_between(previous.date, current.date)

        alert = ""
        if pct <= Decimal("-10"):
            alert = f"Significant devaluation: {program_code} CPP dropped {abs(pct)}%"
        elif pct >= Decimal("10"):
            alert = f"Value increase: {program_code} CPP rose {pct}%"

        return TrendAnalysis(
            program_code=program_code,
            program_name=program_name,
            current_cpp=current.cpp,
            previous_cpp=previous.cpp,
            change_cpp=change,
            change_pct=pct,
            direction=direction,
            period_days=period,
            snapshots=history,
            alert=alert,
        )

    def market_summary(self, program_names: dict[str, str] | None = None) -> MarketSummary:
        """Compute market-wide trends across all tracked programs."""
        names = program_names or {}
        trends = [self.analyze(code, names.get(code, code)) for code in self._history]

        up = [t for t in trends if t.direction == TrendDirection.UP]
        down = [t for t in trends if t.direction == TrendDirection.DOWN]
        stable = [t for t in trends if t.direction == TrendDirection.STABLE]

        avg_pct = Decimal("0")
        if trends:
            avg_pct = (sum(t.change_pct for t in trends) / len(trends)).quantize(Decimal("0.1"))

        biggest_gain = max(trends, key=lambda t: t.change_pct) if trends else None
        biggest_loss = min(trends, key=lambda t: t.change_pct) if trends else None

        # Sort by absolute change (most movement first)
        trends.sort(key=lambda t: abs(t.change_pct), reverse=True)

        return MarketSummary(
            total_programs=len(trends),
            programs_up=len(up),
            programs_down=len(down),
            programs_stable=len(stable),
            avg_change_pct=avg_pct,
            biggest_gain=biggest_gain if biggest_gain and biggest_gain.change_pct > 0 else None,
            biggest_loss=biggest_loss if biggest_loss and biggest_loss.change_pct < 0 else None,
            trends=trends,
        )

    @property
    def tracked_programs(self) -> list[str]:
        return sorted(self._history.keys())


def _days_between(date1: str, date2: str) -> int:
    """Compute days between two ISO dates."""
    from datetime import date

    try:
        d1 = date.fromisoformat(date1)
        d2 = date.fromisoformat(date2)
        return abs((d2 - d1).days)
    except (ValueError, TypeError):
        return 0


# Singleton tracker seeded with historical data
_TRACKER = TrendTracker()


def get_trend_tracker() -> TrendTracker:
    return _TRACKER


def seed_trends(valuations: dict) -> None:
    """Seed tracker with current + simulated historical valuations."""
    tracker = get_trend_tracker()
    for code, prog in valuations.items():
        if hasattr(prog, "valuations"):
            vals = prog.valuations
            if vals:
                avg = sum(vals.values()) / len(vals)
                # Simulate 3-month history with slight movement
                tracker.record(code, (avg * Decimal("0.98")).quantize(Decimal("0.01")), "2025-01-01")
                tracker.record(code, (avg * Decimal("0.99")).quantize(Decimal("0.01")), "2025-02-01")
                tracker.record(code, avg.quantize(Decimal("0.01")), "2025-03-01")


def reset_tracker() -> None:
    """Reset for testing."""
    global _TRACKER
    _TRACKER = TrendTracker()
