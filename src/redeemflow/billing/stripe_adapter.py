"""Billing domain — Stripe payment provider Protocol and adapters.

PaymentProvider Protocol defines the port. StripeAdapter is the real implementation
(stubbed behind feature flag for now). FakePaymentProvider for tests.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, Protocol, runtime_checkable

from redeemflow.billing.models import Subscription, SubscriptionTier


@runtime_checkable
class PaymentProvider(Protocol):
    def create_subscription(
        self, user_id: str, tier: SubscriptionTier | None = None, **kwargs: Any
    ) -> Subscription: ...
    def cancel_subscription(self, subscription_id: str) -> Subscription: ...
    def handle_webhook(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]: ...
    def get_subscription(self, user_id: str) -> Subscription | None: ...


class StripeAdapter:
    """Real Stripe integration — stubbed for now, real calls behind feature flag."""

    def __init__(self, api_key: str, webhook_secret: str) -> None:
        self._api_key = api_key
        self._webhook_secret = webhook_secret

    def create_subscription(self, user_id: str, tier: SubscriptionTier | None = None, **kwargs: Any) -> Subscription:
        raise NotImplementedError("Real Stripe integration not yet enabled")

    def cancel_subscription(self, subscription_id: str) -> Subscription:
        raise NotImplementedError("Real Stripe integration not yet enabled")

    def handle_webhook(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("Real Stripe integration not yet enabled")

    def get_subscription(self, user_id: str) -> Subscription | None:
        raise NotImplementedError("Real Stripe integration not yet enabled")


class FakePaymentProvider:
    """In-memory payment provider for testing with deterministic behavior."""

    def __init__(self) -> None:
        self._subscriptions: dict[str, Subscription] = {}
        self._user_subscriptions: dict[str, str] = {}  # user_id -> subscription_id

    def create_subscription(self, user_id: str, tier: SubscriptionTier | None = None, **kwargs: Any) -> Subscription:
        # Support both 'tier' (SubscriptionTier) and 'tier_value' (str) for flexibility
        if tier is None:
            tier_value = kwargs.get("tier_value")
            if tier_value is not None:
                tier = SubscriptionTier(tier_value)
            else:
                tier = SubscriptionTier.FREE

        now = datetime.now(UTC)
        sub_id = f"sub_{uuid.uuid4().hex[:12]}"
        stripe_id = f"sub_stripe_{uuid.uuid4().hex[:8]}"

        sub = Subscription(
            id=sub_id,
            user_id=user_id,
            tier=tier,
            status="active",
            current_period_start=now.strftime("%Y-%m-%d"),
            current_period_end=now.strftime("%Y-%m-%d"),
            stripe_subscription_id=stripe_id,
        )
        self._subscriptions[sub_id] = sub
        self._user_subscriptions[user_id] = sub_id
        return sub

    def cancel_subscription(self, subscription_id: str) -> Subscription:
        existing = self._subscriptions.get(subscription_id)
        if existing is None:
            raise ValueError(f"Subscription {subscription_id} not found")

        cancelled = Subscription(
            id=existing.id,
            user_id=existing.user_id,
            tier=existing.tier,
            status="cancelled",
            current_period_start=existing.current_period_start,
            current_period_end=existing.current_period_end,
            stripe_subscription_id=existing.stripe_subscription_id,
        )
        self._subscriptions[subscription_id] = cancelled
        return cancelled

    def get_subscription(self, user_id: str) -> Subscription | None:
        sub_id = self._user_subscriptions.get(user_id)
        if sub_id is None:
            return None
        return self._subscriptions.get(sub_id)

    def handle_webhook(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        if event_type == "checkout.session.completed":
            user_id = payload.get("user_id", "unknown")
            tier_value = payload.get("tier", "free")
            try:
                tier = SubscriptionTier(tier_value)
            except ValueError:
                return {"status": "error", "detail": f"Invalid tier: {tier_value}"}
            sub = self.create_subscription(user_id=user_id, tier=tier)
            return {"status": "processed", "subscription": sub.id}

        if event_type == "customer.subscription.updated":
            user_id = payload.get("user_id")
            if user_id:
                sub = self.get_subscription(user_id)
                if sub:
                    return {"status": "processed", "subscription_id": sub.id}
            return {"status": "processed"}

        if event_type == "customer.subscription.deleted":
            user_id = payload.get("user_id")
            if user_id:
                sub = self.get_subscription(user_id)
                if sub:
                    self.cancel_subscription(sub.id)
                    return {"status": "processed", "subscription_id": sub.id}
            return {"status": "processed"}

        return {"status": "ignored"}
