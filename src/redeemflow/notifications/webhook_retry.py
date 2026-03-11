"""Webhook retry — exponential backoff, dead letter queue, delivery tracking.

Beck: Retry is a policy — inputs are attempt history, output is next action.
Fowler: State Machine — pending → delivering → delivered | failed | dead_letter.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


class DeliveryStatus(str, Enum):
    PENDING = "pending"
    DELIVERING = "delivering"
    DELIVERED = "delivered"
    RETRYING = "retrying"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


@dataclass(frozen=True)
class RetryPolicy:
    """Configurable retry policy."""

    max_retries: int = 5
    initial_delay_seconds: int = 1
    backoff_multiplier: int = 2
    max_delay_seconds: int = 3600  # 1 hour cap

    def delay_for_attempt(self, attempt: int) -> int:
        """Compute delay in seconds for a given attempt (0-based)."""
        delay = self.initial_delay_seconds * (self.backoff_multiplier**attempt)
        return min(delay, self.max_delay_seconds)

    def should_retry(self, attempt: int) -> bool:
        return attempt < self.max_retries


DEFAULT_POLICY = RetryPolicy()


@dataclass(frozen=True)
class DeliveryAttempt:
    """Record of a single delivery attempt."""

    attempt_number: int
    timestamp: str
    status_code: int = 0
    error: str = ""
    duration_ms: int = 0


@dataclass
class WebhookDelivery:
    """Tracks delivery of a single webhook event."""

    delivery_id: str
    webhook_id: str
    event_type: str
    payload: str
    target_url: str
    status: DeliveryStatus = DeliveryStatus.PENDING
    attempts: list[DeliveryAttempt] = field(default_factory=list)
    created_at: str = ""
    completed_at: str = ""
    next_retry_at: str = ""
    policy: RetryPolicy = field(default_factory=lambda: DEFAULT_POLICY)

    def record_attempt(self, status_code: int = 0, error: str = "", duration_ms: int = 0) -> DeliveryAttempt:
        """Record a delivery attempt and update status."""
        attempt = DeliveryAttempt(
            attempt_number=len(self.attempts) + 1,
            timestamp=datetime.now(UTC).isoformat(),
            status_code=status_code,
            error=error,
            duration_ms=duration_ms,
        )
        self.attempts.append(attempt)

        if 200 <= status_code < 300:
            self.status = DeliveryStatus.DELIVERED
            self.completed_at = attempt.timestamp
        elif self.policy.should_retry(len(self.attempts)):
            self.status = DeliveryStatus.RETRYING
            delay = self.policy.delay_for_attempt(len(self.attempts) - 1)
            self.next_retry_at = f"+{delay}s"
        else:
            self.status = DeliveryStatus.DEAD_LETTER
            self.completed_at = attempt.timestamp

        return attempt

    def summary(self) -> dict:
        return {
            "delivery_id": self.delivery_id,
            "webhook_id": self.webhook_id,
            "event_type": self.event_type,
            "target_url": self.target_url,
            "status": self.status.value,
            "attempt_count": len(self.attempts),
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "next_retry_at": self.next_retry_at,
        }


@dataclass
class DeliveryQueue:
    """Manages webhook delivery queue with dead letter support."""

    _deliveries: dict[str, WebhookDelivery] = field(default_factory=dict)
    _counter: int = 0

    def enqueue(
        self,
        webhook_id: str,
        event_type: str,
        payload: str,
        target_url: str,
        policy: RetryPolicy | None = None,
    ) -> WebhookDelivery:
        """Add a delivery to the queue."""
        self._counter += 1
        delivery_id = f"dlv-{self._counter}"
        delivery = WebhookDelivery(
            delivery_id=delivery_id,
            webhook_id=webhook_id,
            event_type=event_type,
            payload=payload,
            target_url=target_url,
            created_at=datetime.now(UTC).isoformat(),
            policy=policy or DEFAULT_POLICY,
        )
        self._deliveries[delivery_id] = delivery
        return delivery

    def get_delivery(self, delivery_id: str) -> WebhookDelivery | None:
        return self._deliveries.get(delivery_id)

    def pending_deliveries(self) -> list[WebhookDelivery]:
        """Get deliveries that need processing."""
        return [d for d in self._deliveries.values() if d.status in (DeliveryStatus.PENDING, DeliveryStatus.RETRYING)]

    def dead_letters(self) -> list[WebhookDelivery]:
        """Get deliveries that exhausted retries."""
        return [d for d in self._deliveries.values() if d.status == DeliveryStatus.DEAD_LETTER]

    def delivery_stats(self) -> dict:
        """Get delivery statistics."""
        statuses = [d.status for d in self._deliveries.values()]
        return {
            "total": len(statuses),
            "pending": statuses.count(DeliveryStatus.PENDING),
            "delivering": statuses.count(DeliveryStatus.DELIVERING),
            "delivered": statuses.count(DeliveryStatus.DELIVERED),
            "retrying": statuses.count(DeliveryStatus.RETRYING),
            "failed": statuses.count(DeliveryStatus.FAILED),
            "dead_letter": statuses.count(DeliveryStatus.DEAD_LETTER),
            "success_rate": (
                round(statuses.count(DeliveryStatus.DELIVERED) / len(statuses) * 100, 1) if statuses else 0
            ),
        }

    def replay_dead_letter(self, delivery_id: str) -> WebhookDelivery | None:
        """Re-enqueue a dead letter for retry."""
        delivery = self._deliveries.get(delivery_id)
        if delivery is None or delivery.status != DeliveryStatus.DEAD_LETTER:
            return None
        delivery.status = DeliveryStatus.RETRYING
        delivery.attempts.clear()
        delivery.completed_at = ""
        delivery.next_retry_at = ""
        return delivery


# Singleton
_DELIVERY_QUEUE = DeliveryQueue()


def get_delivery_queue() -> DeliveryQueue:
    return _DELIVERY_QUEUE


def reset_delivery_queue() -> None:
    global _DELIVERY_QUEUE
    _DELIVERY_QUEUE = DeliveryQueue()
