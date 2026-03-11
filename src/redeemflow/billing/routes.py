"""Billing API — subscription management endpoints.

All subscription endpoints require auth except webhooks.
Provider is stored on app.state by the application factory.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from redeemflow.billing.models import SubscriptionTier
from redeemflow.billing.stripe_adapter import PaymentProvider, StripeAdapter
from redeemflow.billing.webhook_processor import WebhookEventLog, process_webhook_event
from redeemflow.identity.auth import get_current_user
from redeemflow.identity.models import User

router = APIRouter()


def get_payment_provider(request: Request) -> PaymentProvider:
    return request.app.state.payment_provider


def get_webhook_log(request: Request) -> WebhookEventLog:
    if not hasattr(request.app.state, "webhook_event_log"):
        request.app.state.webhook_event_log = WebhookEventLog()
    return request.app.state.webhook_event_log


class SubscribeRequest(BaseModel):
    tier: SubscriptionTier


class CheckoutRequest(BaseModel):
    tier: SubscriptionTier
    success_url: str = "https://redeemflow.com/billing/success"
    cancel_url: str = "https://redeemflow.com/billing/cancel"


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


@router.post("/api/billing/checkout")
def create_checkout(
    req: CheckoutRequest,
    user: User = Depends(get_current_user),
    provider: PaymentProvider = Depends(get_payment_provider),
):
    """Create a Stripe Checkout Session for subscription signup.

    Only available when real Stripe adapter is configured.
    With FakePaymentProvider, falls back to direct subscription creation.
    """
    if isinstance(provider, StripeAdapter):
        result = provider.create_checkout_session(
            user_id=user.id,
            tier=req.tier,
            success_url=req.success_url,
            cancel_url=req.cancel_url,
        )
        return result

    # Fake provider: create subscription directly (no checkout flow)
    sub = provider.create_subscription(user_id=user.id, tier=req.tier)
    return {
        "session_id": f"fake_cs_{sub.id}",
        "checkout_url": None,
        "subscription_id": sub.id,
    }


@router.post("/api/billing/webhook")
def webhook(
    req: WebhookRequest,
    provider: PaymentProvider = Depends(get_payment_provider),
):
    result = provider.handle_webhook(event_type=req.type, payload=req.data)
    return result


@router.post("/api/billing/webhook/stripe")
async def stripe_webhook(
    request: Request,
    provider: PaymentProvider = Depends(get_payment_provider),
):
    """Stripe webhook with signature verification.

    Reads raw body and Stripe-Signature header for verification.
    Only functional when StripeAdapter is configured.
    """
    if not isinstance(provider, StripeAdapter):
        raise HTTPException(status_code=501, detail="Stripe webhooks require Stripe configuration")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    try:
        result = provider.handle_webhook_signed(payload=payload, sig_header=sig_header)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook verification failed: {e}") from e


class IdempotentWebhookRequest(BaseModel):
    event_id: str
    event_type: str
    source: str = "stripe"
    data: dict[str, Any] = {}


@router.post("/api/billing/webhook/idempotent")
def idempotent_webhook(
    req: IdempotentWebhookRequest,
    provider: PaymentProvider = Depends(get_payment_provider),
    event_log: WebhookEventLog = Depends(get_webhook_log),
):
    """Process webhook with idempotency — duplicate events return original result."""
    result = process_webhook_event(
        event_log=event_log,
        handler=provider,
        event_id=req.event_id,
        event_type=req.event_type,
        source=req.source,
        payload=req.data,
    )
    return result


@router.get("/api/billing/webhook/events")
def list_webhook_events(
    status: str | None = None,
    source: str | None = None,
    limit: int = 50,
    user: User = Depends(get_current_user),
    event_log: WebhookEventLog = Depends(get_webhook_log),
):
    """List webhook events — admin endpoint for observability."""
    from redeemflow.billing.webhook_processor import WebhookEventStatus

    status_filter = None
    if status is not None:
        try:
            status_filter = WebhookEventStatus(status)
        except ValueError:
            return {"error": f"Invalid status: {status}"}

    events = event_log.list_events(status=status_filter, source=source, limit=limit)
    return {
        "events": [
            {
                "event_id": e.event_id,
                "event_type": e.event_type,
                "source": e.source,
                "status": e.status.value,
                "received_at": e.received_at,
                "processed_at": e.processed_at,
                "error_message": e.error_message,
            }
            for e in events
        ],
        "total": event_log.total_count,
        "processed": event_log.processed_count,
    }


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
