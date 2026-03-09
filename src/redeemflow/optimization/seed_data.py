"""Seed data — real-world transfer partnerships and redemption sweet spots.

All data is public knowledge from loyalty program websites and community forums.
"""

from __future__ import annotations

from redeemflow.optimization.models import RedemptionOption, TransferPartner

# --- Transfer Partners ---
# Format: source_program -> target_program at transfer_ratio

CHASE_UR_PARTNERS: list[TransferPartner] = [
    TransferPartner(source_program="chase-ur", target_program="united", transfer_ratio=1.0),
    TransferPartner(source_program="chase-ur", target_program="hyatt", transfer_ratio=1.0),
    TransferPartner(source_program="chase-ur", target_program="southwest", transfer_ratio=1.0),
    TransferPartner(source_program="chase-ur", target_program="british-airways", transfer_ratio=1.0),
    TransferPartner(source_program="chase-ur", target_program="air-france-klm", transfer_ratio=1.0),
    TransferPartner(source_program="chase-ur", target_program="singapore", transfer_ratio=1.0),
    TransferPartner(source_program="chase-ur", target_program="virgin-atlantic", transfer_ratio=1.0),
]

AMEX_MR_PARTNERS: list[TransferPartner] = [
    TransferPartner(source_program="amex-mr", target_program="delta", transfer_ratio=1.0),
    TransferPartner(source_program="amex-mr", target_program="ana", transfer_ratio=1.0),
    TransferPartner(source_program="amex-mr", target_program="british-airways", transfer_ratio=1.0),
    TransferPartner(source_program="amex-mr", target_program="hilton", transfer_ratio=2.0),
    TransferPartner(source_program="amex-mr", target_program="singapore", transfer_ratio=1.0),
    TransferPartner(source_program="amex-mr", target_program="virgin-atlantic", transfer_ratio=1.0),
    TransferPartner(source_program="amex-mr", target_program="air-france-klm", transfer_ratio=1.0),
]

CITI_TY_PARTNERS: list[TransferPartner] = [
    TransferPartner(source_program="citi-ty", target_program="jetblue", transfer_ratio=1.0),
    TransferPartner(source_program="citi-ty", target_program="singapore", transfer_ratio=1.0),
    TransferPartner(source_program="citi-ty", target_program="turkish", transfer_ratio=1.0),
    TransferPartner(source_program="citi-ty", target_program="air-france-klm", transfer_ratio=1.0),
    TransferPartner(source_program="citi-ty", target_program="virgin-atlantic", transfer_ratio=1.0),
]

CAPITAL_ONE_PARTNERS: list[TransferPartner] = [
    TransferPartner(source_program="capital-one", target_program="air-canada", transfer_ratio=1.0),
    TransferPartner(source_program="capital-one", target_program="turkish", transfer_ratio=1.0),
    TransferPartner(source_program="capital-one", target_program="british-airways", transfer_ratio=1.0),
    TransferPartner(source_program="capital-one", target_program="singapore", transfer_ratio=1.0),
    TransferPartner(source_program="capital-one", target_program="air-france-klm", transfer_ratio=1.0),
]

# Marriott transfers at 3:1 with a 5K bonus per 60K transferred
MARRIOTT_PARTNERS: list[TransferPartner] = [
    TransferPartner(
        source_program="marriott",
        target_program="united",
        transfer_ratio=1.0 / 3.0,
        min_transfer=3000,
        is_instant=False,
    ),
    TransferPartner(
        source_program="marriott",
        target_program="delta",
        transfer_ratio=1.0 / 3.0,
        min_transfer=3000,
        is_instant=False,
    ),
    TransferPartner(
        source_program="marriott",
        target_program="ana",
        transfer_ratio=1.0 / 3.0,
        min_transfer=3000,
        is_instant=False,
    ),
    TransferPartner(
        source_program="marriott",
        target_program="british-airways",
        transfer_ratio=1.0 / 3.0,
        min_transfer=3000,
        is_instant=False,
    ),
    TransferPartner(
        source_program="marriott",
        target_program="air-france-klm",
        transfer_ratio=1.0 / 3.0,
        min_transfer=3000,
        is_instant=False,
    ),
    TransferPartner(
        source_program="marriott",
        target_program="singapore",
        transfer_ratio=1.0 / 3.0,
        min_transfer=3000,
        is_instant=False,
    ),
    TransferPartner(
        source_program="marriott",
        target_program="turkish",
        transfer_ratio=1.0 / 3.0,
        min_transfer=3000,
        is_instant=False,
    ),
]

ALL_PARTNERS: list[TransferPartner] = (
    CHASE_UR_PARTNERS + AMEX_MR_PARTNERS + CITI_TY_PARTNERS + CAPITAL_ONE_PARTNERS + MARRIOTT_PARTNERS
)

# --- Redemption Sweet Spots ---

REDEMPTION_OPTIONS: list[RedemptionOption] = [
    RedemptionOption(
        program="hyatt",
        description="Hyatt Category 1-4 hotels",
        points_required=8000,
        cash_value=240.0,
        availability="high",
    ),
    RedemptionOption(
        program="ana",
        description="ANA First Class SFO-NRT",
        points_required=110000,
        cash_value=16500.0,
        availability="low",
    ),
    RedemptionOption(
        program="singapore",
        description="Singapore Suites JFK-SIN",
        points_required=156000,
        cash_value=12480.0,
        availability="low",
    ),
    RedemptionOption(
        program="turkish",
        description="Turkish domestic US flights",
        points_required=7500,
        cash_value=225.0,
        availability="high",
    ),
    RedemptionOption(
        program="air-france-klm",
        description="Air France Promo Awards Europe",
        points_required=20000,
        cash_value=500.0,
        availability="medium",
    ),
    RedemptionOption(
        program="united",
        description="United Polaris Business SFO-NRT",
        points_required=80000,
        cash_value=5600.0,
        availability="medium",
    ),
    RedemptionOption(
        program="british-airways",
        description="BA short-haul Avios flights",
        points_required=6000,
        cash_value=150.0,
        availability="high",
    ),
    RedemptionOption(
        program="virgin-atlantic",
        description="Virgin Atlantic Upper Class LHR-JFK",
        points_required=47500,
        cash_value=3800.0,
        availability="medium",
    ),
    RedemptionOption(
        program="delta",
        description="Delta One transatlantic",
        points_required=85000,
        cash_value=4250.0,
        availability="medium",
    ),
    RedemptionOption(
        program="hyatt",
        description="Park Hyatt luxury (Cat 7-8)",
        points_required=30000,
        cash_value=900.0,
        availability="medium",
    ),
]
