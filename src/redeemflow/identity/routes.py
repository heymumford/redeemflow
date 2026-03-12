"""Identity API — user profile and account management."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from redeemflow.identity.api_keys import get_api_key_store
from redeemflow.identity.auth import get_current_user
from redeemflow.identity.models import User
from redeemflow.identity.onboarding import (
    OnboardingProfile,
    ProgramSelection,
    TravelStyle,
    complete_onboarding,
)
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
            return JSONResponse(status_code=400, content={"detail": f"Invalid currency: {req.display_currency}"})
    if req.distance_unit is not None:
        try:
            updates["distance_unit"] = DistanceUnit(req.distance_unit)
        except ValueError:
            return JSONResponse(status_code=400, content={"detail": f"Invalid unit: {req.distance_unit}"})
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


# ---------------------------------------------------------------------------
# API Key management
# ---------------------------------------------------------------------------


class CreateKeyRequest(BaseModel):
    name: str
    scopes: list[str] = ["read"]
    expires_at: str = ""


def _serialize_key(key) -> dict:
    return {
        "key_id": key.key_id,
        "name": key.name,
        "prefix": key.prefix,
        "user_id": key.user_id,
        "created_at": key.created_at,
        "expires_at": key.expires_at,
        "is_active": key.is_active,
        "last_used_at": key.last_used_at,
        "scopes": key.scopes,
    }


@router.post("/api/keys")
def create_api_key(req: CreateKeyRequest, user: User = Depends(get_current_user)):
    """Create a new API key. Returns the raw key only once."""
    store = get_api_key_store()
    raw_key, key = store.create_key(
        user_id=user.id,
        name=req.name,
        scopes=req.scopes,
        expires_at=req.expires_at,
    )
    return {"raw_key": raw_key, "key": _serialize_key(key)}


@router.get("/api/keys")
def list_api_keys(user: User = Depends(get_current_user)):
    """List all API keys for the current user."""
    store = get_api_key_store()
    keys = store.list_keys(user.id)
    return {"keys": [_serialize_key(k) for k in keys]}


@router.delete("/api/keys/{key_id}")
def revoke_api_key(key_id: str, user: User = Depends(get_current_user)):
    """Revoke an API key."""
    store = get_api_key_store()
    revoked = store.revoke_key(key_id, user.id)
    if revoked is None:
        return JSONResponse(status_code=404, content={"detail": "Key not found"})
    return {"key": _serialize_key(revoked)}


# ---------------------------------------------------------------------------
# Onboarding
# ---------------------------------------------------------------------------


class ProgramInput(BaseModel):
    program_code: str
    estimated_balance: int = 0
    is_primary: bool = False


class OnboardingRequest(BaseModel):
    programs: list[ProgramInput]
    travel_style: str = "comfort"
    home_airport: str = ""
    preferred_cabins: list[str] = []
    travel_frequency: int = 4
    interested_in_hotels: bool = True
    interested_in_flights: bool = True


@router.post("/api/onboarding/complete")
def onboarding_complete(req: OnboardingRequest, user: User = Depends(get_current_user)):
    """Complete onboarding and get personalized setup recommendations."""
    try:
        style = TravelStyle(req.travel_style)
    except ValueError:
        style = TravelStyle.COMFORT

    programs = [
        ProgramSelection(
            program_code=p.program_code,
            estimated_balance=p.estimated_balance,
            is_primary=p.is_primary,
        )
        for p in req.programs
    ]

    profile = OnboardingProfile(
        travel_style=style,
        home_airport=req.home_airport,
        preferred_cabins=req.preferred_cabins,
        travel_frequency=req.travel_frequency,
        interested_in_hotels=req.interested_in_hotels,
        interested_in_flights=req.interested_in_flights,
    )

    report = complete_onboarding(user.id, programs, profile)
    return {
        "current_step": report.current_step.value,
        "programs": [
            {
                "program_code": p.program_code,
                "estimated_balance": p.estimated_balance,
                "is_primary": p.is_primary,
            }
            for p in report.programs
        ],
        "suggested_goals": [
            {
                "goal_name": g.goal_name,
                "program_code": g.program_code,
                "target_points": g.target_points,
                "estimated_value": str(g.estimated_value),
                "category": g.category,
                "rationale": g.rationale,
            }
            for g in report.suggested_goals
        ],
        "quick_wins": report.quick_wins,
        "next_actions": report.next_actions,
        "estimated_portfolio_value": str(report.estimated_portfolio_value),
        "completed_at": report.completed_at,
    }
