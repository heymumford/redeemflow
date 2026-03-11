"""Admin metrics — system health and business observability.

Beck: Metrics as data, not side effects. Pure functions from state to numbers.
Fowler: Build metrics that tell you if the system is healthy, not just alive.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal


@dataclass(frozen=True)
class SystemMetrics:
    """Snapshot of system health indicators."""

    timestamp: str
    total_programs: int
    total_transfer_partners: int
    total_sweet_spots: int
    webhook_events_total: int
    webhook_events_processed: int
    webhook_events_failed: int
    avg_program_valuation_cpp: Decimal
    active_notification_channels: int


@dataclass(frozen=True)
class ProgramMetrics:
    """Per-program analytics."""

    program_code: str
    program_name: str
    cpp_value: Decimal
    transfer_partner_count: int
    sweet_spot_count: int
    has_hotel_transfers: bool


def collect_system_metrics(
    programs: list,
    transfer_partners: list,
    sweet_spots: list,
    webhook_log: object | None = None,
) -> SystemMetrics:
    """Collect system-wide metrics from available data sources."""
    # Webhook stats
    wh_total = 0
    wh_processed = 0
    wh_failed = 0
    if webhook_log is not None and hasattr(webhook_log, "total_count"):
        wh_total = webhook_log.total_count
        wh_processed = webhook_log.processed_count
        failed = webhook_log.failed_events() if hasattr(webhook_log, "failed_events") else []
        wh_failed = len(failed)

    # Average CPP across programs
    cpp_values = []
    for prog in programs:
        if hasattr(prog, "valuations"):
            # ProgramValuation — average across valuation sources
            vals = list(prog.valuations.values())
            if vals:
                cpp_values.append(sum(vals, Decimal("0")) / len(vals))
        elif hasattr(prog, "cpp"):
            cpp_values.append(prog.cpp)
        elif isinstance(prog, dict) and "cpp" in prog:
            cpp_values.append(Decimal(str(prog["cpp"])))

    avg_cpp = Decimal("0")
    if cpp_values:
        avg_cpp = sum(cpp_values, Decimal("0")) / len(cpp_values)

    return SystemMetrics(
        timestamp=datetime.now(UTC).isoformat(),
        total_programs=len(programs),
        total_transfer_partners=len(transfer_partners),
        total_sweet_spots=len(sweet_spots),
        webhook_events_total=wh_total,
        webhook_events_processed=wh_processed,
        webhook_events_failed=wh_failed,
        avg_program_valuation_cpp=avg_cpp.quantize(Decimal("0.01")),
        active_notification_channels=3,  # email, push, in_app
    )


def collect_program_metrics(
    programs: list,
    transfer_partners: list,
    sweet_spots: list,
) -> list[ProgramMetrics]:
    """Collect per-program metrics."""
    results = []
    for prog in programs:
        if hasattr(prog, "program_code"):
            code = prog.program_code
            name = prog.program_name
            vals = list(prog.valuations.values()) if hasattr(prog, "valuations") else []
            cpp = sum(vals, Decimal("0")) / len(vals) if vals else Decimal("0")
        elif hasattr(prog, "code"):
            code = prog.code
            name = prog.name if hasattr(prog, "name") else ""
            cpp = prog.cpp if hasattr(prog, "cpp") else Decimal("0")
        else:
            code = prog.get("code", "")
            name = prog.get("name", "")
            cpp = Decimal(str(prog.get("cpp", "0")))

        partner_count = sum(1 for tp in transfer_partners if _matches_program(tp, code))
        spot_count = sum(1 for ss in sweet_spots if _matches_sweet_spot(ss, code))
        hotel = code in ("marriott", "hilton", "ihg", "hyatt", "wyndham")

        results.append(
            ProgramMetrics(
                program_code=code,
                program_name=name,
                cpp_value=cpp,
                transfer_partner_count=partner_count,
                sweet_spot_count=spot_count,
                has_hotel_transfers=hotel,
            )
        )
    return results


def _matches_program(partner: object, code: str) -> bool:
    """Check if a transfer partner involves this program."""
    if hasattr(partner, "source_program"):
        return partner.source_program == code or partner.target_program == code
    if isinstance(partner, dict):
        return partner.get("source_program") == code or partner.get("target_program") == code
    return False


def _matches_sweet_spot(sweet_spot: object, code: str) -> bool:
    """Check if a sweet spot belongs to this program."""
    if hasattr(sweet_spot, "program"):
        return sweet_spot.program == code
    if isinstance(sweet_spot, dict):
        return sweet_spot.get("program") == code
    return False
