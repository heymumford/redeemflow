"""Billing domain — Stripe payment provider Protocol and adapters.

PaymentProvider Protocol defines the port. StripeAdapter wraps the real Stripe SDK.
FakePaymentProvider provides deterministic in-memory behavior for tests.

Beck: Protocol boundary — both sides satisfy the same contract.
Fowler: Strangler Fig — env var toggles real vs fake, zero route changes.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, Protocol, runtime_checkable

import stripe

from redeemflow.billing.models import Subscription, SubscriptionTier
from redeemflow.middleware.logging import get_logger

logger = get_logger("billing")

# Stripe price IDs — set via environment or overridden in tests.
# These map our tier enum to Stripe Price objects.
TIER_PRICE_MAP: dict[SubscriptionTier, str] = {
    SubscriptionTier.PREMIUM: "price_premium_monthly",
    SubscriptionTier.PRO: "price_pro_monthly",
}


@runtime_checkable
class PaymentProvider(Protocol):
    def create_subscription(
        self, user_id: str, tier: SubscriptionTier | None = None, **kwargs: Any
    ) -> Subscription: ...
    def cancel_subscription(self, subscription_id: str) -> Subscription: ...
    def handle_webhook(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]: ...
    def get_subscription(self, user_id: str) -> Subscription | None: ...


def _timestamp_to_date(ts: int) -> str:
    """Convert Unix timestamp to ISO date string."""
    return datetime.fromtimestamp(ts, tz=UTC).strftime("%Y-%m-%d")


class StripeAdapter:
    """Real Stripe integration — wraps stripe SDK for subscription lifecycle.

    Maintains a local cache of subscription mappings so we can translate
    between our internal IDs and Stripe's subscription IDs.
    """

    def __init__(self, api_key: str, webhook_secret: str) -> None:
        self._api_key = api_key
        self._webhook_secret = webhook_secret
        stripe.api_key = api_key
        self._subscriptions: dict[str, Subscription] = {}
        self._user_subscriptions: dict[str, str] = {}  # user_id -> internal sub_id

    def _get_or_create_customer(self, user_id: str) -> str:
        """Find existing Stripe customer by metadata or create one."""
        customers = stripe.Customer.list(limit=1, email=None, metadata={"user_id": user_id})
        if customers.data:
            return customers.data[0].id

        customer = stripe.Customer.create(metadata={"user_id": user_id})
        return customer.id

    def create_subscription(self, user_id: str, tier: SubscriptionTier | None = None, **kwargs: Any) -> Subscription:
        if tier is None:
            tier = SubscriptionTier.FREE

        customer_id = self._get_or_create_customer(user_id)
        price_id = TIER_PRICE_MAP.get(tier)
        if not price_id:
            raise ValueError(f"No Stripe price configured for tier: {tier.value}")

        stripe_sub = stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price_id}],
            metadata={"user_id": user_id, "tier": tier.value},
        )

        sub_id = f"sub_{uuid.uuid4().hex[:12]}"
        sub = Subscription(
            id=sub_id,
            user_id=user_id,
            tier=tier,
            status="active" if stripe_sub.status == "active" else stripe_sub.status,
            current_period_start=_timestamp_to_date(stripe_sub.current_period_start),
            current_period_end=_timestamp_to_date(stripe_sub.current_period_end),
            stripe_subscription_id=stripe_sub.id,
        )
        self._subscriptions[sub_id] = sub
        self._user_subscriptions[user_id] = sub_id

        logger.info(
            "subscription_created",
            user_id=user_id,
            tier=tier.value,
            stripe_sub_id=stripe_sub.id,
        )
        return sub

    def cancel_subscription(self, subscription_id: str) -> Subscription:
        existing = self._subscriptions.get(subscription_id)
        if existing is None:
            raise ValueError(f"Subscription {subscription_id} not found")

        stripe.Subscription.modify(
            existing.stripe_subscription_id,
            cancel_at_period_end=True,
        )

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

        logger.info(
            "subscription_cancelled",
            subscription_id=subscription_id,
            stripe_sub_id=existing.stripe_subscription_id,
        )
        return cancelled

    def get_subscription(self, user_id: str) -> Subscription | None:
        sub_id = self._user_subscriptions.get(user_id)
        if sub_id is None:
            return None
        return self._subscriptions.get(sub_id)

    def handle_webhook(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Process webhook from parsed event data (no signature verification)."""
        return self._process_event(event_type, payload)

    def handle_webhook_signed(self, payload: bytes, sig_header: str) -> dict[str, Any]:
        """Process webhook with Stripe signature verification."""
        event = stripe.Webhook.construct_event(payload, sig_header, self._webhook_secret)
        event_data = event.data.object if hasattr(event.data, "object") else {}
        metadata = event_data.get("metadata", {}) if isinstance(event_data, dict) else {}
        return self._process_event(event.type, metadata)

    def _process_event(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Route webhook events to handlers."""
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

        logger.info("webhook_ignored", event_type=event_type)
        return {"status": "ignored"}

    def create_checkout_session(
        self,
        user_id: str,
        tier: SubscriptionTier,
        success_url: str,
        cancel_url: str,
    ) -> dict[str, str]:
        """Create a Stripe Checkout Session for subscription signup."""
        price_id = TIER_PRICE_MAP.get(tier)
        if not price_id:
            raise ValueError(f"No Stripe price configured for tier: {tier.value}")

        customer_id = self._get_or_create_customer(user_id)

        session = stripe.checkout.Session.create(
            customer=customer_id,
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"user_id": user_id, "tier": tier.value},
        )

        logger.info(
            "checkout_session_created",
            user_id=user_id,
            tier=tier.value,
            session_id=session.id,
        )
        return {"session_id": session.id, "checkout_url": session.url}


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
