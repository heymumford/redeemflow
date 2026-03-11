"""Tests for portfolio export/import — data portability."""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from redeemflow.portfolio.export import (
    ExportFormat,
    export_portfolio,
    export_to_csv,
    export_to_json,
    import_from_csv,
    import_from_json,
)
from redeemflow.portfolio.models import PointBalance


def _balances() -> list[PointBalance]:
    return [
        PointBalance(program_code="united", points=80000, cpp_baseline=Decimal("1.20")),
        PointBalance(program_code="hyatt", points=40000, cpp_baseline=Decimal("1.70")),
    ]


class TestExportPortfolio:
    def test_basic_export(self):
        export = export_portfolio("u1", _balances())
        assert export.user_id == "u1"
        assert export.program_count == 2
        assert export.total_points == 120000
        assert len(export.balances) == 2

    def test_json_format(self):
        export = export_portfolio("u1", _balances(), ExportFormat.JSON)
        assert export.format == ExportFormat.JSON

    def test_csv_format(self):
        export = export_portfolio("u1", _balances(), ExportFormat.CSV)
        assert export.format == ExportFormat.CSV

    def test_program_names(self):
        names = {"united": "United MileagePlus", "hyatt": "World of Hyatt"}
        export = export_portfolio("u1", _balances(), program_names=names)
        assert export.balances[0].program_name == "United MileagePlus"

    def test_empty_balances(self):
        export = export_portfolio("u1", [])
        assert export.total_points == 0
        assert export.program_count == 0


class TestSerialize:
    def test_to_json(self):
        export = export_portfolio("u1", _balances())
        json_str = export_to_json(export)
        assert '"united"' in json_str
        assert '"hyatt"' in json_str
        assert '"total_points": 120000' in json_str

    def test_to_csv(self):
        export = export_portfolio("u1", _balances())
        csv_str = export_to_csv(export)
        lines = csv_str.strip().split("\n")
        assert lines[0] == "program_code,program_name,points,estimated_value,cpp"
        assert len(lines) == 3  # header + 2 balances

    def test_json_roundtrip(self):
        export = export_portfolio("u1", _balances())
        json_str = export_to_json(export)
        imported = import_from_json(json_str)
        assert len(imported) == 2
        assert imported[0]["program_code"] == "united"
        assert imported[0]["points"] == 80000

    def test_csv_roundtrip(self):
        export = export_portfolio("u1", _balances())
        csv_str = export_to_csv(export)
        imported = import_from_csv(csv_str)
        assert len(imported) == 2
        assert imported[0]["program_code"] == "united"
        assert imported[0]["points"] == 80000


class TestImport:
    def test_import_empty_json(self):
        assert import_from_json("{}") == []

    def test_import_empty_csv(self):
        assert import_from_csv("") == []

    def test_import_csv_header_only(self):
        assert import_from_csv("program_code,points") == []


class TestExportAPI:
    AUTH_HEADERS = {"Authorization": "Bearer test-token-eric"}

    @pytest.fixture
    def client(self):
        from redeemflow.app import create_app
        from redeemflow.ports import PortBundle

        return TestClient(create_app(ports=PortBundle()))

    def test_export_json(self, client):
        resp = client.get("/api/portfolio/export?format=json", headers=self.AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["format"] == "json"
        assert "data" in data

    def test_export_csv(self, client):
        resp = client.get("/api/portfolio/export?format=csv", headers=self.AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["format"] == "csv"

    def test_export_invalid_format(self, client):
        resp = client.get("/api/portfolio/export?format=xml", headers=self.AUTH_HEADERS)
        assert "error" in resp.json()

    def test_import_json(self, client):
        # First export, then import
        export_resp = client.get("/api/portfolio/export?format=json", headers=self.AUTH_HEADERS)
        json_data = export_resp.json()["data"]
        resp = client.post(
            "/api/portfolio/import",
            json={"data": json_data, "format": "json"},
            headers=self.AUTH_HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "imported"

    def test_export_requires_auth(self, client):
        assert client.get("/api/portfolio/export").status_code == 401
