"""Tests for graph analytics — connectivity, summary, bonuses."""

from __future__ import annotations

import pytest

from redeemflow.optimization.graph import TransferGraph
from redeemflow.optimization.graph_analytics import (
    find_transfer_bonuses,
    graph_summary,
    program_connectivity,
)
from redeemflow.optimization.seed_data import ALL_PARTNERS, REDEMPTION_OPTIONS


def _build_graph() -> TransferGraph:
    graph = TransferGraph()
    for p in ALL_PARTNERS:
        graph.add_partner(p)
    for r in REDEMPTION_OPTIONS:
        graph.add_redemption(r)
    return graph


class TestProgramConnectivity:
    def test_chase_ur_is_hub(self):
        graph = _build_graph()
        conn = program_connectivity(graph, "chase-ur")
        assert conn.is_hub is True
        assert conn.outbound_partners >= 9

    def test_amex_mr_is_hub(self):
        graph = _build_graph()
        conn = program_connectivity(graph, "amex-mr")
        assert conn.is_hub is True

    def test_endpoint_program_not_hub(self):
        graph = _build_graph()
        conn = program_connectivity(graph, "ana")
        assert conn.is_hub is False
        assert conn.inbound_partners > 0

    def test_outbound_count(self):
        graph = _build_graph()
        conn = program_connectivity(graph, "bilt")
        assert conn.outbound_partners >= 7


class TestGraphSummary:
    def test_total_programs(self):
        graph = _build_graph()
        summary = graph_summary(graph)
        assert summary.total_programs >= 15

    def test_total_partnerships(self):
        graph = _build_graph()
        summary = graph_summary(graph)
        assert summary.total_partnerships == len(ALL_PARTNERS)

    def test_hubs_identified(self):
        graph = _build_graph()
        summary = graph_summary(graph)
        assert "chase-ur" in summary.hub_programs
        assert "amex-mr" in summary.hub_programs

    def test_density_between_0_and_1(self):
        graph = _build_graph()
        summary = graph_summary(graph)
        assert 0 < summary.density < 1

    def test_avg_connections_positive(self):
        graph = _build_graph()
        summary = graph_summary(graph)
        assert summary.avg_connections > 0


class TestTransferBonuses:
    def test_no_bonuses_in_seed_data(self):
        graph = _build_graph()
        bonuses = find_transfer_bonuses(graph)
        # Seed data has no active bonuses (all bonus=0)
        assert len(bonuses) == 0


class TestAPIEndpoints:
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient

        from redeemflow.app import create_app
        from redeemflow.ports import PortBundle

        return TestClient(create_app(ports=PortBundle()))

    def test_graph_summary_endpoint(self, client):
        resp = client.get("/api/graph/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_programs" in data
        assert "hub_programs" in data
        assert data["total_programs"] >= 15

    def test_connectivity_endpoint(self, client):
        resp = client.get("/api/graph/connectivity/chase-ur")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_hub"] is True
        assert data["outbound_partners"] >= 9

    def test_connectivity_unknown_program(self, client):
        resp = client.get("/api/graph/connectivity/nonexistent")
        assert resp.status_code == 200
        assert "error" in resp.json()

    def test_bonuses_endpoint(self, client):
        resp = client.get("/api/graph/bonuses")
        assert resp.status_code == 200
        assert "count" in resp.json()
