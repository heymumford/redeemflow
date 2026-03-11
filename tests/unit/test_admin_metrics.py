"""Tests for admin metrics and dashboard endpoints."""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from redeemflow.admin.metrics import (
    SystemMetrics,
    collect_program_metrics,
    collect_system_metrics,
)


class FakeProgram:
    def __init__(self, code: str, name: str, cpp: Decimal):
        self.code = code
        self.name = name
        self.cpp = cpp


class FakePartner:
    def __init__(self, source_program: str, target_program: str):
        self.source_program = source_program
        self.target_program = target_program


class FakeSweetSpot:
    def __init__(self, program: str):
        self.program = program


class TestCollectSystemMetrics:
    def test_basic_counts(self):
        programs = [FakeProgram("chase-ur", "Chase UR", Decimal("2.0"))]
        partners = [FakePartner("chase-ur", "united")]
        spots = [FakeSweetSpot("chase-ur"), FakeSweetSpot("united")]

        metrics = collect_system_metrics(programs, partners, spots)
        assert isinstance(metrics, SystemMetrics)
        assert metrics.total_programs == 1
        assert metrics.total_transfer_partners == 1
        assert metrics.total_sweet_spots == 2

    def test_avg_cpp_calculation(self):
        programs = [
            FakeProgram("chase-ur", "Chase UR", Decimal("2.0")),
            FakeProgram("amex-mr", "Amex MR", Decimal("1.5")),
        ]
        metrics = collect_system_metrics(programs, [], [])
        assert metrics.avg_program_valuation_cpp == Decimal("1.75")

    def test_empty_programs(self):
        metrics = collect_system_metrics([], [], [])
        assert metrics.total_programs == 0
        assert metrics.avg_program_valuation_cpp == Decimal("0")

    def test_webhook_log_integration(self):
        from redeemflow.billing.webhook_processor import WebhookEventLog

        log = WebhookEventLog()
        log.receive("evt_1", "test", "stripe", {})
        log.receive("evt_2", "test", "stripe", {})
        log.mark_processed("evt_1")
        log.mark_failed("evt_2", "error")

        metrics = collect_system_metrics([], [], [], webhook_log=log)
        assert metrics.webhook_events_total == 2
        assert metrics.webhook_events_processed == 1
        assert metrics.webhook_events_failed == 1

    def test_no_webhook_log(self):
        metrics = collect_system_metrics([], [], [], webhook_log=None)
        assert metrics.webhook_events_total == 0

    def test_dict_programs(self):
        programs = [{"code": "united", "name": "United", "cpp": "1.4"}]
        metrics = collect_system_metrics(programs, [], [])
        assert metrics.total_programs == 1
        assert metrics.avg_program_valuation_cpp == Decimal("1.40")

    def test_timestamp_present(self):
        metrics = collect_system_metrics([], [], [])
        assert metrics.timestamp is not None
        assert "T" in metrics.timestamp  # ISO format


class TestCollectProgramMetrics:
    def test_basic_program(self):
        programs = [FakeProgram("chase-ur", "Chase UR", Decimal("2.0"))]
        partners = [
            FakePartner("chase-ur", "united"),
            FakePartner("chase-ur", "hyatt"),
        ]
        spots = [FakeSweetSpot("chase-ur")]

        results = collect_program_metrics(programs, partners, spots)
        assert len(results) == 1
        assert results[0].program_code == "chase-ur"
        assert results[0].transfer_partner_count == 2
        assert results[0].sweet_spot_count == 1
        assert results[0].has_hotel_transfers is False

    def test_hotel_program_flagged(self):
        programs = [FakeProgram("marriott", "Marriott Bonvoy", Decimal("0.7"))]
        results = collect_program_metrics(programs, [], [])
        assert results[0].has_hotel_transfers is True

    def test_multiple_programs(self):
        programs = [
            FakeProgram("chase-ur", "Chase UR", Decimal("2.0")),
            FakeProgram("amex-mr", "Amex MR", Decimal("1.5")),
        ]
        results = collect_program_metrics(programs, [], [])
        assert len(results) == 2

    def test_dict_programs(self):
        programs = [{"code": "united", "name": "United", "cpp": "1.4"}]
        results = collect_program_metrics(programs, [], [])
        assert results[0].program_code == "united"


class TestAdminAPIEndpoints:
    AUTH_HEADERS = {"Authorization": "Bearer test-token-eric"}

    @pytest.fixture
    def client(self):
        from redeemflow.app import create_app
        from redeemflow.ports import PortBundle

        return TestClient(create_app(ports=PortBundle()))

    def test_system_metrics_requires_auth(self, client):
        resp = client.get("/api/admin/metrics")
        assert resp.status_code == 401

    def test_system_metrics_returns_data(self, client):
        resp = client.get("/api/admin/metrics", headers=self.AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "programs" in data
        assert "transfer_network" in data
        assert "webhooks" in data
        assert "notifications" in data
        assert data["programs"]["total"] > 0

    def test_program_metrics_requires_auth(self, client):
        resp = client.get("/api/admin/programs")
        assert resp.status_code == 401

    def test_program_metrics_returns_programs(self, client):
        resp = client.get("/api/admin/programs", headers=self.AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "programs" in data
        assert len(data["programs"]) > 0
        prog = data["programs"][0]
        assert "code" in prog
        assert "cpp" in prog
        assert "transfer_partners" in prog

    def test_program_metrics_includes_hotel_flag(self, client):
        resp = client.get("/api/admin/programs", headers=self.AUTH_HEADERS)
        programs = resp.json()["programs"]
        codes = {p["code"] for p in programs}
        hotel_programs = [p for p in programs if p["has_hotel_transfers"]]
        if "marriott" in codes:
            assert any(p["code"] == "marriott" for p in hotel_programs)
