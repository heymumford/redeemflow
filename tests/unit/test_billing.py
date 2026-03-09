"""Sprint 2: Billing domain — subscription tiers, plans, and Stripe integration."""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from redeemflow.app import create_app
from redeemflow.billing.models import (
    PREMIUM_PLAN,
    PRO_PLAN,
    Subscription,
    SubscriptionTier,
)
from redeemflow.billing.stripe_adapter import FakePaymentProvider, PaymentProvider


class TestSubscriptionTier:
    def test_free_tier_exists(self):
        assert SubscriptionTier.FREE.value == "free"

    def test_premium_tier_exists(self):
        assert SubscriptionTier.PREMIUM.value == "premium"

    def test_pro_tier_exists(self):
        assert SubscriptionTier.PRO.value == "pro"

    def test_tier_values_are_strings(self):
        for tier in SubscriptionTier:
            assert isinstance(tier.value, str)


class TestSubscriptionPlan:
    def test_premium_plan_monthly_price(self):
        assert PREMIUM_PLAN.monthly_price == Decimal("9.99")

    def test_premium_plan_annual_price(self):
        assert PREMIUM_PLAN.annual_price == Decimal("99.99")

    def test_pro_plan_monthly_price(self):
        assert PRO_PLAN.monthly_price == Decimal("24.99")

    def test_pro_plan_annual_price(self):
        assert PRO_PLAN.annual_price == Decimal("249.99")

    def test_plan_is_frozen(self):
        with pytest.raises(AttributeError):
            PREMIUM_PLAN.monthly_price = Decimal("0")

    def test_premium_plan_has_features(self):
        assert len(PREMIUM_PLAN.features) > 0

    def test_pro_plan_has_features(self):
        assert len(PRO_PLAN.features) > 0

    def test_premium_plan_tier(self):
        assert PREMIUM_PLAN.tier == SubscriptionTier.PREMIUM

    def test_pro_plan_tier(self):
        assert PRO_PLAN.tier == SubscriptionTier.PRO

    def test_annual_savings_over_monthly(self):
        premium_annual_if_monthly = PREMIUM_PLAN.monthly_price * 12
        assert PREMIUM_PLAN.annual_price < premium_annual_if_monthly

        pro_annual_if_monthly = PRO_PLAN.monthly_price * 12
        assert PRO_PLAN.annual_price < pro_annual_if_monthly


class TestSubscription:
    def test_subscription_is_frozen(self):
        sub = Subscription(
            id="sub_123",
            user_id="auth0|eric",
            tier=SubscriptionTier.PREMIUM,
            status="active",
            current_period_start="2026-03-01",
            current_period_end="2026-04-01",
            stripe_subscription_id="sub_stripe_123",
        )
        with pytest.raises(AttributeError):
            sub.status = "cancelled"

    def test_subscription_active_status(self):
        sub = Subscription(
            id="sub_123",
            user_id="auth0|eric",
            tier=SubscriptionTier.PREMIUM,
            status="active",
            current_period_start="2026-03-01",
            current_period_end="2026-04-01",
            stripe_subscription_id="sub_stripe_123",
        )
        assert sub.status == "active"

    def test_subscription_cancelled_status(self):
        sub = Subscription(
            id="sub_456",
            user_id="auth0|eric",
            tier=SubscriptionTier.PRO,
            status="cancelled",
            current_period_start="2026-03-01",
            current_period_end="2026-04-01",
            stripe_subscription_id="sub_stripe_456",
        )
        assert sub.status == "cancelled"

    def test_subscription_past_due_status(self):
        sub = Subscription(
            id="sub_789",
            user_id="auth0|eric",
            tier=SubscriptionTier.PREMIUM,
            status="past_due",
            current_period_start="2026-03-01",
            current_period_end="2026-04-01",
            stripe_subscription_id="sub_stripe_789",
        )
        assert sub.status == "past_due"

    def test_subscription_requires_all_fields(self):
        sub = Subscription(
            id="sub_100",
            user_id="auth0|steve",
            tier=SubscriptionTier.FREE,
            status="active",
            current_period_start="2026-01-01",
            current_period_end="2026-02-01",
        )
        assert sub.stripe_subscription_id is None


class TestFakePaymentProvider:
    def test_implements_protocol(self):
        provider = FakePaymentProvider()
        assert isinstance(provider, PaymentProvider)

    def test_create_subscription(self):
        provider = FakePaymentProvider()
        sub = provider.create_subscription(
            user_id="auth0|eric",
            tier=SubscriptionTier.PREMIUM,
        )
        assert sub.user_id == "auth0|eric"
        assert sub.tier == SubscriptionTier.PREMIUM
        assert sub.status == "active"
        assert sub.stripe_subscription_id is not None

    def test_cancel_subscription(self):
        provider = FakePaymentProvider()
        sub = provider.create_subscription(
            user_id="auth0|eric",
            tier=SubscriptionTier.PREMIUM,
        )
        cancelled = provider.cancel_subscription(sub.id)
        assert cancelled.status == "cancelled"
        assert cancelled.user_id == sub.user_id

    def test_cancel_nonexistent_raises(self):
        provider = FakePaymentProvider()
        with pytest.raises(ValueError, match="not found"):
            provider.cancel_subscription("nonexistent")

    def test_handle_webhook_checkout_completed(self):
        provider = FakePaymentProvider()
        result = provider.handle_webhook(
            event_type="checkout.session.completed",
            payload={"user_id": "auth0|eric", "tier": "premium"},
        )
        assert result["status"] == "processed"

    def test_handle_webhook_unknown_event(self):
        provider = FakePaymentProvider()
        result = provider.handle_webhook(
            event_type="unknown.event",
            payload={},
        )
        assert result["status"] == "ignored"

    def test_get_subscription(self):
        provider = FakePaymentProvider()
        sub = provider.create_subscription(
            user_id="auth0|eric",
            tier=SubscriptionTier.PRO,
        )
        retrieved = provider.get_subscription(sub.user_id)
        assert retrieved is not None
        assert retrieved.id == sub.id

    def test_get_subscription_nonexistent(self):
        provider = FakePaymentProvider()
        assert provider.get_subscription("auth0|nobody") is None


class TestBillingRoutes:
    @pytest.fixture
    def client(self):
        app = create_app()
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self):
        return {"Authorization": "Bearer test-token-eric"}

    def test_subscribe_requires_auth(self, client):
        response = client.post("/api/billing/subscribe", json={"tier": "premium"})
        assert response.status_code == 401

    def test_subscribe_creates_subscription(self, client, auth_headers):
        response = client.post(
            "/api/billing/subscribe",
            json={"tier": "premium"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["subscription"]["tier"] == "premium"
        assert data["subscription"]["status"] == "active"

    def test_subscribe_invalid_tier(self, client, auth_headers):
        response = client.post(
            "/api/billing/subscribe",
            json={"tier": "diamond"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_get_subscription_status(self, client, auth_headers):
        # First subscribe
        client.post(
            "/api/billing/subscribe",
            json={"tier": "premium"},
            headers=auth_headers,
        )
        # Then check status
        response = client.get("/api/billing/subscription", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["subscription"]["tier"] == "premium"

    def test_get_subscription_none(self, client, auth_headers):
        response = client.get("/api/billing/subscription", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["subscription"] is None

    def test_cancel_subscription(self, client, auth_headers):
        # Subscribe first
        client.post(
            "/api/billing/subscribe",
            json={"tier": "pro"},
            headers=auth_headers,
        )
        # Cancel
        response = client.post("/api/billing/cancel", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["subscription"]["status"] == "cancelled"

    def test_cancel_no_subscription(self, client, auth_headers):
        response = client.post("/api/billing/cancel", headers=auth_headers)
        assert response.status_code == 404

    def test_webhook_endpoint(self, client):
        response = client.post(
            "/api/billing/webhook",
            json={
                "type": "checkout.session.completed",
                "data": {"user_id": "auth0|eric", "tier": "premium"},
            },
        )
        assert response.status_code == 200

    def test_cancel_requires_auth(self, client):
        response = client.post("/api/billing/cancel")
        assert response.status_code == 401

    def test_subscription_status_requires_auth(self, client):
        response = client.get("/api/billing/subscription")
        assert response.status_code == 401

    def test_checkout_with_fake_provider(self, client, auth_headers):
        """Checkout endpoint falls back to direct subscription with fake provider."""
        response = client.post(
            "/api/billing/checkout",
            json={"tier": "premium"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["checkout_url"] is None  # Fake has no Stripe URL
        assert "subscription_id" in data

    def test_checkout_requires_auth(self, client):
        response = client.post("/api/billing/checkout", json={"tier": "premium"})
        assert response.status_code == 401

    def test_checkout_invalid_tier(self, client, auth_headers):
        response = client.post(
            "/api/billing/checkout",
            json={"tier": "diamond"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_stripe_webhook_requires_stripe_config(self, client):
        """Signed webhook returns 501 when using fake provider."""
        response = client.post(
            "/api/billing/webhook/stripe",
            content=b'{"type":"test"}',
            headers={"stripe-signature": "t=1,v1=abc"},
        )
        assert response.status_code == 501

    def test_stripe_webhook_missing_signature(self, client):
        """Signed webhook requires Stripe-Signature header."""
        # Even without Stripe config, 501 comes first
        response = client.post(
            "/api/billing/webhook/stripe",
            content=b'{"type":"test"}',
        )
        assert response.status_code == 501
