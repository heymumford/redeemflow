"""Webhook event processing — idempotent event log with deduplication.

Fowler: Event Sourcing lite — log every inbound event, process exactly once.
Beck: Separation of concerns — receipt vs processing vs notification.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


class WebhookEventStatus(str, Enum):
    RECEIVED = "received"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    DUPLICATE = "duplicate"


@dataclass(frozen=True)
class WebhookEvent:
    """Immutable record of a received webhook event."""

    event_id: str
    event_type: str
    source: str  # "stripe", "manual", "test"
    payload: dict
    received_at: str
    status: WebhookEventStatus = WebhookEventStatus.RECEIVED
    processed_at: str | None = None
    error_message: str | None = None
    idempotency_key: str | None = None


@dataclass
class WebhookEventLog:
    """In-memory event log with deduplication and status tracking.

    Production would back this with a database table.
    """

    _events: dict[str, WebhookEvent] = field(default_factory=dict)
    _processed_keys: set[str] = field(default_factory=set)

    def receive(self, event_id: str, event_type: str, source: str, payload: dict) -> WebhookEvent:
        """Record a received webhook event. Returns DUPLICATE if already seen."""
        if event_id in self._events:
            existing = self._events[event_id]
            return WebhookEvent(
                event_id=existing.event_id,
                event_type=existing.event_type,
                source=existing.source,
                payload=existing.payload,
                received_at=existing.received_at,
                status=WebhookEventStatus.DUPLICATE,
                processed_at=existing.processed_at,
                idempotency_key=existing.idempotency_key,
            )

        now = datetime.now(UTC).isoformat()
        event = WebhookEvent(
            event_id=event_id,
            event_type=event_type,
            source=source,
            payload=payload,
            received_at=now,
            idempotency_key=f"{source}:{event_id}",
        )
        self._events[event_id] = event
        return event

    def mark_processing(self, event_id: str) -> WebhookEvent | None:
        """Mark event as in-progress. Returns None if not found."""
        event = self._events.get(event_id)
        if event is None:
            return None

        updated = WebhookEvent(
            event_id=event.event_id,
            event_type=event.event_type,
            source=event.source,
            payload=event.payload,
            received_at=event.received_at,
            status=WebhookEventStatus.PROCESSING,
            idempotency_key=event.idempotency_key,
        )
        self._events[event_id] = updated
        return updated

    def mark_processed(self, event_id: str) -> WebhookEvent | None:
        """Mark event as successfully processed."""
        event = self._events.get(event_id)
        if event is None:
            return None

        now = datetime.now(UTC).isoformat()
        updated = WebhookEvent(
            event_id=event.event_id,
            event_type=event.event_type,
            source=event.source,
            payload=event.payload,
            received_at=event.received_at,
            status=WebhookEventStatus.PROCESSED,
            processed_at=now,
            idempotency_key=event.idempotency_key,
        )
        self._events[event_id] = updated
        self._processed_keys.add(event.idempotency_key or event_id)
        return updated

    def mark_failed(self, event_id: str, error: str) -> WebhookEvent | None:
        """Mark event as failed with error message."""
        event = self._events.get(event_id)
        if event is None:
            return None

        now = datetime.now(UTC).isoformat()
        updated = WebhookEvent(
            event_id=event.event_id,
            event_type=event.event_type,
            source=event.source,
            payload=event.payload,
            received_at=event.received_at,
            status=WebhookEventStatus.FAILED,
            processed_at=now,
            error_message=error,
            idempotency_key=event.idempotency_key,
        )
        self._events[event_id] = updated
        return updated

    def get(self, event_id: str) -> WebhookEvent | None:
        """Retrieve event by ID."""
        return self._events.get(event_id)

    def list_events(
        self,
        status: WebhookEventStatus | None = None,
        source: str | None = None,
        limit: int = 50,
    ) -> list[WebhookEvent]:
        """List events with optional filtering."""
        events = list(self._events.values())

        if status is not None:
            events = [e for e in events if e.status == status]
        if source is not None:
            events = [e for e in events if e.source == source]

        # Most recent first
        events.sort(key=lambda e: e.received_at, reverse=True)
        return events[:limit]

    def is_duplicate(self, event_id: str) -> bool:
        """Check if event has already been received."""
        return event_id in self._events

    def failed_events(self) -> list[WebhookEvent]:
        """Get all failed events for retry consideration."""
        return self.list_events(status=WebhookEventStatus.FAILED)

    @property
    def total_count(self) -> int:
        return len(self._events)

    @property
    def processed_count(self) -> int:
        return len(self._processed_keys)


def process_webhook_event(
    event_log: WebhookEventLog,
    handler: object,
    event_id: str,
    event_type: str,
    source: str,
    payload: dict,
) -> dict:
    """Process a webhook event through the log with idempotency.

    1. Receive (dedup check)
    2. Mark processing
    3. Delegate to handler
    4. Mark processed or failed
    """
    event = event_log.receive(event_id, event_type, source, payload)

    if event.status == WebhookEventStatus.DUPLICATE:
        return {
            "status": "duplicate",
            "event_id": event_id,
            "original_status": event_log.get(event_id).status.value if event_log.get(event_id) else "unknown",
        }

    event_log.mark_processing(event_id)

    try:
        if hasattr(handler, "handle_webhook"):
            result = handler.handle_webhook(event_type=event_type, payload=payload)
        else:
            result = {"status": "no_handler"}

        event_log.mark_processed(event_id)
        return {
            "status": "processed",
            "event_id": event_id,
            "result": result,
        }
    except Exception as exc:
        event_log.mark_failed(event_id, str(exc))
        return {
            "status": "failed",
            "event_id": event_id,
            "error": str(exc),
        }
