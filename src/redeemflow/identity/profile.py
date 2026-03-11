"""User profile management — preferences, display settings, linked accounts.

Beck: Profile is mutable state owned by the user.
Fowler: Aggregate root — profile owns preferences and linked accounts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class DisplayCurrency(str, Enum):
    USD = "usd"
    EUR = "eur"
    GBP = "gbp"
    CAD = "cad"
    AUD = "aud"
    JPY = "jpy"


class DistanceUnit(str, Enum):
    MILES = "miles"
    KILOMETERS = "kilometers"


@dataclass(frozen=True)
class LinkedAccount:
    """A connected loyalty program account."""

    provider: str  # "awardwallet", "manual"
    program_code: str
    account_id: str
    display_name: str
    linked_at: str


@dataclass(frozen=True)
class UserPreferences:
    """Display and calculation preferences."""

    home_airport: str = ""
    display_currency: DisplayCurrency = DisplayCurrency.USD
    distance_unit: DistanceUnit = DistanceUnit.MILES
    show_cash_prices: bool = True
    default_cabin: str = "economy"
    favorite_programs: list[str] = field(default_factory=list)


@dataclass
class UserProfile:
    """Mutable user profile aggregate."""

    user_id: str
    display_name: str = ""
    bio: str = ""
    preferences: UserPreferences = field(default_factory=UserPreferences)
    linked_accounts: list[LinkedAccount] = field(default_factory=list)

    def update_preferences(self, **kwargs: object) -> UserPreferences:
        """Update preferences, returning new frozen object."""
        current = self.preferences
        updates = {}
        for k, v in kwargs.items():
            if hasattr(current, k) and v is not None:
                updates[k] = v
        self.preferences = UserPreferences(
            home_airport=updates.get("home_airport", current.home_airport),
            display_currency=updates.get("display_currency", current.display_currency),
            distance_unit=updates.get("distance_unit", current.distance_unit),
            show_cash_prices=updates.get("show_cash_prices", current.show_cash_prices),
            default_cabin=updates.get("default_cabin", current.default_cabin),
            favorite_programs=updates.get("favorite_programs", current.favorite_programs),
        )
        return self.preferences

    def link_account(self, account: LinkedAccount) -> None:
        """Add a linked loyalty account."""
        # Prevent duplicates by program_code + account_id
        for existing in self.linked_accounts:
            if existing.program_code == account.program_code and existing.account_id == account.account_id:
                return
        self.linked_accounts.append(account)

    def unlink_account(self, program_code: str, account_id: str) -> bool:
        """Remove a linked account. Returns True if found and removed."""
        before = len(self.linked_accounts)
        self.linked_accounts = [
            a for a in self.linked_accounts if not (a.program_code == program_code and a.account_id == account_id)
        ]
        return len(self.linked_accounts) < before

    def summary(self) -> dict:
        """Profile summary for API response."""
        return {
            "user_id": self.user_id,
            "display_name": self.display_name,
            "bio": self.bio,
            "home_airport": self.preferences.home_airport,
            "display_currency": self.preferences.display_currency.value,
            "distance_unit": self.preferences.distance_unit.value,
            "linked_accounts_count": len(self.linked_accounts),
            "favorite_programs": self.preferences.favorite_programs,
        }


# In-memory profile store
_PROFILES: dict[str, UserProfile] = {}


def get_or_create_profile(user_id: str) -> UserProfile:
    """Get existing profile or create default."""
    if user_id not in _PROFILES:
        _PROFILES[user_id] = UserProfile(user_id=user_id)
    return _PROFILES[user_id]


def get_profile(user_id: str) -> UserProfile | None:
    """Get profile if it exists."""
    return _PROFILES.get(user_id)
