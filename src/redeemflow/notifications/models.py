"""Notifications domain — alert value objects."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AlertType(str, Enum):
    DEVALUATION = "devaluation"
    TRANSFER_BONUS = "transfer_bonus"
    EXPIRATION = "expiration"
    SWEET_SPOT = "sweet_spot"
    PRICE_DROP = "price_drop"


class AlertPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class Alert:
    """An alert for the user about a loyalty program event."""

    id: str
    alert_type: AlertType
    priority: AlertPriority
    title: str
    message: str
    program_code: str | None
    action_url: str | None
    created_at: str
    expires_at: str | None
