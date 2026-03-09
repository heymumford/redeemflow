"""Contract tests — PaymentProvider protocol conformance.

Both FakePaymentProvider and StripeAdapter must satisfy the same
PaymentProvider Protocol contract. Stripe API calls are mocked
so these run without credentials.

Beck: Test the contract, not the wiring.
Fowler: Both sides of the adapter boundary prove they keep their promises.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from redeemflow.billing.models import Subscription, SubscriptionTier
from redeemflow.billing.stripe_adapter import (
    FakePaymentProvider,
    PaymentProvider,
    StripeAdapter,
)


@pytest.fixture()
def fake_provider():
    return FakePaymentProvider()


@pytest.fixture()
def stripe_provider():
    return StripeAdapter(api_key="sk_test_fake123", webhook_secret="whsec_test_fake")


class TestProtocolConformance:
    """Both adapters satisfy PaymentProvider Protocol."""

    def test_fake_is_payment_provider(self, fake_provider):
        assert isinstance(fake_provider, PaymentProvider)

    def test_stripe_is_payment_provider(self, stripe_provider):
        assert isinstance(stripe_provider, PaymentProvider)


class TestCreateSubscription:
    """create_subscription returns a valid Subscription."""

    def test_fake_creates_subscription(self, fake_provider):
        sub = fake_provider.create_subscription(user_id="user-1", tier=SubscriptionTier.PREMIUM)
        assert isinstance(sub, Subscription)
        assert sub.user_id == "user-1"
        assert sub.tier == SubscriptionTier.PREMIUM
        assert sub.status == "active"

    @patch("stripe.Subscription.create")
    @patch("stripe.Customer.list")
    def test_stripe_creates_subscription(self, mock_list, mock_create, stripe_provider):
        mock_list.return_value = MagicMock(data=[MagicMock(id="cus_123")])
        mock_create.return_value = MagicMock(
            id="sub_stripe_abc",
            status="active",
            current_period_start=1700000000,
            current_period_end=1702592000,
        )
        sub = stripe_provider.create_subscription(user_id="user-1", tier=SubscriptionTier.PREMIUM)
        assert isinstance(sub, Subscription)
        assert sub.user_id == "user-1"
        assert sub.tier == SubscriptionTier.PREMIUM
        assert sub.status == "active"
        assert sub.stripe_subscription_id == "sub_stripe_abc"


class TestCancelSubscription:
    """cancel_subscription returns Subscription with status 'cancelled'."""

    def test_fake_cancels(self, fake_provider):
        sub = fake_provider.create_subscription(user_id="user-1", tier=SubscriptionTier.PREMIUM)
        cancelled = fake_provider.cancel_subscription(sub.id)
        assert cancelled.status == "cancelled"
        assert cancelled.id == sub.id

    @patch("stripe.Subscription.modify")
    def test_stripe_cancels(self, mock_modify, stripe_provider):
        mock_modify.return_value = MagicMock(
            id="sub_stripe_abc",
            status="canceled",
            current_period_start=1700000000,
            current_period_end=1702592000,
        )
        # Seed internal mapping so cancel can find the subscription
        stripe_provider._subscriptions["sub-1"] = Subscription(
            id="sub-1",
            user_id="user-1",
            tier=SubscriptionTier.PREMIUM,
            status="active",
            current_period_start="2024-01-01",
            current_period_end="2024-02-01",
            stripe_subscription_id="sub_stripe_abc",
        )
        cancelled = stripe_provider.cancel_subscription("sub-1")
        assert cancelled.status == "cancelled"
        mock_modify.assert_called_once_with("sub_stripe_abc", cancel_at_period_end=True)


class TestGetSubscription:
    """get_subscription returns Subscription or None."""

    def test_fake_returns_none_for_unknown(self, fake_provider):
        assert fake_provider.get_subscription("nonexistent") is None

    def test_fake_returns_subscription_after_create(self, fake_provider):
        sub = fake_provider.create_subscription(user_id="user-1", tier=SubscriptionTier.FREE)
        found = fake_provider.get_subscription("user-1")
        assert found is not None
        assert found.id == sub.id

    @patch("stripe.Subscription.retrieve")
    def test_stripe_returns_subscription(self, mock_retrieve, stripe_provider):
        mock_retrieve.return_value = MagicMock(
            id="sub_stripe_abc",
            status="active",
            current_period_start=1700000000,
            current_period_end=1702592000,
        )
        stripe_provider._user_subscriptions["user-1"] = "sub-1"
        stripe_provider._subscriptions["sub-1"] = Subscription(
            id="sub-1",
            user_id="user-1",
            tier=SubscriptionTier.PREMIUM,
            status="active",
            current_period_start="2024-01-01",
            current_period_end="2024-02-01",
            stripe_subscription_id="sub_stripe_abc",
        )
        found = stripe_provider.get_subscription("user-1")
        assert found is not None
        assert found.stripe_subscription_id == "sub_stripe_abc"

    def test_stripe_returns_none_for_unknown(self, stripe_provider):
        assert stripe_provider.get_subscription("nonexistent") is None


class TestWebhookHandling:
    """handle_webhook processes Stripe event types."""

    def test_fake_checkout_completed(self, fake_provider):
        result = fake_provider.handle_webhook(
            "checkout.session.completed",
            {"user_id": "user-1", "tier": "premium"},
        )
        assert result["status"] == "processed"

    @patch("stripe.Subscription.create")
    @patch("stripe.Customer.list")
    @patch("stripe.Webhook.construct_event")
    def test_stripe_webhook_signature_verified(self, mock_construct, mock_cust_list, mock_sub_create, stripe_provider):
        """Stripe adapter verifies webhook signatures before processing."""
        mock_construct.return_value = MagicMock(
            type="checkout.session.completed",
            data=MagicMock(object={"metadata": {"user_id": "user-1", "tier": "premium"}}),
        )
        mock_cust_list.return_value = MagicMock(data=[MagicMock(id="cus_123")])
        mock_sub_create.return_value = MagicMock(
            id="sub_stripe_wh",
            status="active",
            current_period_start=1700000000,
            current_period_end=1702592000,
        )
        result = stripe_provider.handle_webhook_signed(
            payload=b'{"type": "checkout.session.completed"}',
            sig_header="t=123,v1=abc",
        )
        assert result["status"] == "processed"
        mock_construct.assert_called_once()

    def test_fake_ignores_unknown_event(self, fake_provider):
        result = fake_provider.handle_webhook("unknown.event", {})
        assert result["status"] == "ignored"


class TestCheckoutSession:
    """Stripe checkout session creation for subscription flow."""

    @patch("stripe.checkout.Session.create")
    @patch("stripe.Customer.create")
    @patch("stripe.Customer.list")
    def test_create_checkout_session(self, mock_list, mock_cust_create, mock_session, stripe_provider):
        mock_list.return_value = MagicMock(data=[])
        mock_cust_create.return_value = MagicMock(id="cus_new_123")
        mock_session.return_value = MagicMock(
            id="cs_test_abc",
            url="https://checkout.stripe.com/pay/cs_test_abc",
        )
        result = stripe_provider.create_checkout_session(
            user_id="user-1",
            tier=SubscriptionTier.PREMIUM,
            success_url="https://redeemflow.com/success",
            cancel_url="https://redeemflow.com/cancel",
        )
        assert "checkout_url" in result
        assert "session_id" in result
        assert result["session_id"] == "cs_test_abc"
        mock_cust_create.assert_called_once()
