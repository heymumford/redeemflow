"""RED tests for the valuations domain model and calculator logic.

Beck: Write the test you wish you had. These define the behavior contract.
Fowler: Test the domain, not the framework.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from redeemflow.valuations.models import CreditCard, ProgramValuation, ValuationSource


class TestProgramValuation:
    def test_create_valuation_with_all_sources(self):
        v = ProgramValuation(
            program_code="chase-ur",
            program_name="Chase Ultimate Rewards",
            valuations={
                ValuationSource.TPG: Decimal("2.0"),
                ValuationSource.OMAAT: Decimal("1.7"),
                ValuationSource.NERDWALLET: Decimal("1.5"),
                ValuationSource.UPGRADED_POINTS: Decimal("2.0"),
            },
        )
        assert v.program_code == "chase-ur"
        assert len(v.valuations) == 4

    def test_median_cpp_even_sources(self):
        v = ProgramValuation(
            program_code="chase-ur",
            program_name="Chase Ultimate Rewards",
            valuations={
                ValuationSource.TPG: Decimal("2.0"),
                ValuationSource.OMAAT: Decimal("1.7"),
                ValuationSource.NERDWALLET: Decimal("1.5"),
                ValuationSource.UPGRADED_POINTS: Decimal("2.0"),
            },
        )
        # sorted: 1.5, 1.7, 2.0, 2.0 → median = (1.7 + 2.0) / 2 = 1.85
        assert v.median_cpp == Decimal("1.85")

    def test_min_and_max_cpp(self):
        v = ProgramValuation(
            program_code="chase-ur",
            program_name="Chase Ultimate Rewards",
            valuations={
                ValuationSource.TPG: Decimal("2.0"),
                ValuationSource.OMAAT: Decimal("1.7"),
                ValuationSource.NERDWALLET: Decimal("1.5"),
                ValuationSource.UPGRADED_POINTS: Decimal("2.0"),
            },
        )
        assert v.min_cpp == Decimal("1.5")
        assert v.max_cpp == Decimal("2.0")

    def test_dollar_value_at_median(self):
        v = ProgramValuation(
            program_code="chase-ur",
            program_name="Chase Ultimate Rewards",
            valuations={
                ValuationSource.TPG: Decimal("2.0"),
                ValuationSource.OMAAT: Decimal("1.7"),
                ValuationSource.NERDWALLET: Decimal("1.5"),
                ValuationSource.UPGRADED_POINTS: Decimal("2.0"),
            },
        )
        # 50000 points at 1.85 cpp = 50000 * 1.85 / 100 = $925.00
        assert v.dollar_value(50000) == Decimal("925.00")

    def test_dollar_value_range(self):
        v = ProgramValuation(
            program_code="chase-ur",
            program_name="Chase Ultimate Rewards",
            valuations={
                ValuationSource.TPG: Decimal("2.0"),
                ValuationSource.OMAAT: Decimal("1.7"),
                ValuationSource.NERDWALLET: Decimal("1.5"),
                ValuationSource.UPGRADED_POINTS: Decimal("2.0"),
            },
        )
        low, high = v.dollar_value_range(50000)
        assert low == Decimal("750.00")  # 50000 * 1.5 / 100
        assert high == Decimal("1000.00")  # 50000 * 2.0 / 100

    def test_cash_back_value(self):
        v = ProgramValuation(
            program_code="chase-ur",
            program_name="Chase Ultimate Rewards",
            valuations={ValuationSource.TPG: Decimal("2.0")},
            cash_back_cpp=Decimal("1.0"),
        )
        assert v.cash_back_value(50000) == Decimal("500.00")

    def test_opportunity_cost(self):
        v = ProgramValuation(
            program_code="chase-ur",
            program_name="Chase Ultimate Rewards",
            valuations={
                ValuationSource.TPG: Decimal("2.0"),
                ValuationSource.OMAAT: Decimal("1.7"),
                ValuationSource.NERDWALLET: Decimal("1.5"),
                ValuationSource.UPGRADED_POINTS: Decimal("2.0"),
            },
            cash_back_cpp=Decimal("1.0"),
        )
        # median value ($925) - cash back ($500) = $425 left on table if cash back
        assert v.opportunity_cost(50000) == Decimal("425.00")

    def test_empty_valuations_raises(self):
        with pytest.raises(ValueError, match="at least one"):
            ProgramValuation(
                program_code="chase-ur",
                program_name="Chase UR",
                valuations={},
            )

    def test_single_source_median_equals_that_source(self):
        v = ProgramValuation(
            program_code="delta",
            program_name="Delta SkyMiles",
            valuations={ValuationSource.OMAAT: Decimal("1.1")},
        )
        assert v.median_cpp == Decimal("1.1")


class TestCreditCard:
    def test_create_card(self):
        card = CreditCard(
            name="Chase Sapphire Reserve",
            issuer="Chase",
            annual_fee=Decimal("550"),
            earn_rates={"travel": Decimal("3.0"), "dining": Decimal("3.0"), "other": Decimal("1.0")},
            credits={"travel_credit": Decimal("300")},
            currency="chase-ur",
        )
        assert card.name == "Chase Sapphire Reserve"
        assert card.net_annual_fee == Decimal("250")

    def test_net_fee_with_multiple_credits(self):
        card = CreditCard(
            name="Amex Platinum",
            issuer="Amex",
            annual_fee=Decimal("695"),
            earn_rates={"flights": Decimal("5.0"), "other": Decimal("1.0")},
            credits={"airline_credit": Decimal("200"), "hotel_credit": Decimal("200"), "uber_credit": Decimal("200")},
            currency="amex-mr",
        )
        assert card.net_annual_fee == Decimal("95")

    def test_earn_for_category(self):
        card = CreditCard(
            name="Amex Gold",
            issuer="Amex",
            annual_fee=Decimal("325"),
            earn_rates={"dining": Decimal("4.0"), "groceries": Decimal("4.0"), "other": Decimal("1.0")},
            credits={"dining_credit": Decimal("120")},
            currency="amex-mr",
        )
        # $1000 on dining at 4x = 4000 points
        assert card.points_earned("dining", Decimal("1000")) == 4000
        # Unknown category falls back to "other"
        assert card.points_earned("gas", Decimal("1000")) == 1000

    def test_annual_value_estimate(self):
        card = CreditCard(
            name="Chase Sapphire Reserve",
            issuer="Chase",
            annual_fee=Decimal("550"),
            earn_rates={"travel": Decimal("3.0"), "dining": Decimal("3.0"), "other": Decimal("1.0")},
            credits={"travel_credit": Decimal("300")},
            currency="chase-ur",
        )
        spend = {"travel": Decimal("5000"), "dining": Decimal("6000"), "other": Decimal("12000")}
        # travel: 15000 pts, dining: 18000 pts, other: 12000 pts = 45000 pts
        # At 2.0 cpp = $900 value, minus $550 fee + $300 credit = net $650
        result = card.annual_value(spend, cpp=Decimal("2.0"))
        assert result.total_points == 45000
        assert result.points_value == Decimal("900.00")
        assert result.net_value == Decimal("650.00")
