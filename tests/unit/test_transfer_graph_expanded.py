"""RED tests for expanded transfer graph with Bilt + Wells Fargo + more redemptions.

Beck: The test tells you what the code should do.
Fowler: Seed data is a domain concern, not an infrastructure concern.
"""

from __future__ import annotations

from redeemflow.optimization.graph import TransferGraph
from redeemflow.optimization.seed_data import ALL_PARTNERS, REDEMPTION_OPTIONS


class TestExpandedSeedData:
    def test_bilt_partners_exist(self):
        sources = {p.source_program for p in ALL_PARTNERS}
        assert "bilt" in sources

    def test_wells_fargo_partners_exist(self):
        sources = {p.source_program for p in ALL_PARTNERS}
        assert "wells-fargo" in sources

    def test_all_big_six_currencies_present(self):
        sources = {p.source_program for p in ALL_PARTNERS}
        big_six = {"chase-ur", "amex-mr", "citi-ty", "capital-one", "bilt", "wells-fargo"}
        assert big_six.issubset(sources)

    def test_minimum_programs_in_graph(self):
        graph = TransferGraph()
        for p in ALL_PARTNERS:
            graph.add_partner(p)
        for r in REDEMPTION_OPTIONS:
            graph.add_redemption(r)
        # 7 source currencies + 16 unique target programs = 23 total
        assert len(graph.programs) >= 23

    def test_minimum_partner_count(self):
        assert len(ALL_PARTNERS) >= 40

    def test_redemption_sweet_spots_expanded(self):
        programs_with_redemptions = {r.program for r in REDEMPTION_OPTIONS}
        assert "hyatt" in programs_with_redemptions
        assert "ana" in programs_with_redemptions
        assert "virgin-atlantic" in programs_with_redemptions
        assert "air-canada" in programs_with_redemptions  # new: Aeroplan sweet spots
        assert len(REDEMPTION_OPTIONS) >= 15

    def test_bilt_transfers_to_hyatt(self):
        bilt_targets = {p.target_program for p in ALL_PARTNERS if p.source_program == "bilt"}
        assert "hyatt" in bilt_targets

    def test_bilt_transfers_to_airlines(self):
        bilt_targets = {p.target_program for p in ALL_PARTNERS if p.source_program == "bilt"}
        assert "united" in bilt_targets or "american" in bilt_targets

    def test_chase_ur_has_ihg(self):
        chase_targets = {p.target_program for p in ALL_PARTNERS if p.source_program == "chase-ur"}
        assert "ihg" in chase_targets

    def test_chase_ur_has_marriott(self):
        chase_targets = {p.target_program for p in ALL_PARTNERS if p.source_program == "chase-ur"}
        assert "marriott" in chase_targets

    def test_amex_mr_has_marriott(self):
        amex_targets = {p.target_program for p in ALL_PARTNERS if p.source_program == "amex-mr"}
        assert "marriott" in amex_targets
