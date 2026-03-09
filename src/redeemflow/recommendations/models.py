"""Recommendations domain — value objects."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Recommendation:
    program_code: str
    action: str
    rationale: str
    cpp_gain: Decimal
    points_involved: int
