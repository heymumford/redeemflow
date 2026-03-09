"""Contract tests — Stripe webhook payload parsing for subscription events."""

from __future__ import annotations

import pytest

from redeemflow.billing.stripe_adapter import FakePaymentProvider


class TestStripeWebhookContract:
    """Verify that webhook handler correctly processes Stripe event types.

    These are contract tests for the webhook interface: they define what
    event shapes we promise to handle and what responses consumers can expect.
    """

    @pytest.fixture
    def provider(self):
        return FakePaymentProvider()

    def test_checkout_session_completed(self, provider):
        result = provider.handle_webhook(
            event_type="checkout.session.completed",
            payload={
                "user_id": "auth0|eric",
                "tier": "premium",
                "stripe_subscription_id": "sub_abc123",
            },
        )
        assert result["status"] == "processed"
        assert "subscription" in result

    def test_customer_subscription_updated(self, provider):
        # First create a subscription
        provider.create_subscription(
            user_id="auth0|eric",
            tier_value="premium",
        )
        result = provider.handle_webhook(
            event_type="customer.subscription.updated",
            payload={
                "user_id": "auth0|eric",
                "status": "active",
                "stripe_subscription_id": "sub_abc123",
            },
        )
        assert result["status"] == "processed"

    def test_customer_subscription_deleted(self, provider):
        # First create a subscription
        sub = provider.create_subscription(
            user_id="auth0|eric",
            tier_value="premium",
        )
        result = provider.handle_webhook(
            event_type="customer.subscription.deleted",
            payload={
                "user_id": "auth0|eric",
                "subscription_id": sub.id,
            },
        )
        assert result["status"] == "processed"
        # Verify subscription was cancelled
        retrieved = provider.get_subscription("auth0|eric")
        assert retrieved is not None
        assert retrieved.status == "cancelled"

    def test_unknown_event_type_ignored(self, provider):
        result = provider.handle_webhook(
            event_type="payment_intent.created",
            payload={"id": "pi_123"},
        )
        assert result["status"] == "ignored"

    def test_checkout_invalid_tier_returns_error(self, provider):
        result = provider.handle_webhook(
            event_type="checkout.session.completed",
            payload={
                "user_id": "auth0|attacker",
                "tier": "hacker_tier",
            },
        )
        assert result["status"] == "error"
        assert "Invalid tier" in result["detail"]

    def test_webhook_response_always_has_status(self, provider):
        events = [
            ("checkout.session.completed", {"user_id": "u1", "tier": "free"}),
            ("customer.subscription.updated", {"user_id": "u2", "status": "active"}),
            ("customer.subscription.deleted", {"user_id": "u3", "subscription_id": "s1"}),
            ("charge.succeeded", {"id": "ch_123"}),
        ]
        for event_type, payload in events:
            result = provider.handle_webhook(event_type=event_type, payload=payload)
            assert "status" in result, f"Missing status in response for {event_type}"
