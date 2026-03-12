"""Tests for hotel transfer analysis — Marriott, Hilton, IHG economics."""

from __future__ import annotations

from decimal import Decimal

import pytest

from redeemflow.optimization.graph import TransferGraph
from redeemflow.optimization.hotel_transfers import (
    assess_hotel_transfer,
    summarize_hotel_program,
)
from redeemflow.optimization.seed_data import ALL_PARTNERS, REDEMPTION_OPTIONS


def _build_graph() -> TransferGraph:
    graph = TransferGraph()
    for p in ALL_PARTNERS:
        graph.add_partner(p)
    for r in REDEMPTION_OPTIONS:
        graph.add_redemption(r)
    return graph


class TestSeedDataExpansion:
    def test_hilton_has_airline_partners(self):
        graph = _build_graph()
        partners = graph.get_partners_from("hilton")
        targets = {p.target_program for p in partners}
        assert "american" in targets
        assert "delta" in targets
        assert "british-airways" in targets

    def test_ihg_has_airline_partners(self):
        graph = _build_graph()
        partners = graph.get_partners_from("ihg")
        targets = {p.target_program for p in partners}
        assert "united" in targets
        assert "american" in targets

    def test_marriott_still_has_partners(self):
        graph = _build_graph()
        partners = graph.get_partners_from("marriott")
        assert len(partners) >= 7

    def test_hilton_ratio_is_10_to_1(self):
        graph = _build_graph()
        partners = graph.get_partners_from("hilton")
        for p in partners:
            assert abs(p.transfer_ratio - 0.1) < 0.001

    def test_expanded_hotel_redemptions(self):
        graph = _build_graph()
        ihg_redemptions = graph.get_redemptions("ihg")
        assert len(ihg_redemptions) >= 2
        marriott_redemptions = graph.get_redemptions("marriott")
        assert len(marriott_redemptions) >= 3
        hilton_redemptions = graph.get_redemptions("hilton")
        assert len(hilton_redemptions) >= 3

    def test_total_partners_increased(self):
        # Hilton (5) + IHG (3) = 8 new partnerships
        assert len(ALL_PARTNERS) >= 50


class TestAssessHotelTransfer:
    def test_marriott_to_united(self):
        graph = _build_graph()
        assessment = assess_hotel_transfer(graph, "marriott", "united", 60000)
        assert assessment is not None
        assert assessment.hotel_program == "marriott"
        assert assessment.airline_program == "united"
        assert assessment.airline_miles_received == int(60000 * (1.0 / 3.0))

    def test_hilton_to_delta(self):
        graph = _build_graph()
        assessment = assess_hotel_transfer(graph, "hilton", "delta", 100000)
        assert assessment is not None
        assert assessment.airline_miles_received == 10000
        assert assessment.transfer_ratio == pytest.approx(0.1)

    def test_ihg_to_united(self):
        graph = _build_graph()
        assessment = assess_hotel_transfer(graph, "ihg", "united", 100000)
        assert assessment is not None
        assert assessment.airline_miles_received == 20000

    def test_nonexistent_partnership_returns_none(self):
        graph = _build_graph()
        assessment = assess_hotel_transfer(graph, "hilton", "southwest", 100000)
        assert assessment is None

    def test_recommendation_is_valid(self):
        graph = _build_graph()
        assessment = assess_hotel_transfer(graph, "marriott", "united", 100000)
        assert assessment is not None
        assert assessment.recommendation in ("transfer", "redeem_hotel", "situational")
        assert len(assessment.rationale) > 0

    def test_value_ratio_positive(self):
        graph = _build_graph()
        assessment = assess_hotel_transfer(graph, "marriott", "united", 100000)
        assert assessment is not None
        assert assessment.value_ratio >= Decimal("0")


class TestSummarizeHotelProgram:
    def test_marriott_summary(self):
        graph = _build_graph()
        summary = summarize_hotel_program(graph, "marriott")
        assert summary.program == "marriott"
        assert len(summary.airline_partners) >= 5
        assert summary.best_direct_cpp > Decimal("0")

    def test_hilton_summary(self):
        graph = _build_graph()
        summary = summarize_hotel_program(graph, "hilton")
        assert summary.program == "hilton"
        assert len(summary.airline_partners) >= 3
        assert len(summary.assessments) >= 3

    def test_transfer_penalty_non_negative(self):
        graph = _build_graph()
        summary = summarize_hotel_program(graph, "marriott")
        assert summary.transfer_penalty >= Decimal("0")


class TestAPIEndpoints:
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient

        from redeemflow.app import create_app
        from redeemflow.ports import PortBundle

        return TestClient(create_app(ports=PortBundle()))

    def test_assess_transfer_endpoint(self, client):
        resp = client.post(
            "/api/hotel-transfer/assess",
            json={"hotel_program": "marriott", "airline_program": "united", "points": 60000},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["hotel_program"] == "marriott"
        assert data["recommendation"] in ("transfer", "redeem_hotel", "situational")

    def test_assess_nonexistent_partnership(self, client):
        resp = client.post(
            "/api/hotel-transfer/assess",
            json={"hotel_program": "hilton", "airline_program": "southwest", "points": 100000},
        )
        assert resp.status_code == 404
        assert "detail" in resp.json()

    def test_hotel_summary_endpoint(self, client):
        resp = client.get("/api/hotel-transfer/summary/marriott")
        assert resp.status_code == 200
        data = resp.json()
        assert data["program"] == "marriott"
        assert len(data["airline_partners"]) >= 5
        assert "assessments" in data

    def test_hotel_summary_unknown_program(self, client):
        resp = client.get("/api/hotel-transfer/summary/nonexistent")
        assert resp.status_code == 404
        assert "detail" in resp.json()

    def test_graph_summary_reflects_new_partners(self, client):
        resp = client.get("/api/graph/summary")
        assert resp.status_code == 200
        data = resp.json()
        # Should reflect expanded partner count
        assert data["total_partnerships"] >= 50
