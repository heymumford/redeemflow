"""Tests for webhook event processing — idempotency, deduplication, event log."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from redeemflow.billing.webhook_processor import (
    WebhookEventLog,
    WebhookEventStatus,
    process_webhook_event,
)


class TestWebhookEventLog:
    def test_receive_new_event(self):
        log = WebhookEventLog()
        event = log.receive("evt_001", "checkout.session.completed", "stripe", {"user_id": "u1"})
        assert event.event_id == "evt_001"
        assert event.status == WebhookEventStatus.RECEIVED
        assert event.idempotency_key == "stripe:evt_001"

    def test_receive_duplicate_returns_duplicate_status(self):
        log = WebhookEventLog()
        log.receive("evt_001", "checkout.session.completed", "stripe", {"user_id": "u1"})
        dup = log.receive("evt_001", "checkout.session.completed", "stripe", {"user_id": "u1"})
        assert dup.status == WebhookEventStatus.DUPLICATE

    def test_is_duplicate(self):
        log = WebhookEventLog()
        assert log.is_duplicate("evt_001") is False
        log.receive("evt_001", "test", "stripe", {})
        assert log.is_duplicate("evt_001") is True

    def test_mark_processing(self):
        log = WebhookEventLog()
        log.receive("evt_001", "test", "stripe", {})
        event = log.mark_processing("evt_001")
        assert event is not None
        assert event.status == WebhookEventStatus.PROCESSING

    def test_mark_processing_missing_returns_none(self):
        log = WebhookEventLog()
        assert log.mark_processing("nonexistent") is None

    def test_mark_processed(self):
        log = WebhookEventLog()
        log.receive("evt_001", "test", "stripe", {})
        event = log.mark_processed("evt_001")
        assert event is not None
        assert event.status == WebhookEventStatus.PROCESSED
        assert event.processed_at is not None

    def test_mark_failed(self):
        log = WebhookEventLog()
        log.receive("evt_001", "test", "stripe", {})
        event = log.mark_failed("evt_001", "Connection timeout")
        assert event is not None
        assert event.status == WebhookEventStatus.FAILED
        assert event.error_message == "Connection timeout"

    def test_get_event(self):
        log = WebhookEventLog()
        log.receive("evt_001", "test", "stripe", {"key": "val"})
        event = log.get("evt_001")
        assert event is not None
        assert event.payload == {"key": "val"}

    def test_get_missing_returns_none(self):
        log = WebhookEventLog()
        assert log.get("nonexistent") is None

    def test_list_events_default(self):
        log = WebhookEventLog()
        log.receive("evt_001", "test", "stripe", {})
        log.receive("evt_002", "test", "manual", {})
        events = log.list_events()
        assert len(events) == 2

    def test_list_events_filter_by_status(self):
        log = WebhookEventLog()
        log.receive("evt_001", "test", "stripe", {})
        log.receive("evt_002", "test", "stripe", {})
        log.mark_processed("evt_001")
        events = log.list_events(status=WebhookEventStatus.PROCESSED)
        assert len(events) == 1
        assert events[0].event_id == "evt_001"

    def test_list_events_filter_by_source(self):
        log = WebhookEventLog()
        log.receive("evt_001", "test", "stripe", {})
        log.receive("evt_002", "test", "manual", {})
        events = log.list_events(source="stripe")
        assert len(events) == 1

    def test_list_events_respects_limit(self):
        log = WebhookEventLog()
        for i in range(10):
            log.receive(f"evt_{i:03d}", "test", "stripe", {})
        events = log.list_events(limit=3)
        assert len(events) == 3

    def test_failed_events(self):
        log = WebhookEventLog()
        log.receive("evt_001", "test", "stripe", {})
        log.receive("evt_002", "test", "stripe", {})
        log.mark_failed("evt_001", "error")
        failed = log.failed_events()
        assert len(failed) == 1
        assert failed[0].event_id == "evt_001"

    def test_total_and_processed_counts(self):
        log = WebhookEventLog()
        log.receive("evt_001", "test", "stripe", {})
        log.receive("evt_002", "test", "stripe", {})
        log.mark_processed("evt_001")
        assert log.total_count == 2
        assert log.processed_count == 1


class TestProcessWebhookEvent:
    def _make_handler(self):
        from redeemflow.billing.stripe_adapter import FakePaymentProvider

        return FakePaymentProvider()

    def test_processes_new_event(self):
        log = WebhookEventLog()
        handler = self._make_handler()
        result = process_webhook_event(
            log,
            handler,
            "evt_001",
            "checkout.session.completed",
            "stripe",
            {"user_id": "u1", "tier": "premium"},
        )
        assert result["status"] == "processed"
        assert result["event_id"] == "evt_001"

    def test_duplicate_event_not_reprocessed(self):
        log = WebhookEventLog()
        handler = self._make_handler()
        process_webhook_event(
            log,
            handler,
            "evt_001",
            "checkout.session.completed",
            "stripe",
            {"user_id": "u1", "tier": "premium"},
        )
        result = process_webhook_event(
            log,
            handler,
            "evt_001",
            "checkout.session.completed",
            "stripe",
            {"user_id": "u1", "tier": "premium"},
        )
        assert result["status"] == "duplicate"

    def test_unknown_event_type_still_logged(self):
        log = WebhookEventLog()
        handler = self._make_handler()
        result = process_webhook_event(
            log,
            handler,
            "evt_002",
            "unknown.event",
            "stripe",
            {},
        )
        assert result["status"] == "processed"
        assert log.get("evt_002").status == WebhookEventStatus.PROCESSED

    def test_handler_failure_marks_failed(self):
        log = WebhookEventLog()

        class BrokenHandler:
            def handle_webhook(self, event_type, payload):
                raise RuntimeError("Connection refused")

        result = process_webhook_event(
            log,
            BrokenHandler(),
            "evt_003",
            "test",
            "stripe",
            {},
        )
        assert result["status"] == "failed"
        assert "Connection refused" in result["error"]
        assert log.get("evt_003").status == WebhookEventStatus.FAILED

    def test_no_handler_method(self):
        log = WebhookEventLog()
        result = process_webhook_event(
            log,
            object(),
            "evt_004",
            "test",
            "stripe",
            {},
        )
        assert result["status"] == "processed"
        assert result["result"]["status"] == "no_handler"


class TestWebhookAPIEndpoints:
    AUTH_HEADERS = {"Authorization": "Bearer test-token-eric"}

    @pytest.fixture
    def client(self):
        from redeemflow.app import create_app
        from redeemflow.ports import PortBundle

        return TestClient(create_app(ports=PortBundle()))

    def test_idempotent_webhook_processes(self, client):
        resp = client.post(
            "/api/billing/webhook/idempotent",
            json={
                "event_id": "evt_test_001",
                "event_type": "checkout.session.completed",
                "source": "stripe",
                "data": {"user_id": "u1", "tier": "premium"},
            },
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "processed"

    def test_idempotent_webhook_deduplicates(self, client):
        payload = {
            "event_id": "evt_test_dup",
            "event_type": "checkout.session.completed",
            "source": "stripe",
            "data": {"user_id": "u1", "tier": "premium"},
        }
        client.post("/api/billing/webhook/idempotent", json=payload)
        resp = client.post("/api/billing/webhook/idempotent", json=payload)
        assert resp.status_code == 200
        assert resp.json()["status"] == "duplicate"

    def test_list_events_requires_auth(self, client):
        resp = client.get("/api/billing/webhook/events")
        assert resp.status_code == 401

    def test_list_events_returns_events(self, client):
        client.post(
            "/api/billing/webhook/idempotent",
            json={
                "event_id": "evt_list_test",
                "event_type": "test",
                "source": "test",
                "data": {},
            },
        )
        resp = client.get("/api/billing/webhook/events", headers=self.AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "events" in data
        assert data["total"] >= 1

    def test_list_events_filter_by_status(self, client):
        resp = client.get(
            "/api/billing/webhook/events",
            params={"status": "processed"},
            headers=self.AUTH_HEADERS,
        )
        assert resp.status_code == 200

    def test_list_events_invalid_status(self, client):
        resp = client.get(
            "/api/billing/webhook/events",
            params={"status": "bogus"},
            headers=self.AUTH_HEADERS,
        )
        assert resp.status_code == 200
        assert "error" in resp.json()
