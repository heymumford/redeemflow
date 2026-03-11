"""Tests for program comparison."""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from redeemflow.valuations.program_comparison import (
    PROGRAM_PROFILES,
    compare_programs,
)


class TestComparePrograms:
    def test_compare_all(self):
        report = compare_programs()
        assert len(report.programs) == len(PROGRAM_PROFILES)
        assert report.best_overall != ""

    def test_compare_subset(self):
        report = compare_programs(["chase-ur", "amex-mr"])
        assert len(report.programs) == 2

    def test_rankings_assigned(self):
        report = compare_programs(["chase-ur", "amex-mr", "hyatt"])
        ranks = [p.overall_rank for p in report.programs]
        assert sorted(ranks) == [1, 2, 3]

    def test_best_overall_is_rank_1(self):
        report = compare_programs()
        best = [p for p in report.programs if p.program_code == report.best_overall]
        assert best[0].overall_rank == 1

    def test_dimension_scores_present(self):
        report = compare_programs(["chase-ur"])
        p = report.programs[0]
        assert len(p.dimension_scores) == 3

    def test_best_by_dimension(self):
        report = compare_programs()
        assert "value" in report.best_by_dimension
        assert "flexibility" in report.best_by_dimension

    def test_hyatt_best_value(self):
        report = compare_programs(["chase-ur", "amex-mr", "hyatt"])
        assert report.best_by_dimension["value"] == "hyatt"  # Highest cpp

    def test_amex_best_flexibility(self):
        report = compare_programs(["chase-ur", "amex-mr", "citi-typ"])
        assert report.best_by_dimension["flexibility"] == "amex-mr"  # Most partners

    def test_empty_codes_returns_all(self):
        report = compare_programs([])
        assert len(report.programs) == len(PROGRAM_PROFILES)

    def test_unknown_codes_ignored(self):
        report = compare_programs(["chase-ur", "nonexistent"])
        assert len(report.programs) == 1

    def test_scores_between_0_and_100(self):
        report = compare_programs()
        for p in report.programs:
            assert Decimal("0") <= p.overall_score <= Decimal("100")


class TestProgramComparisonAPI:
    @pytest.fixture
    def client(self):
        from redeemflow.app import create_app
        from redeemflow.ports import PortBundle

        return TestClient(create_app(ports=PortBundle()))

    def test_compare_all(self, client):
        resp = client.get("/api/programs/compare")
        assert resp.status_code == 200
        data = resp.json()
        assert "programs" in data
        assert "best_overall" in data

    def test_compare_subset(self, client):
        resp = client.get("/api/programs/compare?programs=chase-ur,amex-mr")
        assert resp.status_code == 200
        assert len(resp.json()["programs"]) == 2
