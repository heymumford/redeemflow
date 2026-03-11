"""Optimization domain — fake adapter for testing.

In-memory TransferGraphPort implementation with deterministic transfer data.
Zero network calls.
"""

from __future__ import annotations

from redeemflow.optimization.models import RedemptionOption, TransferPartner, TransferPath

# Deterministic test transfer partners
_TEST_PARTNERS: list[TransferPartner] = [
    TransferPartner(source_program="UR", target_program="UA", transfer_ratio=1.0),
    TransferPartner(source_program="UR", target_program="HH", transfer_ratio=1.0, transfer_bonus=0.0),
    TransferPartner(source_program="UR", target_program="BA", transfer_ratio=1.0),
    TransferPartner(source_program="MR", target_program="ANA", transfer_ratio=1.0),
    TransferPartner(source_program="MR", target_program="DL", transfer_ratio=1.0),
    TransferPartner(source_program="MR", target_program="BA", transfer_ratio=1.0, transfer_bonus=0.25),
    TransferPartner(source_program="TYP", target_program="TK", transfer_ratio=1.0),
    TransferPartner(source_program="TYP", target_program="SQ", transfer_ratio=1.0),
]

_TEST_REDEMPTIONS: dict[str, list[RedemptionOption]] = {
    "UA": [
        RedemptionOption(
            program="UA",
            description="SFO-NRT Business Saver",
            points_required=80000,
            cash_value=5600.0,
        ),
    ],
    "ANA": [
        RedemptionOption(
            program="ANA",
            description="SFO-NRT First Class",
            points_required=110000,
            cash_value=16500.0,
        ),
    ],
    "BA": [
        RedemptionOption(
            program="BA",
            description="JFK-LHR Business",
            points_required=60000,
            cash_value=4500.0,
        ),
    ],
}


class FakeTransferGraphAdapter:
    """In-memory transfer graph adapter with deterministic test data."""

    def __init__(
        self,
        partners: list[TransferPartner] | None = None,
        redemptions: dict[str, list[RedemptionOption]] | None = None,
    ) -> None:
        self._partners = partners if partners is not None else list(_TEST_PARTNERS)
        self._redemptions = redemptions if redemptions is not None else dict(_TEST_REDEMPTIONS)

    def find_paths(self, source: str, target: str) -> list[TransferPath]:
        """Find transfer paths from source to target program."""
        paths: list[TransferPath] = []
        # Direct single-hop paths
        for partner in self._partners:
            if partner.source_program == source and partner.target_program == target:
                redemptions = self._redemptions.get(target, [])
                for redemption in redemptions:
                    source_points = int(redemption.points_required / partner.effective_ratio)
                    cpp = redemption.cash_value / source_points * 100 if source_points > 0 else 0.0
                    paths.append(
                        TransferPath(
                            steps=(partner,),
                            redemption=redemption,
                            source_points_needed=source_points,
                            effective_cpp=cpp,
                            total_hops=1,
                        )
                    )
        # Two-hop paths: source -> intermediate -> target
        for p1 in self._partners:
            if p1.source_program != source:
                continue
            for p2 in self._partners:
                if p2.source_program != p1.target_program or p2.target_program != target:
                    continue
                redemptions = self._redemptions.get(target, [])
                for redemption in redemptions:
                    combined_ratio = p1.effective_ratio * p2.effective_ratio
                    source_points = int(redemption.points_required / combined_ratio)
                    cpp = redemption.cash_value / source_points * 100 if source_points > 0 else 0.0
                    paths.append(
                        TransferPath(
                            steps=(p1, p2),
                            redemption=redemption,
                            source_points_needed=source_points,
                            effective_cpp=cpp,
                            total_hops=2,
                        )
                    )
        return sorted(paths, key=lambda p: p.effective_cpp, reverse=True)

    def get_ratio(self, source: str, target: str) -> float | None:
        """Get direct transfer ratio between two programs, or None if no direct link."""
        for partner in self._partners:
            if partner.source_program == source and partner.target_program == target:
                return partner.effective_ratio
        return None

    def get_partners_from(self, source: str) -> list[TransferPartner]:
        """Get all outbound transfer partners from a source program."""
        return [p for p in self._partners if p.source_program == source]
