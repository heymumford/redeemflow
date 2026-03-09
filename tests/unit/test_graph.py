"""Optimization domain — transfer graph engine tests."""

from __future__ import annotations

from decimal import Decimal

import pytest

from redeemflow.optimization.graph import TransferGraph
from redeemflow.optimization.models import RedemptionOption, TransferPartner, TransferPath
from redeemflow.optimization.seed_data import ALL_PARTNERS, REDEMPTION_OPTIONS
from redeemflow.portfolio.models import PointBalance

# --- Frozen dataclass enforcement ---


class TestFrozenValueObjects:
    def test_transfer_partner_is_frozen(self):
        partner = TransferPartner(source_program="a", target_program="b", transfer_ratio=1.0)
        with pytest.raises(AttributeError):
            partner.source_program = "changed"

    def test_redemption_option_is_frozen(self):
        option = RedemptionOption(program="hyatt", description="test", points_required=8000, cash_value=240.0)
        with pytest.raises(AttributeError):
            option.program = "changed"

    def test_transfer_path_is_frozen(self):
        partner = TransferPartner(source_program="a", target_program="b", transfer_ratio=1.0)
        option = RedemptionOption(program="b", description="test", points_required=8000, cash_value=240.0)
        path = TransferPath(
            steps=(partner,),
            redemption=option,
            source_points_needed=8000,
            effective_cpp=3.0,
            total_hops=1,
        )
        with pytest.raises(AttributeError):
            path.effective_cpp = 0.0


# --- TransferPartner model ---


class TestTransferPartner:
    def test_effective_ratio_no_bonus(self):
        partner = TransferPartner(source_program="a", target_program="b", transfer_ratio=1.0)
        assert partner.effective_ratio == 1.0

    def test_effective_ratio_with_bonus(self):
        partner = TransferPartner(source_program="a", target_program="b", transfer_ratio=1.0, transfer_bonus=0.25)
        assert partner.effective_ratio == pytest.approx(1.25)

    def test_effective_ratio_poor_ratio_with_bonus(self):
        partner = TransferPartner(
            source_program="marriott", target_program="ana", transfer_ratio=1.0 / 3.0, transfer_bonus=0.0
        )
        assert partner.effective_ratio == pytest.approx(1.0 / 3.0)

    def test_default_values(self):
        partner = TransferPartner(source_program="a", target_program="b", transfer_ratio=1.0)
        assert partner.transfer_bonus == 0.0
        assert partner.min_transfer == 1000
        assert partner.is_instant is True


# --- RedemptionOption model ---


class TestRedemptionOption:
    def test_cpp_calculation(self):
        option = RedemptionOption(program="hyatt", description="Cat 1-4", points_required=8000, cash_value=240.0)
        assert option.cpp == pytest.approx(3.0)

    def test_cpp_high_value(self):
        option = RedemptionOption(
            program="ana", description="First Class SFO-NRT", points_required=110000, cash_value=16500.0
        )
        assert option.cpp == pytest.approx(15.0)

    def test_cpp_zero_points_returns_zero(self):
        option = RedemptionOption(program="test", description="zero", points_required=0, cash_value=100.0)
        assert option.cpp == 0.0

    def test_default_availability(self):
        option = RedemptionOption(program="test", description="test", points_required=1000, cash_value=50.0)
        assert option.availability == "medium"


# --- Graph construction ---


class TestGraphConstruction:
    def test_empty_graph(self):
        graph = TransferGraph()
        assert graph.partner_count == 0
        assert graph.programs == set()

    def test_add_single_partner(self):
        graph = TransferGraph()
        partner = TransferPartner(source_program="chase-ur", target_program="hyatt", transfer_ratio=1.0)
        graph.add_partner(partner)
        assert graph.partner_count == 1
        assert "chase-ur" in graph.programs
        assert "hyatt" in graph.programs

    def test_add_multiple_partners(self):
        graph = TransferGraph()
        graph.add_partner(TransferPartner(source_program="chase-ur", target_program="hyatt", transfer_ratio=1.0))
        graph.add_partner(TransferPartner(source_program="chase-ur", target_program="united", transfer_ratio=1.0))
        assert graph.partner_count == 2

    def test_add_redemption(self):
        graph = TransferGraph()
        option = RedemptionOption(program="hyatt", description="Cat 1-4", points_required=8000, cash_value=240.0)
        graph.add_redemption(option)
        assert "hyatt" in graph.programs
        assert len(graph.get_redemptions("hyatt")) == 1

    def test_add_multiple_redemptions_same_program(self):
        graph = TransferGraph()
        graph.add_redemption(
            RedemptionOption(program="hyatt", description="Cat 1-4", points_required=8000, cash_value=240.0)
        )
        graph.add_redemption(
            RedemptionOption(program="hyatt", description="Cat 7-8", points_required=30000, cash_value=900.0)
        )
        assert len(graph.get_redemptions("hyatt")) == 2

    def test_get_partners_from(self):
        graph = TransferGraph()
        graph.add_partner(TransferPartner(source_program="chase-ur", target_program="hyatt", transfer_ratio=1.0))
        graph.add_partner(TransferPartner(source_program="chase-ur", target_program="united", transfer_ratio=1.0))
        graph.add_partner(TransferPartner(source_program="amex-mr", target_program="delta", transfer_ratio=1.0))
        partners = graph.get_partners_from("chase-ur")
        assert len(partners) == 2
        targets = {p.target_program for p in partners}
        assert targets == {"hyatt", "united"}

    def test_get_partners_from_unknown_program(self):
        graph = TransferGraph()
        assert graph.get_partners_from("unknown") == []

    def test_get_redemptions_unknown_program(self):
        graph = TransferGraph()
        assert graph.get_redemptions("unknown") == []


# --- Path finding ---


class TestPathFinding:
    def setup_method(self):
        """Build a small test graph: chase-ur -> hyatt -> redemption."""
        self.graph = TransferGraph()
        self.graph.add_partner(TransferPartner(source_program="chase-ur", target_program="hyatt", transfer_ratio=1.0))
        self.graph.add_redemption(
            RedemptionOption(program="hyatt", description="Cat 1-4", points_required=8000, cash_value=240.0)
        )

    def test_single_hop_path(self):
        paths = self.graph.find_paths("chase-ur")
        assert len(paths) >= 1
        path = paths[0]
        assert path.total_hops == 1
        assert path.steps[0].target_program == "hyatt"
        assert path.redemption.program == "hyatt"

    def test_single_hop_effective_cpp(self):
        paths = self.graph.find_paths("chase-ur")
        path = paths[0]
        # 1:1 ratio, so effective CPP = redemption CPP = 3.0
        assert path.effective_cpp == pytest.approx(3.0)
        assert path.source_points_needed == 8000

    def test_no_paths_from_unknown_source(self):
        paths = self.graph.find_paths("unknown-program")
        assert paths == []

    def test_no_paths_from_terminal_node(self):
        # hyatt has no outbound edges and no further redemptions through it
        paths = self.graph.find_paths("hyatt")
        assert paths == []

    def test_paths_sorted_by_cpp_descending(self):
        self.graph.add_redemption(
            RedemptionOption(program="hyatt", description="Cat 7-8", points_required=30000, cash_value=600.0)
        )
        paths = self.graph.find_paths("chase-ur")
        cpps = [p.effective_cpp for p in paths]
        assert cpps == sorted(cpps, reverse=True)

    def test_multi_hop_path(self):
        """chase-ur -> hub -> final -> redemption (2 hops)."""
        graph = TransferGraph()
        graph.add_partner(TransferPartner(source_program="chase-ur", target_program="hub", transfer_ratio=1.0))
        graph.add_partner(TransferPartner(source_program="hub", target_program="final", transfer_ratio=0.5))
        graph.add_redemption(
            RedemptionOption(program="final", description="Test redemption", points_required=10000, cash_value=500.0)
        )
        paths = graph.find_paths("chase-ur")
        assert len(paths) >= 1
        path = paths[0]
        assert path.total_hops == 2
        # Effective ratio: 1.0 * 0.5 = 0.5. Need 10000/0.5 = 20000 source points.
        assert path.source_points_needed == 20000
        # CPP: 500 / 20000 * 100 = 2.5
        assert path.effective_cpp == pytest.approx(2.5)

    def test_max_hops_limit(self):
        """Paths beyond max_hops are excluded."""
        graph = TransferGraph()
        graph.add_partner(TransferPartner(source_program="a", target_program="b", transfer_ratio=1.0))
        graph.add_partner(TransferPartner(source_program="b", target_program="c", transfer_ratio=1.0))
        graph.add_partner(TransferPartner(source_program="c", target_program="d", transfer_ratio=1.0))
        graph.add_redemption(RedemptionOption(program="d", description="deep", points_required=1000, cash_value=100.0))
        # max_hops=2 should NOT reach d (needs 3 hops)
        paths_2 = graph.find_paths("a", max_hops=2)
        assert len(paths_2) == 0

        # max_hops=3 SHOULD reach d
        paths_3 = graph.find_paths("a", max_hops=3)
        assert len(paths_3) >= 1
        assert paths_3[0].total_hops == 3

    def test_transfer_bonus_affects_points_needed(self):
        graph = TransferGraph()
        graph.add_partner(
            TransferPartner(source_program="chase-ur", target_program="hyatt", transfer_ratio=1.0, transfer_bonus=0.25)
        )
        graph.add_redemption(
            RedemptionOption(program="hyatt", description="Cat 1-4", points_required=8000, cash_value=240.0)
        )
        paths = graph.find_paths("chase-ur")
        path = paths[0]
        # With 25% bonus, effective ratio = 1.25. Need 8000/1.25 = 6400.
        assert path.source_points_needed == 6400
        # CPP: 240 / 6400 * 100 = 3.75
        assert path.effective_cpp == pytest.approx(3.75)

    def test_poor_transfer_ratio(self):
        """Marriott-style 3:1 transfer ratio."""
        graph = TransferGraph()
        graph.add_partner(TransferPartner(source_program="marriott", target_program="united", transfer_ratio=1.0 / 3.0))
        graph.add_redemption(
            RedemptionOption(
                program="united",
                description="Polaris Business",
                points_required=80000,
                cash_value=5600.0,
            )
        )
        paths = graph.find_paths("marriott")
        path = paths[0]
        # Need 80000 / (1/3) = 240000 Marriott points
        assert path.source_points_needed == 240000
        # CPP: 5600 / 240000 * 100 ≈ 2.333
        assert path.effective_cpp == pytest.approx(5600.0 / 240000 * 100)


# --- Circular references ---


class TestCircularReferences:
    def test_no_infinite_loop_on_cycle(self):
        """Graph with a cycle should not cause infinite loop."""
        graph = TransferGraph()
        graph.add_partner(TransferPartner(source_program="a", target_program="b", transfer_ratio=1.0))
        graph.add_partner(TransferPartner(source_program="b", target_program="a", transfer_ratio=1.0))
        graph.add_redemption(RedemptionOption(program="b", description="test", points_required=1000, cash_value=50.0))
        # Should complete without hanging
        paths = graph.find_paths("a")
        assert len(paths) >= 1
        # No path should visit the same node twice
        for path in paths:
            visited = [path.steps[0].source_program] + [s.target_program for s in path.steps]
            assert len(visited) == len(set(visited))

    def test_three_node_cycle(self):
        """a -> b -> c -> a should not loop."""
        graph = TransferGraph()
        graph.add_partner(TransferPartner(source_program="a", target_program="b", transfer_ratio=1.0))
        graph.add_partner(TransferPartner(source_program="b", target_program="c", transfer_ratio=1.0))
        graph.add_partner(TransferPartner(source_program="c", target_program="a", transfer_ratio=1.0))
        graph.add_redemption(RedemptionOption(program="c", description="test", points_required=1000, cash_value=50.0))
        paths = graph.find_paths("a")
        assert len(paths) >= 1


# --- find_best_path ---


class TestFindBestPath:
    def test_returns_best_affordable_path(self):
        graph = TransferGraph()
        graph.add_partner(TransferPartner(source_program="chase-ur", target_program="hyatt", transfer_ratio=1.0))
        graph.add_redemption(
            RedemptionOption(program="hyatt", description="Cat 1-4", points_required=8000, cash_value=240.0)
        )
        graph.add_redemption(
            RedemptionOption(program="hyatt", description="Park Hyatt", points_required=30000, cash_value=900.0)
        )
        path = graph.find_best_path("chase-ur", points=50000)
        assert path is not None
        # Both are affordable; best CPP wins (Cat 1-4 = 3.0 > Park Hyatt = 3.0 ... equal, first wins)
        assert path.source_points_needed <= 50000

    def test_returns_none_when_insufficient_points(self):
        graph = TransferGraph()
        graph.add_partner(TransferPartner(source_program="chase-ur", target_program="hyatt", transfer_ratio=1.0))
        graph.add_redemption(
            RedemptionOption(program="hyatt", description="Cat 1-4", points_required=8000, cash_value=240.0)
        )
        path = graph.find_best_path("chase-ur", points=1000)
        assert path is None

    def test_returns_none_for_unknown_program(self):
        graph = TransferGraph()
        path = graph.find_best_path("nonexistent", points=100000)
        assert path is None


# --- Portfolio optimization ---


class TestPortfolioOptimization:
    def setup_method(self):
        self.graph = TransferGraph()
        self.graph.add_partner(TransferPartner(source_program="chase-ur", target_program="hyatt", transfer_ratio=1.0))
        self.graph.add_partner(TransferPartner(source_program="amex-mr", target_program="ana", transfer_ratio=1.0))
        self.graph.add_redemption(
            RedemptionOption(program="hyatt", description="Cat 1-4", points_required=8000, cash_value=240.0)
        )
        self.graph.add_redemption(
            RedemptionOption(
                program="ana", description="First Class SFO-NRT", points_required=110000, cash_value=16500.0
            )
        )

    def test_optimizes_multiple_balances(self):
        balances = [
            PointBalance(program_code="chase-ur", points=50000, cpp_baseline=Decimal("1.5")),
            PointBalance(program_code="amex-mr", points=120000, cpp_baseline=Decimal("1.0")),
        ]
        recs = self.graph.optimize_portfolio(balances)
        assert len(recs) == 2
        # Sorted by effective_cpp descending: ANA (15.0) > Hyatt (3.0)
        assert recs[0].redemption.program == "ana"
        assert recs[1].redemption.program == "hyatt"

    def test_skips_zero_point_balances(self):
        balances = [
            PointBalance(program_code="chase-ur", points=0, cpp_baseline=Decimal("1.5")),
        ]
        recs = self.graph.optimize_portfolio(balances)
        assert recs == []

    def test_skips_unaffordable_balances(self):
        balances = [
            PointBalance(program_code="amex-mr", points=1000, cpp_baseline=Decimal("1.0")),
        ]
        recs = self.graph.optimize_portfolio(balances)
        assert recs == []

    def test_empty_portfolio(self):
        recs = self.graph.optimize_portfolio([])
        assert recs == []

    def test_program_not_in_graph(self):
        balances = [
            PointBalance(program_code="unknown", points=50000, cpp_baseline=Decimal("1.0")),
        ]
        recs = self.graph.optimize_portfolio(balances)
        assert recs == []


# --- Seed data integrity ---


class TestSeedData:
    def test_all_partners_have_positive_ratio(self):
        for partner in ALL_PARTNERS:
            assert partner.transfer_ratio > 0, f"{partner.source_program} -> {partner.target_program} has bad ratio"

    def test_all_redemptions_have_positive_points(self):
        for option in REDEMPTION_OPTIONS:
            assert option.points_required > 0, f"{option.description} has zero/negative points"

    def test_all_redemptions_have_positive_value(self):
        for option in REDEMPTION_OPTIONS:
            assert option.cash_value > 0, f"{option.description} has zero/negative cash value"

    def test_all_redemptions_have_valid_availability(self):
        valid = {"high", "medium", "low"}
        for option in REDEMPTION_OPTIONS:
            assert option.availability in valid, f"{option.description} has invalid availability"

    def test_seed_graph_builds_without_error(self):
        graph = TransferGraph()
        for partner in ALL_PARTNERS:
            graph.add_partner(partner)
        for option in REDEMPTION_OPTIONS:
            graph.add_redemption(option)
        assert graph.partner_count == len(ALL_PARTNERS)

    def test_chase_ur_has_partners(self):
        graph = TransferGraph()
        for partner in ALL_PARTNERS:
            graph.add_partner(partner)
        partners = graph.get_partners_from("chase-ur")
        assert len(partners) >= 7

    def test_seed_graph_finds_paths(self):
        """The seeded graph should produce real recommendations."""
        graph = TransferGraph()
        for partner in ALL_PARTNERS:
            graph.add_partner(partner)
        for option in REDEMPTION_OPTIONS:
            graph.add_redemption(option)
        paths = graph.find_paths("chase-ur")
        assert len(paths) > 0
        # Best Chase UR path should include Hyatt or similar high-CPP option
        assert paths[0].effective_cpp > 1.0
