"""Identity API — user profile and account management."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from redeemflow.identity.auth import get_current_user
from redeemflow.identity.models import User
from redeemflow.identity.profile import (
    DisplayCurrency,
    DistanceUnit,
    LinkedAccount,
    get_or_create_profile,
)

router = APIRouter()


class UpdateProfileRequest(BaseModel):
    display_name: str | None = None
    bio: str | None = None


class UpdatePreferencesRequest(BaseModel):
    home_airport: str | None = None
    display_currency: str | None = None
    distance_unit: str | None = None
    show_cash_prices: bool | None = None
    default_cabin: str | None = None
    favorite_programs: list[str] | None = None


class LinkAccountRequest(BaseModel):
    provider: str = "manual"
    program_code: str
    account_id: str
    display_name: str = ""


@router.get("/api/profile")
def get_profile(user: User = Depends(get_current_user)):
    """Get user profile with preferences and linked accounts."""
    profile = get_or_create_profile(user.id)
    return {
        **profile.summary(),
        "preferences": {
            "home_airport": profile.preferences.home_airport,
            "display_currency": profile.preferences.display_currency.value,
            "distance_unit": profile.preferences.distance_unit.value,
            "show_cash_prices": profile.preferences.show_cash_prices,
            "default_cabin": profile.preferences.default_cabin,
            "favorite_programs": profile.preferences.favorite_programs,
        },
        "linked_accounts": [
            {
                "provider": a.provider,
                "program_code": a.program_code,
                "account_id": a.account_id,
                "display_name": a.display_name,
                "linked_at": a.linked_at,
            }
            for a in profile.linked_accounts
        ],
    }


@router.put("/api/profile")
def update_profile(req: UpdateProfileRequest, user: User = Depends(get_current_user)):
    """Update profile display name and bio."""
    profile = get_or_create_profile(user.id)
    if req.display_name is not None:
        profile.display_name = req.display_name
    if req.bio is not None:
        profile.bio = req.bio
    return {"status": "updated", **profile.summary()}


@router.put("/api/profile/preferences")
def update_preferences(req: UpdatePreferencesRequest, user: User = Depends(get_current_user)):
    """Update display and calculation preferences."""
    profile = get_or_create_profile(user.id)
    updates: dict = {}

    if req.home_airport is not None:
        updates["home_airport"] = req.home_airport
    if req.display_currency is not None:
        try:
            updates["display_currency"] = DisplayCurrency(req.display_currency)
        except ValueError:
            return {"error": f"Invalid currency: {req.display_currency}"}
    if req.distance_unit is not None:
        try:
            updates["distance_unit"] = DistanceUnit(req.distance_unit)
        except ValueError:
            return {"error": f"Invalid unit: {req.distance_unit}"}
    if req.show_cash_prices is not None:
        updates["show_cash_prices"] = req.show_cash_prices
    if req.default_cabin is not None:
        updates["default_cabin"] = req.default_cabin
    if req.favorite_programs is not None:
        updates["favorite_programs"] = req.favorite_programs

    prefs = profile.update_preferences(**updates)
    return {
        "status": "updated",
        "preferences": {
            "home_airport": prefs.home_airport,
            "display_currency": prefs.display_currency.value,
            "distance_unit": prefs.distance_unit.value,
            "show_cash_prices": prefs.show_cash_prices,
            "default_cabin": prefs.default_cabin,
            "favorite_programs": prefs.favorite_programs,
        },
    }


@router.post("/api/profile/accounts")
def link_account(req: LinkAccountRequest, user: User = Depends(get_current_user)):
    """Link a loyalty program account."""
    from datetime import UTC, datetime

    profile = get_or_create_profile(user.id)
    account = LinkedAccount(
        provider=req.provider,
        program_code=req.program_code,
        account_id=req.account_id,
        display_name=req.display_name,
        linked_at=datetime.now(UTC).isoformat(),
    )
    profile.link_account(account)
    return {"status": "linked", "linked_accounts_count": len(profile.linked_accounts)}


@router.delete("/api/profile/accounts/{program_code}/{account_id}")
def unlink_account(program_code: str, account_id: str, user: User = Depends(get_current_user)):
    """Unlink a loyalty program account."""
    profile = get_or_create_profile(user.id)
    removed = profile.unlink_account(program_code, account_id)
    return {"status": "unlinked" if removed else "not_found"}
