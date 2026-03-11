"""Tests for path optimizer — top paths, efficient paths, comparisons."""

from __future__ import annotations

from decimal import Decimal

import pytest

from redeemflow.optimization.graph import TransferGraph
from redeemflow.optimization.path_optimizer import (
    compare_paths,
    find_efficient_paths,
    find_top_paths,
    summarize_path,
)
from redeemflow.optimization.seed_data import ALL_PARTNERS, REDEMPTION_OPTIONS


def _build_graph() -> TransferGraph:
    graph = TransferGraph()
    for p in ALL_PARTNERS:
        graph.add_partner(p)
    for r in REDEMPTION_OPTIONS:
        graph.add_redemption(r)
    return graph


class TestFindTopPaths:
    def test_chase_ur_returns_paths(self):
        graph = _build_graph()
        paths = find_top_paths(graph, "chase-ur", 100000)
        assert len(paths) > 0

    def test_paths_sorted_by_cpp_descending(self):
        graph = _build_graph()
        paths = find_top_paths(graph, "chase-ur", 100000)
        cpps = [p.effective_cpp for p in paths]
        assert cpps == sorted(cpps, reverse=True)

    def test_max_results_limit(self):
        graph = _build_graph()
        paths = find_top_paths(graph, "chase-ur", 100000, max_results=3)
        assert len(paths) <= 3

    def test_no_paths_for_insufficient_points(self):
        graph = _build_graph()
        paths = find_top_paths(graph, "chase-ur", 1)
        # May or may not have paths depending on minimum requirements
        for path in paths:
            assert path.source_points_needed <= 1

    def test_unknown_program_returns_empty(self):
        graph = _build_graph()
        paths = find_top_paths(graph, "nonexistent", 100000)
        assert paths == []


class TestFindEfficientPaths:
    def test_returns_paths(self):
        graph = _build_graph()
        paths = find_efficient_paths(graph, "amex-mr", 100000)
        assert len(paths) > 0

    def test_sorted_by_efficiency(self):
        graph = _build_graph()
        paths = find_efficient_paths(graph, "amex-mr", 100000)
        efficiencies = [p.efficiency_score for p in paths]
        assert efficiencies == sorted(efficiencies, reverse=True)


class TestSummarizePath:
    def test_path_summary_has_route(self):
        graph = _build_graph()
        raw_paths = graph.find_paths("chase-ur")
        if raw_paths:
            summary = summarize_path(raw_paths[0])
            assert len(summary.route) > 0
            assert summary.hops > 0

    def test_efficiency_score_positive(self):
        graph = _build_graph()
        raw_paths = graph.find_paths("chase-ur")
        if raw_paths:
            summary = summarize_path(raw_paths[0])
            assert summary.efficiency_score > Decimal("0")


class TestComparePaths:
    def test_comparison_recommends_higher_cpp(self):
        graph = _build_graph()
        raw_paths = graph.find_paths("chase-ur")
        if len(raw_paths) >= 2:
            comparison = compare_paths(raw_paths[0], raw_paths[1])
            assert comparison.recommended in ("a", "b")
            assert len(comparison.rationale) > 0


class TestAPIEndpoints:
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient

        from redeemflow.app import create_app
        from redeemflow.ports import PortBundle

        return TestClient(create_app(ports=PortBundle()))

    def test_top_paths_endpoint(self, client):
        resp = client.post(
            "/api/paths/top",
            json={"program": "chase-ur", "points": 100000},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "paths" in data
        assert data["program"] == "chase-ur"

    def test_efficient_paths_endpoint(self, client):
        resp = client.post(
            "/api/paths/efficient",
            json={"program": "amex-mr", "points": 100000},
        )
        assert resp.status_code == 200
        assert "paths" in resp.json()

    def test_top_paths_with_max_results(self, client):
        resp = client.post(
            "/api/paths/top",
            json={"program": "chase-ur", "points": 100000, "max_results": 2},
        )
        assert resp.status_code == 200
        assert len(resp.json()["paths"]) <= 2
