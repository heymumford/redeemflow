"""Seed data — real-world transfer partnerships and redemption sweet spots.

All data is public knowledge from loyalty program websites and community forums.
Expanded to include all Big 6 currencies (Chase UR, Amex MR, Citi TY, Capital One, Bilt, Wells Fargo).
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
    TransferPartner(source_program="chase-ur", target_program="air-canada", transfer_ratio=1.0),
    TransferPartner(source_program="chase-ur", target_program="jetblue", transfer_ratio=1.0),
    TransferPartner(source_program="chase-ur", target_program="ihg", transfer_ratio=1.0),
    TransferPartner(source_program="chase-ur", target_program="marriott", transfer_ratio=1.0),
]

AMEX_MR_PARTNERS: list[TransferPartner] = [
    TransferPartner(source_program="amex-mr", target_program="delta", transfer_ratio=1.0),
    TransferPartner(source_program="amex-mr", target_program="ana", transfer_ratio=1.0),
    TransferPartner(source_program="amex-mr", target_program="british-airways", transfer_ratio=1.0),
    TransferPartner(source_program="amex-mr", target_program="hilton", transfer_ratio=2.0),
    TransferPartner(source_program="amex-mr", target_program="singapore", transfer_ratio=1.0),
    TransferPartner(source_program="amex-mr", target_program="virgin-atlantic", transfer_ratio=1.0),
    TransferPartner(source_program="amex-mr", target_program="air-france-klm", transfer_ratio=1.0),
    TransferPartner(source_program="amex-mr", target_program="air-canada", transfer_ratio=1.0),
    TransferPartner(source_program="amex-mr", target_program="jetblue", transfer_ratio=1.0),
    TransferPartner(source_program="amex-mr", target_program="marriott", transfer_ratio=1.0),
]

CITI_TY_PARTNERS: list[TransferPartner] = [
    TransferPartner(source_program="citi-ty", target_program="jetblue", transfer_ratio=1.0),
    TransferPartner(source_program="citi-ty", target_program="singapore", transfer_ratio=1.0),
    TransferPartner(source_program="citi-ty", target_program="turkish", transfer_ratio=1.0),
    TransferPartner(source_program="citi-ty", target_program="air-france-klm", transfer_ratio=1.0),
    TransferPartner(source_program="citi-ty", target_program="virgin-atlantic", transfer_ratio=1.0),
    TransferPartner(source_program="citi-ty", target_program="american", transfer_ratio=1.0),
]

CAPITAL_ONE_PARTNERS: list[TransferPartner] = [
    TransferPartner(source_program="capital-one", target_program="air-canada", transfer_ratio=1.0),
    TransferPartner(source_program="capital-one", target_program="turkish", transfer_ratio=1.0),
    TransferPartner(source_program="capital-one", target_program="british-airways", transfer_ratio=1.0),
    TransferPartner(source_program="capital-one", target_program="singapore", transfer_ratio=1.0),
    TransferPartner(source_program="capital-one", target_program="air-france-klm", transfer_ratio=1.0),
    TransferPartner(source_program="capital-one", target_program="virgin-atlantic", transfer_ratio=1.0),
]

BILT_PARTNERS: list[TransferPartner] = [
    TransferPartner(source_program="bilt", target_program="hyatt", transfer_ratio=1.0),
    TransferPartner(source_program="bilt", target_program="united", transfer_ratio=1.0),
    TransferPartner(source_program="bilt", target_program="american", transfer_ratio=1.0),
    TransferPartner(source_program="bilt", target_program="air-canada", transfer_ratio=1.0),
    TransferPartner(source_program="bilt", target_program="turkish", transfer_ratio=1.0),
    TransferPartner(source_program="bilt", target_program="air-france-klm", transfer_ratio=1.0),
    TransferPartner(source_program="bilt", target_program="alaska", transfer_ratio=1.0),
    TransferPartner(source_program="bilt", target_program="ihg", transfer_ratio=1.0),
    TransferPartner(source_program="bilt", target_program="marriott", transfer_ratio=1.0),
]

WELLS_FARGO_PARTNERS: list[TransferPartner] = [
    TransferPartner(source_program="wells-fargo", target_program="british-airways", transfer_ratio=1.0),
    TransferPartner(source_program="wells-fargo", target_program="air-france-klm", transfer_ratio=1.0),
    TransferPartner(source_program="wells-fargo", target_program="jetblue", transfer_ratio=1.0),
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
        source_program="marriott", target_program="delta", transfer_ratio=1.0 / 3.0, min_transfer=3000, is_instant=False
    ),
    TransferPartner(
        source_program="marriott", target_program="ana", transfer_ratio=1.0 / 3.0, min_transfer=3000, is_instant=False
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
    CHASE_UR_PARTNERS
    + AMEX_MR_PARTNERS
    + CITI_TY_PARTNERS
    + CAPITAL_ONE_PARTNERS
    + BILT_PARTNERS
    + WELLS_FARGO_PARTNERS
    + MARRIOTT_PARTNERS
)

# --- Redemption Sweet Spots ---

REDEMPTION_OPTIONS: list[RedemptionOption] = [
    # Hotels
    RedemptionOption(
        program="hyatt",
        description="Hyatt Category 1-4 hotels",
        points_required=8000,
        cash_value=240.0,
        availability="high",
    ),
    RedemptionOption(
        program="hyatt",
        description="Park Hyatt luxury (Cat 7-8)",
        points_required=30000,
        cash_value=900.0,
        availability="medium",
    ),
    RedemptionOption(
        program="hyatt",
        description="Hyatt all-inclusive Ziva/Zilara",
        points_required=25000,
        cash_value=750.0,
        availability="medium",
    ),
    RedemptionOption(
        program="marriott",
        description="Marriott Cat 5-6 properties",
        points_required=40000,
        cash_value=300.0,
        availability="high",
    ),
    RedemptionOption(
        program="hilton",
        description="Hilton 5th night free aspiration",
        points_required=380000,
        cash_value=2000.0,
        availability="medium",
    ),
    RedemptionOption(
        program="ihg",
        description="IHG 4th night free award",
        points_required=120000,
        cash_value=600.0,
        availability="high",
    ),
    # Airlines — premium cabin
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
        program="virgin-atlantic",
        description="ANA First via Virgin Atlantic",
        points_required=60000,
        cash_value=16500.0,
        availability="low",
    ),
    RedemptionOption(
        program="virgin-atlantic",
        description="Virgin Atlantic Upper Class LHR-JFK",
        points_required=47500,
        cash_value=3800.0,
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
        program="delta",
        description="Delta One transatlantic",
        points_required=85000,
        cash_value=4250.0,
        availability="medium",
    ),
    RedemptionOption(
        program="american",
        description="AA Qatar Qsuite JFK-DOH",
        points_required=70000,
        cash_value=6000.0,
        availability="medium",
    ),
    RedemptionOption(
        program="american",
        description="AA JAL First Class to Japan",
        points_required=80000,
        cash_value=12000.0,
        availability="low",
    ),
    # Airlines — economy sweet spots
    RedemptionOption(
        program="turkish",
        description="Turkish domestic US flights",
        points_required=7500,
        cash_value=225.0,
        availability="high",
    ),
    RedemptionOption(
        program="british-airways",
        description="BA short-haul Avios flights",
        points_required=6000,
        cash_value=150.0,
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
        program="air-canada",
        description="Aeroplan business class transatlantic with stopover",
        points_required=70000,
        cash_value=5000.0,
        availability="medium",
    ),
    RedemptionOption(
        program="alaska",
        description="Alaska Cathay Pacific First HKG",
        points_required=70000,
        cash_value=10000.0,
        availability="low",
    ),
    RedemptionOption(
        program="jetblue",
        description="JetBlue Mint transcon",
        points_required=30000,
        cash_value=1200.0,
        availability="medium",
    ),
    RedemptionOption(
        program="southwest",
        description="Southwest Companion Pass value",
        points_required=60000,
        cash_value=2400.0,
        availability="high",
    ),
]
