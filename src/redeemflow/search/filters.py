"""Search filters and sorting — multi-dimension result filtering.

Beck: Composable predicates — each filter is a pure function from result to bool.
Fowler: Specification pattern — combine filters declaratively.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum

from redeemflow.search.award_search import AwardResult


class SortField(str, Enum):
    POINTS = "points"
    VALUE = "value"
    CPP = "cpp"
    SEATS = "seats"


class SortDirection(str, Enum):
    ASC = "asc"
    DESC = "desc"


@dataclass(frozen=True)
class SearchFilters:
    """Declarative search filter specification."""

    cabins: list[str] = field(default_factory=list)
    programs: list[str] = field(default_factory=list)
    max_points: int | None = None
    min_points: int | None = None
    direct_only: bool = False
    min_seats: int | None = None
    min_cpp: Decimal | None = None
    max_cpp: Decimal | None = None
    sort_by: SortField = SortField.POINTS
    sort_direction: SortDirection = SortDirection.ASC
    limit: int = 50


@dataclass(frozen=True)
class FilteredSearchResult:
    """Search result enriched with computed metrics."""

    result: AwardResult
    cpp: Decimal
    value_rating: str  # "excellent", "good", "fair", "poor"


def compute_cpp(result: AwardResult) -> Decimal:
    """Cents per point for this result."""
    if result.points_required <= 0:
        return Decimal("0")
    return (result.cash_value * 100 / result.points_required).quantize(Decimal("0.01"))


def _value_rating(cpp: Decimal) -> str:
    """Rate the value based on CPP."""
    if cpp >= Decimal("3.0"):
        return "excellent"
    if cpp >= Decimal("2.0"):
        return "good"
    if cpp >= Decimal("1.0"):
        return "fair"
    return "poor"


def apply_filters(results: list[AwardResult], filters: SearchFilters) -> list[FilteredSearchResult]:
    """Apply filters and sorting to search results."""
    filtered: list[FilteredSearchResult] = []

    for r in results:
        # Cabin filter
        if filters.cabins and r.cabin not in filters.cabins:
            continue

        # Program filter
        if filters.programs and r.program not in filters.programs:
            continue

        # Points range
        if filters.max_points is not None and r.points_required > filters.max_points:
            continue
        if filters.min_points is not None and r.points_required < filters.min_points:
            continue

        # Direct only
        if filters.direct_only and not r.direct:
            continue

        # Seats filter
        if filters.min_seats is not None:
            if r.available_seats is None or r.available_seats < filters.min_seats:
                continue

        # Compute CPP
        cpp = compute_cpp(r)

        # CPP range
        if filters.min_cpp is not None and cpp < filters.min_cpp:
            continue
        if filters.max_cpp is not None and cpp > filters.max_cpp:
            continue

        filtered.append(
            FilteredSearchResult(
                result=r,
                cpp=cpp,
                value_rating=_value_rating(cpp),
            )
        )

    # Sort
    filtered = _sort_results(filtered, filters.sort_by, filters.sort_direction)

    # Limit
    return filtered[: filters.limit]


def _key_points(r: FilteredSearchResult) -> int:
    return r.result.points_required


def _key_value(r: FilteredSearchResult) -> Decimal:
    return r.result.cash_value


def _key_cpp(r: FilteredSearchResult) -> Decimal:
    return r.cpp


def _key_seats(r: FilteredSearchResult) -> int:
    return r.result.available_seats if r.result.available_seats is not None else 0


_SORT_KEYS = {
    SortField.POINTS: _key_points,
    SortField.VALUE: _key_value,
    SortField.CPP: _key_cpp,
    SortField.SEATS: _key_seats,
}


def _sort_results(
    results: list[FilteredSearchResult],
    sort_by: SortField,
    direction: SortDirection,
) -> list[FilteredSearchResult]:
    """Sort filtered results by the specified field."""
    reverse = direction == SortDirection.DESC
    key = _SORT_KEYS.get(sort_by, _key_points)
    return sorted(results, key=key, reverse=reverse)


def search_summary(results: list[FilteredSearchResult]) -> dict:
    """Generate summary statistics for filtered results."""
    if not results:
        return {
            "total_results": 0,
            "cabins": [],
            "programs": [],
            "points_range": None,
            "cpp_range": None,
            "best_value": None,
        }

    programs = sorted({r.result.program for r in results})
    cabins = sorted({r.result.cabin for r in results})
    points = [r.result.points_required for r in results]
    cpps = [r.cpp for r in results]

    best = max(results, key=lambda r: r.cpp)

    return {
        "total_results": len(results),
        "cabins": cabins,
        "programs": programs,
        "points_range": {"min": min(points), "max": max(points)},
        "cpp_range": {"min": str(min(cpps)), "max": str(max(cpps))},
        "best_value": {
            "program": best.result.program,
            "points": best.result.points_required,
            "cpp": str(best.cpp),
            "rating": best.value_rating,
        },
    }
