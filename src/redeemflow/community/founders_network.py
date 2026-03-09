"""Women Founders Travel Network — directory, verification, matching.

Beck: The simplest thing that could work.
Fowler: Mutable aggregate root (FounderProfile) for evolving membership state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


class FounderStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    ACTIVE = "active"
    SUSPENDED = "suspended"


@dataclass
class FounderProfile:
    """Mutable state holder — membership evolves through verification lifecycle."""

    user_id: str
    name: str
    email: str
    status: FounderStatus
    joined_at: str
    company_name: str | None = None
    industry: str | None = None
    verification_source: str | None = None
    bio: str | None = None
    travel_interests: list[str] = field(default_factory=list)
    is_mentor: bool = False
    mentor_topics: list[str] = field(default_factory=list)


class FounderDirectory:
    """Orchestrates founder membership — apply, verify, search, match."""

    def __init__(self, repository: object | None = None) -> None:
        self._repository = repository
        self._members: dict[str, FounderProfile] = {}

    def apply(
        self,
        user_id: str,
        name: str,
        email: str,
        company_name: str | None = None,
        verification_source: str | None = None,
        bio: str | None = None,
        travel_interests: list[str] | None = None,
    ) -> FounderProfile:
        now = datetime.now(UTC).isoformat()
        profile = FounderProfile(
            user_id=user_id,
            name=name,
            email=email,
            company_name=company_name,
            verification_source=verification_source,
            status=FounderStatus.PENDING,
            joined_at=now,
            bio=bio,
            travel_interests=travel_interests or [],
        )
        self._members[user_id] = profile
        if self._repository:
            self._repository.save(profile)
        return profile

    def verify(self, user_id: str) -> FounderProfile:
        profile = self._members.get(user_id)
        if profile is None:
            raise ValueError(f"Member not found: {user_id}")
        profile.status = FounderStatus.ACTIVE
        if self._repository:
            self._repository.save(profile)
        return profile

    def get_profile(self, user_id: str) -> FounderProfile | None:
        return self._members.get(user_id)

    def list_members(self, status: FounderStatus | None = None) -> list[FounderProfile]:
        members = list(self._members.values())
        if status is not None:
            members = [m for m in members if m.status == status]
        return members

    def search_members(self, query: str) -> list[FounderProfile]:
        if not query:
            return []
        q = query.lower()
        return [
            m for m in self._members.values() if q in m.name.lower() or (m.company_name and q in m.company_name.lower())
        ]

    def find_travel_companions(self, city: str) -> list[FounderProfile]:
        c = city.lower()
        return [m for m in self._members.values() if any(c == interest.lower() for interest in m.travel_interests)]

    def find_mentors(self, topic: str) -> list[FounderProfile]:
        t = topic.lower()
        return [m for m in self._members.values() if m.is_mentor and any(t == mt.lower() for mt in m.mentor_topics)]

    def update_profile(self, user_id: str, **kwargs: str | list[str] | bool | None) -> FounderProfile:
        profile = self._members.get(user_id)
        if profile is None:
            raise ValueError(f"Member not found: {user_id}")
        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        return profile
