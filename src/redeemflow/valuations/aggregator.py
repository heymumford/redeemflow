"""CPP aggregation service — multi-source valuation with configurable strategies.

Fowler: Strategy pattern — the aggregation method is a pluggable policy.
Beck: Simple things simple. The default (median) is always correct. Weights are opt-in.

Invariant: aggregated CPP always falls between min and max source value.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from statistics import median

from redeemflow.valuations.models import ProgramValuation, ValuationSource


class AggregationStrategy(str, Enum):
    MEDIAN = "median"
    MEAN = "mean"
    WEIGHTED = "weighted"


# Default credibility weights per source (higher = more trusted)
DEFAULT_SOURCE_WEIGHTS: dict[ValuationSource, Decimal] = {
    ValuationSource.TPG: Decimal("1.0"),
    ValuationSource.OMAAT: Decimal("1.2"),
    ValuationSource.NERDWALLET: Decimal("0.8"),
    ValuationSource.UPGRADED_POINTS: Decimal("0.9"),
}


@dataclass(frozen=True)
class AggregatedValuation:
    """Result of aggregating CPP across multiple sources."""

    program_code: str
    program_name: str
    aggregated_cpp: Decimal
    strategy: AggregationStrategy
    source_count: int
    min_cpp: Decimal
    max_cpp: Decimal
    spread: Decimal
    sources: dict[str, Decimal]

    @property
    def confidence(self) -> str:
        """Higher source count and lower spread = higher confidence."""
        if self.source_count >= 3 and self.spread < Decimal("0.5"):
            return "high"
        if self.source_count >= 2:
            return "medium"
        return "low"


def aggregate_cpp(
    valuation: ProgramValuation,
    strategy: AggregationStrategy = AggregationStrategy.MEDIAN,
    weights: dict[ValuationSource, Decimal] | None = None,
) -> AggregatedValuation:
    """Aggregate CPP from multiple sources using the given strategy.

    Invariant: result.min_cpp <= result.aggregated_cpp <= result.max_cpp
    """
    cpps = valuation.valuations
    values = list(cpps.values())

    if strategy == AggregationStrategy.MEDIAN:
        agg = Decimal(str(median(values)))
    elif strategy == AggregationStrategy.MEAN:
        agg = (sum(values) / Decimal(len(values))).quantize(Decimal("0.01"))
    elif strategy == AggregationStrategy.WEIGHTED:
        w = weights or DEFAULT_SOURCE_WEIGHTS
        total_weight = Decimal("0")
        weighted_sum = Decimal("0")
        for source, cpp in cpps.items():
            source_weight = w.get(source, Decimal("1.0"))
            weighted_sum += cpp * source_weight
            total_weight += source_weight
        agg = (weighted_sum / total_weight).quantize(Decimal("0.01"))
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

    min_v = min(values)
    max_v = max(values)

    # Clamp to enforce invariant (weighted can theoretically drift due to rounding)
    agg = max(min_v, min(max_v, agg))

    return AggregatedValuation(
        program_code=valuation.program_code,
        program_name=valuation.program_name,
        aggregated_cpp=agg,
        strategy=strategy,
        source_count=len(cpps),
        min_cpp=min_v,
        max_cpp=max_v,
        spread=max_v - min_v,
        sources={src.value: cpp for src, cpp in cpps.items()},
    )


def batch_aggregate(
    valuations: dict[str, ProgramValuation],
    strategy: AggregationStrategy = AggregationStrategy.MEDIAN,
) -> dict[str, AggregatedValuation]:
    """Aggregate all programs at once. Returns dict keyed by program_code."""
    return {code: aggregate_cpp(val, strategy) for code, val in valuations.items()}
