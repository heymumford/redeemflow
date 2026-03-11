"""Admin API — system metrics, audit log, and observability endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from redeemflow.admin.audit import AuditAction, get_audit_log
from redeemflow.admin.metrics import collect_program_metrics, collect_system_metrics
from redeemflow.identity.auth import get_current_user
from redeemflow.identity.models import User
from redeemflow.optimization.seed_data import ALL_PARTNERS
from redeemflow.search.sweet_spots import ALL_SWEET_SPOTS
from redeemflow.valuations.seed_data import PROGRAM_VALUATIONS

router = APIRouter()


@router.get("/api/admin/metrics")
def system_metrics(request: Request, user: User = Depends(get_current_user)):
    """System-wide metrics dashboard."""
    webhook_log = getattr(request.app.state, "webhook_event_log", None)

    metrics = collect_system_metrics(
        programs=list(PROGRAM_VALUATIONS.values()),
        transfer_partners=ALL_PARTNERS,
        sweet_spots=ALL_SWEET_SPOTS,
        webhook_log=webhook_log,
    )

    return {
        "timestamp": metrics.timestamp,
        "programs": {
            "total": metrics.total_programs,
            "avg_cpp": str(metrics.avg_program_valuation_cpp),
        },
        "transfer_network": {
            "total_partners": metrics.total_transfer_partners,
            "total_sweet_spots": metrics.total_sweet_spots,
        },
        "webhooks": {
            "total": metrics.webhook_events_total,
            "processed": metrics.webhook_events_processed,
            "failed": metrics.webhook_events_failed,
        },
        "notifications": {
            "active_channels": metrics.active_notification_channels,
        },
    }


@router.get("/api/admin/programs")
def program_metrics(user: User = Depends(get_current_user)):
    """Per-program metrics breakdown."""
    metrics = collect_program_metrics(
        programs=list(PROGRAM_VALUATIONS.values()),
        transfer_partners=ALL_PARTNERS,
        sweet_spots=ALL_SWEET_SPOTS,
    )

    return {
        "programs": [
            {
                "code": m.program_code,
                "name": m.program_name,
                "cpp": str(m.cpp_value),
                "transfer_partners": m.transfer_partner_count,
                "sweet_spots": m.sweet_spot_count,
                "has_hotel_transfers": m.has_hotel_transfers,
            }
            for m in metrics
        ],
    }


@router.get("/api/admin/audit")
def audit_log_view(
    user: User = Depends(get_current_user),
    action: str | None = None,
    resource_type: str | None = None,
    limit: int = 50,
):
    """Query the audit log with optional filters."""
    log = get_audit_log()

    audit_action = None
    if action:
        try:
            audit_action = AuditAction(action)
        except ValueError:
            return {"error": f"Invalid action: {action}", "valid": [a.value for a in AuditAction]}

    entries = log.query(
        user_id=user.id,
        action=audit_action,
        resource_type=resource_type,
        limit=limit,
    )
    return {
        "entries": [
            {
                "entry_id": e.entry_id,
                "timestamp": e.timestamp,
                "action": e.action.value,
                "resource_type": e.resource_type,
                "resource_id": e.resource_id,
                "detail": e.detail,
            }
            for e in entries
        ],
        "count": len(entries),
    }


@router.get("/api/admin/audit/summary")
def audit_summary(user: User = Depends(get_current_user)):
    """Audit log summary with action counts."""
    log = get_audit_log()
    summary = log.summarize()
    return {
        "total_entries": summary.total_entries,
        "unique_users": summary.unique_users,
        "action_counts": summary.action_counts,
        "recent": [
            {
                "entry_id": e.entry_id,
                "timestamp": e.timestamp,
                "user_id": e.user_id,
                "action": e.action.value,
                "resource_type": e.resource_type,
                "resource_id": e.resource_id,
            }
            for e in summary.recent_entries
        ],
    }
