"""Valuations seed data — CPP valuations from 4 sources, credit card catalog.

All data from public sources (TPG, OMAAT, NerdWallet, Upgraded Points) as of March 2026.
"""

from __future__ import annotations

from decimal import Decimal

from redeemflow.valuations.models import CreditCard, ProgramValuation, ValuationSource

# --- Program Valuations (CPP from multiple sources) ---

PROGRAM_VALUATIONS: dict[str, ProgramValuation] = {
    "chase-ur": ProgramValuation(
        program_code="chase-ur",
        program_name="Chase Ultimate Rewards",
        valuations={
            ValuationSource.TPG: Decimal("2.0"),
            ValuationSource.OMAAT: Decimal("1.7"),
            ValuationSource.NERDWALLET: Decimal("1.5"),
            ValuationSource.UPGRADED_POINTS: Decimal("2.0"),
        },
        cash_back_cpp=Decimal("1.0"),
    ),
    "amex-mr": ProgramValuation(
        program_code="amex-mr",
        program_name="Amex Membership Rewards",
        valuations={
            ValuationSource.TPG: Decimal("2.0"),
            ValuationSource.OMAAT: Decimal("1.7"),
            ValuationSource.UPGRADED_POINTS: Decimal("2.0"),
        },
        cash_back_cpp=Decimal("0.6"),
    ),
    "citi-ty": ProgramValuation(
        program_code="citi-ty",
        program_name="Citi ThankYou Points",
        valuations={
            ValuationSource.TPG: Decimal("1.9"),
            ValuationSource.OMAAT: Decimal("1.7"),
        },
        cash_back_cpp=Decimal("1.0"),
    ),
    "capital-one": ProgramValuation(
        program_code="capital-one",
        program_name="Capital One Miles",
        valuations={
            ValuationSource.TPG: Decimal("1.85"),
            ValuationSource.OMAAT: Decimal("1.7"),
        },
        cash_back_cpp=Decimal("1.0"),
    ),
    "bilt": ProgramValuation(
        program_code="bilt",
        program_name="Bilt Rewards",
        valuations={
            ValuationSource.TPG: Decimal("2.2"),
            ValuationSource.OMAAT: Decimal("1.7"),
            ValuationSource.UPGRADED_POINTS: Decimal("1.8"),
        },
        cash_back_cpp=Decimal("0.5"),
    ),
    "wells-fargo": ProgramValuation(
        program_code="wells-fargo",
        program_name="Wells Fargo Rewards",
        valuations={
            ValuationSource.TPG: Decimal("1.65"),
        },
        cash_back_cpp=Decimal("1.0"),
    ),
    "united": ProgramValuation(
        program_code="united",
        program_name="United MileagePlus",
        valuations={
            ValuationSource.OMAAT: Decimal("1.1"),
            ValuationSource.NERDWALLET: Decimal("1.2"),
        },
    ),
    "delta": ProgramValuation(
        program_code="delta",
        program_name="Delta SkyMiles",
        valuations={
            ValuationSource.OMAAT: Decimal("1.1"),
            ValuationSource.NERDWALLET: Decimal("1.2"),
            ValuationSource.TPG: Decimal("1.2"),
        },
    ),
    "american": ProgramValuation(
        program_code="american",
        program_name="American AAdvantage",
        valuations={
            ValuationSource.OMAAT: Decimal("1.5"),
            ValuationSource.TPG: Decimal("1.55"),
        },
    ),
    "southwest": ProgramValuation(
        program_code="southwest",
        program_name="Southwest Rapid Rewards",
        valuations={
            ValuationSource.OMAAT: Decimal("1.2"),
            ValuationSource.TPG: Decimal("1.3"),
        },
    ),
    "hyatt": ProgramValuation(
        program_code="hyatt",
        program_name="World of Hyatt",
        valuations={
            ValuationSource.OMAAT: Decimal("1.5"),
            ValuationSource.NERDWALLET: Decimal("1.8"),
            ValuationSource.TPG: Decimal("2.0"),
        },
    ),
    "marriott": ProgramValuation(
        program_code="marriott",
        program_name="Marriott Bonvoy",
        valuations={
            ValuationSource.OMAAT: Decimal("0.7"),
            ValuationSource.NERDWALLET: Decimal("0.8"),
            ValuationSource.TPG: Decimal("0.7"),
        },
    ),
    "hilton": ProgramValuation(
        program_code="hilton",
        program_name="Hilton Honors",
        valuations={
            ValuationSource.OMAAT: Decimal("0.5"),
            ValuationSource.NERDWALLET: Decimal("0.4"),
            ValuationSource.TPG: Decimal("0.5"),
        },
    ),
    "ihg": ProgramValuation(
        program_code="ihg",
        program_name="IHG One Rewards",
        valuations={
            ValuationSource.OMAAT: Decimal("0.5"),
            ValuationSource.TPG: Decimal("0.6"),
        },
    ),
    "ana": ProgramValuation(
        program_code="ana",
        program_name="ANA Mileage Club",
        valuations={ValuationSource.OMAAT: Decimal("1.4")},
    ),
    "british-airways": ProgramValuation(
        program_code="british-airways",
        program_name="British Airways Avios",
        valuations={ValuationSource.OMAAT: Decimal("1.3")},
    ),
    "virgin-atlantic": ProgramValuation(
        program_code="virgin-atlantic",
        program_name="Virgin Atlantic Flying Club",
        valuations={ValuationSource.OMAAT: Decimal("1.1")},
    ),
    "air-france-klm": ProgramValuation(
        program_code="air-france-klm",
        program_name="Air France/KLM Flying Blue",
        valuations={ValuationSource.OMAAT: Decimal("1.3")},
    ),
    "singapore": ProgramValuation(
        program_code="singapore",
        program_name="Singapore KrisFlyer",
        valuations={ValuationSource.OMAAT: Decimal("1.4")},
    ),
    "turkish": ProgramValuation(
        program_code="turkish",
        program_name="Turkish Miles&Smiles",
        valuations={ValuationSource.OMAAT: Decimal("1.3")},
    ),
    "air-canada": ProgramValuation(
        program_code="air-canada",
        program_name="Air Canada Aeroplan",
        valuations={ValuationSource.OMAAT: Decimal("1.5")},
    ),
    "jetblue": ProgramValuation(
        program_code="jetblue",
        program_name="JetBlue TrueBlue",
        valuations={ValuationSource.OMAAT: Decimal("1.3")},
    ),
    "alaska": ProgramValuation(
        program_code="alaska",
        program_name="Alaska Atmos Rewards",
        valuations={
            ValuationSource.OMAAT: Decimal("1.5"),
            ValuationSource.NERDWALLET: Decimal("1.2"),
        },
    ),
}


# --- Credit Card Catalog ---

CREDIT_CARDS: dict[str, CreditCard] = {
    "chase-sapphire-reserve": CreditCard(
        name="Chase Sapphire Reserve",
        issuer="Chase",
        annual_fee=Decimal("550"),
        earn_rates={"travel": Decimal("3.0"), "dining": Decimal("3.0"), "other": Decimal("1.0")},
        credits={"travel_credit": Decimal("300")},
        currency="chase-ur",
    ),
    "chase-sapphire-preferred": CreditCard(
        name="Chase Sapphire Preferred",
        issuer="Chase",
        annual_fee=Decimal("95"),
        earn_rates={
            "travel": Decimal("2.0"),
            "dining": Decimal("3.0"),
            "streaming": Decimal("3.0"),
            "other": Decimal("1.0"),
        },
        credits={"hotel_credit": Decimal("50")},
        currency="chase-ur",
    ),
    "chase-ink-preferred": CreditCard(
        name="Chase Ink Business Preferred",
        issuer="Chase",
        annual_fee=Decimal("95"),
        earn_rates={
            "travel": Decimal("3.0"),
            "shipping": Decimal("3.0"),
            "internet": Decimal("3.0"),
            "advertising": Decimal("3.0"),
            "other": Decimal("1.0"),
        },
        credits={},
        currency="chase-ur",
    ),
    "amex-platinum": CreditCard(
        name="Amex Platinum",
        issuer="Amex",
        annual_fee=Decimal("695"),
        earn_rates={"flights": Decimal("5.0"), "hotels_amex": Decimal("5.0"), "other": Decimal("1.0")},
        credits={"airline_credit": Decimal("200"), "hotel_credit": Decimal("200"), "uber_credit": Decimal("200")},
        currency="amex-mr",
    ),
    "amex-gold": CreditCard(
        name="Amex Gold",
        issuer="Amex",
        annual_fee=Decimal("325"),
        earn_rates={
            "dining": Decimal("4.0"),
            "groceries": Decimal("4.0"),
            "flights": Decimal("3.0"),
            "other": Decimal("1.0"),
        },
        credits={"dining_credit": Decimal("120"), "uber_credit": Decimal("120")},
        currency="amex-mr",
    ),
    "amex-business-gold": CreditCard(
        name="Amex Business Gold",
        issuer="Amex",
        annual_fee=Decimal("375"),
        earn_rates={
            "flights": Decimal("4.0"),
            "advertising": Decimal("4.0"),
            "shipping": Decimal("4.0"),
            "other": Decimal("1.0"),
        },
        credits={},
        currency="amex-mr",
    ),
    "capital-one-venture-x": CreditCard(
        name="Capital One Venture X",
        issuer="Capital One",
        annual_fee=Decimal("395"),
        earn_rates={"hotels_portal": Decimal("10.0"), "cars_portal": Decimal("10.0"), "other": Decimal("2.0")},
        credits={"travel_credit": Decimal("300")},
        currency="capital-one",
    ),
    "citi-strata-premier": CreditCard(
        name="Citi Strata Premier",
        issuer="Citi",
        annual_fee=Decimal("95"),
        earn_rates={
            "travel": Decimal("3.0"),
            "dining": Decimal("3.0"),
            "groceries": Decimal("3.0"),
            "gas": Decimal("3.0"),
            "other": Decimal("1.0"),
        },
        credits={"hotel_credit": Decimal("100")},
        currency="citi-ty",
    ),
    "bilt-mastercard": CreditCard(
        name="Bilt Mastercard",
        issuer="Bilt",
        annual_fee=Decimal("0"),
        earn_rates={
            "rent": Decimal("1.0"),
            "dining": Decimal("3.0"),
            "travel": Decimal("2.0"),
            "other": Decimal("1.0"),
        },
        credits={},
        currency="bilt",
    ),
}
