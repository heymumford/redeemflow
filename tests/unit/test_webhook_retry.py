"""Tests for webhook retry with exponential backoff."""

from __future__ import annotations

from redeemflow.notifications.webhook_retry import (
    DeliveryQueue,
    DeliveryStatus,
    RetryPolicy,
    WebhookDelivery,
)


class TestRetryPolicy:
    def test_default_policy(self):
        p = RetryPolicy()
        assert p.max_retries == 5
        assert p.initial_delay_seconds == 1
        assert p.backoff_multiplier == 2

    def test_delay_exponential(self):
        p = RetryPolicy(initial_delay_seconds=1, backoff_multiplier=2)
        assert p.delay_for_attempt(0) == 1
        assert p.delay_for_attempt(1) == 2
        assert p.delay_for_attempt(2) == 4
        assert p.delay_for_attempt(3) == 8

    def test_delay_capped(self):
        p = RetryPolicy(initial_delay_seconds=1, backoff_multiplier=2, max_delay_seconds=10)
        assert p.delay_for_attempt(10) == 10

    def test_should_retry(self):
        p = RetryPolicy(max_retries=3)
        assert p.should_retry(0) is True
        assert p.should_retry(2) is True
        assert p.should_retry(3) is False
        assert p.should_retry(5) is False


class TestWebhookDelivery:
    def _make_delivery(self, policy: RetryPolicy | None = None) -> WebhookDelivery:
        return WebhookDelivery(
            delivery_id="dlv-1",
            webhook_id="wh-1",
            event_type="balance.updated",
            payload='{"points": 1000}',
            target_url="https://example.com/webhook",
            policy=policy or RetryPolicy(max_retries=3),
        )

    def test_successful_delivery(self):
        d = self._make_delivery()
        d.record_attempt(status_code=200, duration_ms=50)
        assert d.status == DeliveryStatus.DELIVERED
        assert d.completed_at != ""

    def test_failed_then_retry(self):
        d = self._make_delivery()
        d.record_attempt(status_code=500, error="Internal Server Error")
        assert d.status == DeliveryStatus.RETRYING
        assert d.next_retry_at.startswith("+")

    def test_exhausted_retries(self):
        d = self._make_delivery(RetryPolicy(max_retries=2))
        d.record_attempt(status_code=500, error="fail 1")
        d.record_attempt(status_code=500, error="fail 2")
        assert d.status == DeliveryStatus.DEAD_LETTER
        assert d.completed_at != ""

    def test_success_after_retry(self):
        d = self._make_delivery()
        d.record_attempt(status_code=500, error="fail")
        d.record_attempt(status_code=200, duration_ms=30)
        assert d.status == DeliveryStatus.DELIVERED
        assert len(d.attempts) == 2

    def test_summary(self):
        d = self._make_delivery()
        s = d.summary()
        assert s["delivery_id"] == "dlv-1"
        assert s["status"] == "pending"
        assert s["attempt_count"] == 0


class TestDeliveryQueue:
    def test_enqueue(self):
        q = DeliveryQueue()
        d = q.enqueue("wh-1", "balance.updated", "{}", "https://example.com/hook")
        assert d.delivery_id == "dlv-1"
        assert d.status == DeliveryStatus.PENDING

    def test_get_delivery(self):
        q = DeliveryQueue()
        d = q.enqueue("wh-1", "test", "{}", "https://example.com")
        assert q.get_delivery(d.delivery_id) is d
        assert q.get_delivery("nope") is None

    def test_pending_deliveries(self):
        q = DeliveryQueue()
        d1 = q.enqueue("wh-1", "test", "{}", "https://example.com")
        d2 = q.enqueue("wh-2", "test", "{}", "https://example.com")
        d1.record_attempt(status_code=200)
        pending = q.pending_deliveries()
        assert len(pending) == 1
        assert pending[0].delivery_id == d2.delivery_id

    def test_dead_letters(self):
        q = DeliveryQueue()
        d = q.enqueue("wh-1", "test", "{}", "https://example.com", RetryPolicy(max_retries=1))
        d.record_attempt(status_code=500)
        assert len(q.dead_letters()) == 1

    def test_delivery_stats(self):
        q = DeliveryQueue()
        d1 = q.enqueue("wh-1", "test", "{}", "https://example.com")
        q.enqueue("wh-2", "test", "{}", "https://example.com")
        d1.record_attempt(status_code=200)
        stats = q.delivery_stats()
        assert stats["total"] == 2
        assert stats["delivered"] == 1
        assert stats["pending"] == 1
        assert stats["success_rate"] == 50.0

    def test_replay_dead_letter(self):
        q = DeliveryQueue()
        d = q.enqueue("wh-1", "test", "{}", "https://example.com", RetryPolicy(max_retries=1))
        d.record_attempt(status_code=500)
        assert d.status == DeliveryStatus.DEAD_LETTER
        replayed = q.replay_dead_letter(d.delivery_id)
        assert replayed is not None
        assert replayed.status == DeliveryStatus.RETRYING
        assert len(replayed.attempts) == 0

    def test_replay_non_dead_letter(self):
        q = DeliveryQueue()
        d = q.enqueue("wh-1", "test", "{}", "https://example.com")
        assert q.replay_dead_letter(d.delivery_id) is None

    def test_replay_nonexistent(self):
        q = DeliveryQueue()
        assert q.replay_dead_letter("nope") is None

    def test_empty_stats(self):
        q = DeliveryQueue()
        stats = q.delivery_stats()
        assert stats["total"] == 0
        assert stats["success_rate"] == 0
