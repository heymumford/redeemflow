"""Charity partner network domain — value objects and state holder.

Beck: The simplest thing that could work.
Fowler: Value objects are immutable. State holders are mutable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum

VALID_US_STATES = frozenset(
    {
        "AL",
        "AK",
        "AZ",
        "AR",
        "CA",
        "CO",
        "CT",
        "DE",
        "FL",
        "GA",
        "HI",
        "ID",
        "IL",
        "IN",
        "IA",
        "KS",
        "KY",
        "LA",
        "ME",
        "MD",
        "MA",
        "MI",
        "MN",
        "MS",
        "MO",
        "MT",
        "NE",
        "NV",
        "NH",
        "NJ",
        "NM",
        "NY",
        "NC",
        "ND",
        "OH",
        "OK",
        "OR",
        "PA",
        "RI",
        "SC",
        "SD",
        "TN",
        "TX",
        "UT",
        "VT",
        "VA",
        "WA",
        "WV",
        "WI",
        "WY",
        "DC",
    }
)

_EIN_PATTERN = re.compile(r"^\d{2}-\d{7}$")


class CharityCategory(str, Enum):
    BUSINESS = "business"
    YOUTH = "youth"
    STEM = "stem"
    COMMUNITY = "community"
    CIVIC = "civic"
    EDUCATION = "education"
    ANIMAL_WELFARE = "animal_welfare"
    ARTS = "arts"
    SAFETY = "safety"
    WORKFORCE = "workforce"
    GRANTS = "grants"
    MULTI = "multi"


@dataclass(frozen=True)
class CharityOrganization:
    name: str
    category: CharityCategory
    state: str
    national_url: str
    is_501c3: bool
    chapter_name: str | None = None
    chapter_url: str | None = None
    donation_url: str | None = None
    accepts_points_donation: bool = False
    ein: str | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        if self.state not in VALID_US_STATES:
            raise ValueError(f"Invalid US state code: '{self.state}'")
        if self.ein is not None and not _EIN_PATTERN.match(self.ein):
            raise ValueError(f"Invalid EIN format: '{self.ein}' (expected XX-XXXXXXX)")


@dataclass
class CharityPartnerNetwork:
    charities: list[CharityOrganization] = field(default_factory=list)

    def by_state(self, state: str) -> list[CharityOrganization]:
        return [c for c in self.charities if c.state == state]

    def by_category(self, category: CharityCategory) -> list[CharityOrganization]:
        return [c for c in self.charities if c.category == category]

    def by_state_and_category(self, state: str, category: CharityCategory) -> list[CharityOrganization]:
        return [c for c in self.charities if c.state == state and c.category == category]

    def search(self, query: str) -> list[CharityOrganization]:
        q = query.lower()
        return [
            c for c in self.charities if q in " ".join(p.lower() for p in [c.name, c.chapter_name, c.description] if p)
        ]

    def states_covered(self) -> set[str]:
        return {c.state for c in self.charities}

    def categories_covered(self) -> set[CharityCategory]:
        return {c.category for c in self.charities}
