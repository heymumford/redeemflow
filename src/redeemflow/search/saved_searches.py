"""Saved searches — persist and replay award search criteria.

Beck: Saved search is a value object — criteria in, stored search out.
Fowler: In-memory store with singleton pattern, replaceable in tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class SearchCriteria:
    """Immutable award search parameters."""

    origin: str
    destination: str
    cabin: str = "economy"
    programs: list[str] = field(default_factory=list)
    max_points: int | None = None
    direct_only: bool = False


@dataclass(frozen=True)
class SavedSearch:
    """A persisted search with metadata."""

    search_id: str
    user_id: str
    name: str
    criteria: SearchCriteria
    created_at: str
    last_run_at: str = ""
    run_count: int = 0
    is_active: bool = True
    alert_on_change: bool = False


@dataclass
class SavedSearchStore:
    """In-memory store for saved searches."""

    _searches: dict[str, SavedSearch] = field(default_factory=dict)
    _counter: int = 0

    def save(
        self,
        user_id: str,
        name: str,
        criteria: SearchCriteria,
        alert_on_change: bool = False,
    ) -> SavedSearch:
        """Save a new search."""
        self._counter += 1
        search_id = f"ss-{self._counter}"
        search = SavedSearch(
            search_id=search_id,
            user_id=user_id,
            name=name,
            criteria=criteria,
            created_at=datetime.now(UTC).isoformat(),
            alert_on_change=alert_on_change,
        )
        self._searches[search_id] = search
        return search

    def list_searches(self, user_id: str) -> list[SavedSearch]:
        """List all active saved searches for a user."""
        return [s for s in self._searches.values() if s.user_id == user_id and s.is_active]

    def get(self, search_id: str) -> SavedSearch | None:
        """Get a saved search by ID."""
        return self._searches.get(search_id)

    def record_run(self, search_id: str) -> SavedSearch | None:
        """Record that a saved search was executed."""
        search = self._searches.get(search_id)
        if search is None or not search.is_active:
            return None
        updated = SavedSearch(
            search_id=search.search_id,
            user_id=search.user_id,
            name=search.name,
            criteria=search.criteria,
            created_at=search.created_at,
            last_run_at=datetime.now(UTC).isoformat(),
            run_count=search.run_count + 1,
            is_active=search.is_active,
            alert_on_change=search.alert_on_change,
        )
        self._searches[search_id] = updated
        return updated

    def delete(self, search_id: str, user_id: str) -> SavedSearch | None:
        """Soft-delete a saved search (deactivate)."""
        search = self._searches.get(search_id)
        if search is None or search.user_id != user_id:
            return None
        deactivated = SavedSearch(
            search_id=search.search_id,
            user_id=search.user_id,
            name=search.name,
            criteria=search.criteria,
            created_at=search.created_at,
            last_run_at=search.last_run_at,
            run_count=search.run_count,
            is_active=False,
            alert_on_change=search.alert_on_change,
        )
        self._searches[search_id] = deactivated
        return deactivated

    def update_name(self, search_id: str, user_id: str, new_name: str) -> SavedSearch | None:
        """Rename a saved search."""
        search = self._searches.get(search_id)
        if search is None or search.user_id != user_id or not search.is_active:
            return None
        renamed = SavedSearch(
            search_id=search.search_id,
            user_id=search.user_id,
            name=new_name,
            criteria=search.criteria,
            created_at=search.created_at,
            last_run_at=search.last_run_at,
            run_count=search.run_count,
            is_active=search.is_active,
            alert_on_change=search.alert_on_change,
        )
        self._searches[search_id] = renamed
        return renamed

    def alert_searches(self, user_id: str) -> list[SavedSearch]:
        """List searches with alerts enabled."""
        return [s for s in self._searches.values() if s.user_id == user_id and s.is_active and s.alert_on_change]

    def stats(self, user_id: str) -> dict:
        """Usage statistics for a user's saved searches."""
        user_searches = [s for s in self._searches.values() if s.user_id == user_id]
        active = [s for s in user_searches if s.is_active]
        total_runs = sum(s.run_count for s in user_searches)
        alert_count = sum(1 for s in active if s.alert_on_change)
        return {
            "total_saved": len(user_searches),
            "active": len(active),
            "total_runs": total_runs,
            "alerts_enabled": alert_count,
        }


_STORE: SavedSearchStore | None = None


def get_saved_search_store() -> SavedSearchStore:
    """Get the singleton saved search store."""
    global _STORE
    if _STORE is None:
        _STORE = SavedSearchStore()
    return _STORE


def reset_saved_search_store() -> None:
    """Reset the store (for testing)."""
    global _STORE
    _STORE = None
