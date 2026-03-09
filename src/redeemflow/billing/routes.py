"""Billing API — subscription management endpoints.

All subscription endpoints require auth except webhooks.
Provider is stored on app.state by the application factory.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from redeemflow.billing.models import SubscriptionTier
from redeemflow.billing.stripe_adapter import PaymentProvider
from redeemflow.identity.auth import get_current_user
from redeemflow.identity.models import User

router = APIRouter()


def get_payment_provider(request: Request) -> PaymentProvider:
    return request.app.state.payment_provider


class SubscribeRequest(BaseModel):
    tier: SubscriptionTier


class WebhookRequest(BaseModel):
    type: str
    data: dict[str, Any]


@router.post("/api/billing/subscribe")
def subscribe(
    req: SubscribeRequest,
    user: User = Depends(get_current_user),
    provider: PaymentProvider = Depends(get_payment_provider),
):
    sub = provider.create_subscription(user_id=user.id, tier=req.tier)
    return {
        "subscription": {
            "id": sub.id,
            "tier": sub.tier.value,
            "status": sub.status,
            "current_period_start": sub.current_period_start,
            "current_period_end": sub.current_period_end,
        }
    }


@router.post("/api/billing/cancel")
def cancel(
    user: User = Depends(get_current_user),
    provider: PaymentProvider = Depends(get_payment_provider),
):
    sub = provider.get_subscription(user.id)
    if sub is None:
        raise HTTPException(status_code=404, detail="No active subscription")

    cancelled = provider.cancel_subscription(sub.id)
    return {
        "subscription": {
            "id": cancelled.id,
            "tier": cancelled.tier.value,
            "status": cancelled.status,
        }
    }


@router.post("/api/billing/webhook")
def webhook(
    req: WebhookRequest,
    provider: PaymentProvider = Depends(get_payment_provider),
):
    result = provider.handle_webhook(event_type=req.type, payload=req.data)
    return result


@router.get("/api/billing/subscription")
def get_subscription(
    user: User = Depends(get_current_user),
    provider: PaymentProvider = Depends(get_payment_provider),
):
    sub = provider.get_subscription(user.id)
    if sub is None:
        return {"subscription": None}

    return {
        "subscription": {
            "id": sub.id,
            "tier": sub.tier.value,
            "status": sub.status,
            "current_period_start": sub.current_period_start,
            "current_period_end": sub.current_period_end,
        }
    }
