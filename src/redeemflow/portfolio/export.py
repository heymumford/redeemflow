"""Portfolio export/import — data portability for user accounts.

Beck: Export is a snapshot; import is a merge.
Fowler: Anti-corruption layer — external format is separate from domain.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class ExportFormat(str, Enum):
    JSON = "json"
    CSV = "csv"


@dataclass(frozen=True)
class ExportedBalance:
    """A single balance in export format."""

    program_code: str
    program_name: str
    points: int
    estimated_value: str
    cpp: str


@dataclass(frozen=True)
class PortfolioExport:
    """Complete portfolio export."""

    user_id: str
    export_date: str
    format: ExportFormat
    balances: list[ExportedBalance]
    total_points: int
    total_value: str
    program_count: int


def export_portfolio(
    user_id: str,
    balances: list,
    export_format: ExportFormat = ExportFormat.JSON,
    program_names: dict[str, str] | None = None,
) -> PortfolioExport:
    """Export portfolio balances to portable format."""
    from datetime import UTC, datetime

    names = program_names or {}
    exported = []
    total_points = 0
    total_value = Decimal("0")

    for b in balances:
        code = b.program_code
        points = b.points
        cpp = b.cpp_baseline if hasattr(b, "cpp_baseline") else Decimal("1.0")
        value = (Decimal(points) * cpp / 100).quantize(Decimal("0.01"))

        exported.append(
            ExportedBalance(
                program_code=code,
                program_name=names.get(code, code),
                points=points,
                estimated_value=str(value),
                cpp=str(cpp),
            )
        )
        total_points += points
        total_value += value

    return PortfolioExport(
        user_id=user_id,
        export_date=datetime.now(UTC).isoformat(),
        format=export_format,
        balances=exported,
        total_points=total_points,
        total_value=str(total_value),
        program_count=len(exported),
    )


def export_to_json(export: PortfolioExport) -> str:
    """Serialize export to JSON string."""
    data = {
        "user_id": export.user_id,
        "export_date": export.export_date,
        "total_points": export.total_points,
        "total_value": export.total_value,
        "program_count": export.program_count,
        "balances": [
            {
                "program_code": b.program_code,
                "program_name": b.program_name,
                "points": b.points,
                "estimated_value": b.estimated_value,
                "cpp": b.cpp,
            }
            for b in export.balances
        ],
    }
    return json.dumps(data, indent=2)


def export_to_csv(export: PortfolioExport) -> str:
    """Serialize export to CSV string."""
    lines = ["program_code,program_name,points,estimated_value,cpp"]
    for b in export.balances:
        name = b.program_name.replace(",", " ")
        lines.append(f"{b.program_code},{name},{b.points},{b.estimated_value},{b.cpp}")
    return "\n".join(lines)


def import_from_json(json_str: str) -> list[dict]:
    """Parse JSON export and return balance dicts for re-import."""
    data = json.loads(json_str)
    return data.get("balances", [])


def import_from_csv(csv_str: str) -> list[dict]:
    """Parse CSV export and return balance dicts."""
    lines = csv_str.strip().split("\n")
    if len(lines) < 2:
        return []

    header = lines[0].split(",")
    results = []
    for line in lines[1:]:
        vals = line.split(",")
        if len(vals) >= len(header):
            row = dict(zip(header, vals, strict=False))
            row["points"] = int(row.get("points", 0))
            results.append(row)
    return results
