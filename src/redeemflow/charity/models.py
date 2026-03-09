"""Charity partner network domain — value objects and state holder.

Beck: The simplest thing that could work.
Fowler: Value objects are immutable. State holders are mutable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


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
        results = []
        for c in self.charities:
            searchable = c.name.lower()
            if c.chapter_name:
                searchable += " " + c.chapter_name.lower()
            if c.description:
                searchable += " " + c.description.lower()
            if q in searchable:
                results.append(c)
        return results

    def states_covered(self) -> set[str]:
        return {c.state for c in self.charities}

    def categories_covered(self) -> set[CharityCategory]:
        return {c.category for c in self.charities}
