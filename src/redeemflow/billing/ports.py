"""Billing domain — ports (Protocol interfaces).

BillingPort defines the contract for subscription lifecycle management.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from redeemflow.billing.models import Subscription, SubscriptionTier


@runtime_checkable
class BillingPort(Protocol):
    """Port for subscription lifecycle: create, cancel, webhook, lookup."""

    def create_subscription(
        self, user_id: str, tier: SubscriptionTier | None = None, **kwargs: Any
    ) -> Subscription: ...

    def cancel_subscription(self, subscription_id: str) -> Subscription: ...

    def handle_webhook(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]: ...

    def get_subscription(self, user_id: str) -> Subscription | None: ...
