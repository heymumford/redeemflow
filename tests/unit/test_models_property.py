"""Property-based tests for all Sprint 1 core entity models.

Uses hypothesis to verify invariants hold across the entire input space.
Zero I/O — these test pure domain logic only.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from redeemflow.billing.models import Subscription, SubscriptionTier
from redeemflow.charity.donation_flow import Donation, DonationStatus
from redeemflow.charity.models import (
    VALID_US_STATES,
    CharityCategory,
    CharityOrganization,
)
from redeemflow.community.models import CommunityPool, Pledge, PoolStatus
from redeemflow.optimization.models import (
    ActionType,
    OptimizationAction,
    TransferPartner,
)
from redeemflow.portfolio.models import (
    LoyaltyProgram,
    PointBalance,
    ProgramCategory,
    UserPortfolio,
)
from redeemflow.valuations.models import ProgramValuation, ValuationSource

# ---------------------------------------------------------------------------
# Shared strategies
# ---------------------------------------------------------------------------

_nonempty_text = st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z")))
_program_code = st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz-0123456789")
_positive_int = st.integers(min_value=1, max_value=10_000_000)
_nonneg_int = st.integers(min_value=0, max_value=10_000_000)
_positive_decimal = st.decimals(
    min_value=Decimal("0.01"),
    max_value=Decimal("99999"),
    places=2,
    allow_nan=False,
    allow_infinity=False,
)
_positive_float = st.floats(
    min_value=0.01,
    max_value=1000.0,
    allow_nan=False,
    allow_infinity=False,
)
_cpp_float = st.floats(
    min_value=0.1,
    max_value=10.0,
    allow_nan=False,
    allow_infinity=False,
)


def _dec_st(lo: str, hi: str, places: int = 1) -> st.SearchStrategy:
    """Shorthand for bounded Decimal strategies."""
    return st.decimals(
        min_value=Decimal(lo),
        max_value=Decimal(hi),
        places=places,
        allow_nan=False,
        allow_infinity=False,
    )


_us_state = st.sampled_from(sorted(VALID_US_STATES))
_category = st.sampled_from(list(ProgramCategory))
_charity_category = st.sampled_from(list(CharityCategory))
_tier = st.sampled_from(list(SubscriptionTier))
_action_type = st.sampled_from(list(ActionType))
_valuation_source = st.sampled_from(list(ValuationSource))
_iso_timestamp = st.just("2026-03-11T00:00:00+00:00")


# ---------------------------------------------------------------------------
# 1. LoyaltyProgram
# ---------------------------------------------------------------------------


class TestLoyaltyProgramProperties:
    @given(code=_program_code, name=_nonempty_text, category=_category)
    @settings(max_examples=100)
    def test_frozen_immutability(self, code: str, name: str, category: ProgramCategory):
        prog = LoyaltyProgram(code=code, name=name, category=category)
        with pytest.raises(AttributeError):
            prog.code = "changed"  # type: ignore[misc]

    @given(code=_program_code, name=_nonempty_text, category=_category)
    @settings(max_examples=100)
    def test_equality_by_code(self, code: str, name: str, category: ProgramCategory):
        a = LoyaltyProgram(code=code, name=name, category=category)
        b = LoyaltyProgram(code=code, name="different name", category=ProgramCategory.HOTEL)
        assert a == b
        assert hash(a) == hash(b)

    @given(
        code=_program_code,
        name=_nonempty_text,
        cpp_min=st.floats(min_value=0.1, max_value=5.0, allow_nan=False, allow_infinity=False),
        cpp_max=st.floats(min_value=5.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_cpp_bounds_valid_range(self, code: str, name: str, cpp_min: float, cpp_max: float):
        prog = LoyaltyProgram(code=code, name=name, cpp_min=cpp_min, cpp_max=cpp_max)
        assert prog.cpp_min <= prog.cpp_max

    def test_cpp_min_below_bound_raises(self):
        with pytest.raises(ValueError, match="cpp_min"):
            LoyaltyProgram(code="test", name="Test", cpp_min=0.05)

    def test_cpp_max_above_bound_raises(self):
        with pytest.raises(ValueError, match="cpp_max"):
            LoyaltyProgram(code="test", name="Test", cpp_max=15.0)

    def test_cpp_min_exceeds_max_raises(self):
        with pytest.raises(ValueError, match="cpp_min"):
            LoyaltyProgram(code="test", name="Test", cpp_min=5.0, cpp_max=2.0)

    def test_empty_code_raises(self):
        with pytest.raises(ValueError, match="code"):
            LoyaltyProgram(code="", name="Test")

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="name"):
            LoyaltyProgram(code="test", name="")

    @given(code=_program_code, name=_nonempty_text, category=_category)
    @settings(max_examples=50)
    def test_category_enum_roundtrip(self, code: str, name: str, category: ProgramCategory):
        prog = LoyaltyProgram(code=code, name=name, category=category)
        assert prog.category == category
        assert prog.category.value == category.value

    def test_all_categories_constructable(self):
        for cat in ProgramCategory:
            prog = LoyaltyProgram(code=f"test-{cat.value}", name=f"Test {cat.name}", category=cat)
            assert prog.category == cat


# ---------------------------------------------------------------------------
# 2. TransferPartner
# ---------------------------------------------------------------------------


class TestTransferPartnerProperties:
    @given(
        source=_program_code,
        target=_program_code,
        ratio=_positive_float,
        bonus=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_effective_ratio_always_positive(self, source: str, target: str, ratio: float, bonus: float):
        if source == target:
            return  # Skip same source/target
        partner = TransferPartner(
            source_program=source,
            target_program=target,
            transfer_ratio=ratio,
            transfer_bonus=bonus,
        )
        assert partner.effective_ratio > 0

    @given(
        source=_program_code,
        target=_program_code,
        ratio=_positive_float,
    )
    @settings(max_examples=100)
    def test_frozen_immutability(self, source: str, target: str, ratio: float):
        if source == target:
            return
        partner = TransferPartner(source_program=source, target_program=target, transfer_ratio=ratio)
        with pytest.raises(AttributeError):
            partner.transfer_ratio = 0.0  # type: ignore[misc]

    def test_zero_ratio_raises(self):
        with pytest.raises(ValueError, match="transfer_ratio"):
            TransferPartner(source_program="a", target_program="b", transfer_ratio=0.0)

    def test_negative_ratio_raises(self):
        with pytest.raises(ValueError, match="transfer_ratio"):
            TransferPartner(source_program="a", target_program="b", transfer_ratio=-1.0)

    def test_same_source_target_raises(self):
        with pytest.raises(ValueError, match="must differ"):
            TransferPartner(source_program="chase-ur", target_program="chase-ur", transfer_ratio=1.0)

    @given(
        source=_program_code,
        target=_program_code,
        ratio=_positive_float,
        bonus=st.floats(min_value=0.0, max_value=2.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_effective_ratio_formula(self, source: str, target: str, ratio: float, bonus: float):
        if source == target:
            return
        partner = TransferPartner(
            source_program=source,
            target_program=target,
            transfer_ratio=ratio,
            transfer_bonus=bonus,
        )
        expected = ratio * (1.0 + bonus)
        assert partner.effective_ratio == pytest.approx(expected)


# ---------------------------------------------------------------------------
# 3. ProgramValuation (PointValuation)
# ---------------------------------------------------------------------------


class TestProgramValuationProperties:
    @given(
        code=_program_code,
        name=_nonempty_text,
        vals=st.dictionaries(
            keys=_valuation_source,
            values=_dec_st("0.1", "20"),
            min_size=1,
            max_size=4,
        ),
    )
    @settings(max_examples=100)
    def test_min_leq_median_leq_max(self, code: str, name: str, vals: dict):
        v = ProgramValuation(program_code=code, program_name=name, valuations=vals)
        assert v.min_cpp <= v.median_cpp <= v.max_cpp

    @given(
        code=_program_code,
        name=_nonempty_text,
        single_val=_dec_st("0.1", "20"),
        source=_valuation_source,
    )
    @settings(max_examples=50)
    def test_single_source_min_eq_median_eq_max(
        self,
        code: str,
        name: str,
        single_val: Decimal,
        source: ValuationSource,
    ):
        v = ProgramValuation(program_code=code, program_name=name, valuations={source: single_val})
        assert v.min_cpp == v.max_cpp == v.median_cpp

    def test_empty_valuations_raises(self):
        with pytest.raises(ValueError, match="at least one"):
            ProgramValuation(program_code="test", program_name="Test", valuations={})

    @given(
        points=st.integers(min_value=100, max_value=10_000_000),
        cpp=_dec_st("0.5", "5.0"),
    )
    @settings(max_examples=100)
    def test_dollar_value_positive_for_positive_inputs(self, points: int, cpp: Decimal):
        v = ProgramValuation(
            program_code="test",
            program_name="Test",
            valuations={ValuationSource.TPG: cpp},
        )
        dv = v.dollar_value(points)
        assert dv > 0

    @given(
        points=_positive_int,
        cpp_low=_dec_st("0.5", "2.0"),
        cpp_high=_dec_st("2.1", "5.0"),
    )
    @settings(max_examples=100)
    def test_dollar_value_range_low_leq_high(self, points: int, cpp_low: Decimal, cpp_high: Decimal):
        v = ProgramValuation(
            program_code="test",
            program_name="Test",
            valuations={ValuationSource.TPG: cpp_high, ValuationSource.OMAAT: cpp_low},
        )
        low, high = v.dollar_value_range(points)
        assert low <= high

    def test_timestamp_optional(self):
        v = ProgramValuation(
            program_code="test",
            program_name="Test",
            valuations={ValuationSource.TPG: Decimal("2.0")},
        )
        assert v.timestamp is None

    def test_timestamp_set(self):
        v = ProgramValuation(
            program_code="test",
            program_name="Test",
            valuations={ValuationSource.TPG: Decimal("2.0")},
            timestamp="2026-03-11T00:00:00+00:00",
        )
        assert v.timestamp == "2026-03-11T00:00:00+00:00"

    def test_four_named_sources(self):
        v = ProgramValuation(
            program_code="chase-ur",
            program_name="Chase UR",
            valuations={
                ValuationSource.OMAAT: Decimal("1.7"),
                ValuationSource.TPG: Decimal("2.0"),
                ValuationSource.NERDWALLET: Decimal("1.5"),
                ValuationSource.UPGRADED_POINTS: Decimal("2.0"),
            },
        )
        assert len(v.valuations) == 4
        assert v.min_cpp == Decimal("1.5")
        assert v.max_cpp == Decimal("2.0")


# ---------------------------------------------------------------------------
# 4. UserPortfolio + PointBalance (ProgramBalance)
# ---------------------------------------------------------------------------


class TestPointBalanceProperties:
    @given(
        code=_program_code,
        points=_nonneg_int,
        cpp=_dec_st("0.1", "10.0"),
    )
    @settings(max_examples=100)
    def test_estimated_value_nonnegative(self, code: str, points: int, cpp: Decimal):
        b = PointBalance(program_code=code, points=points, cpp_baseline=cpp)
        assert b.estimated_value_cents >= 0
        assert b.estimated_value_dollars >= 0

    @given(
        code=_program_code,
        points=_nonneg_int,
        cpp=_dec_st("0.1", "10.0"),
    )
    @settings(max_examples=100)
    def test_frozen_immutability(self, code: str, points: int, cpp: Decimal):
        b = PointBalance(program_code=code, points=points, cpp_baseline=cpp)
        with pytest.raises(AttributeError):
            b.points = 0  # type: ignore[misc]

    def test_negative_points_raises(self):
        with pytest.raises(ValueError, match="points"):
            PointBalance(program_code="test", points=-1, cpp_baseline=Decimal("1.0"))

    @given(
        code=_program_code,
        points=_nonneg_int,
        cpp=_dec_st("0.1", "10.0"),
    )
    @settings(max_examples=100)
    def test_dollars_equals_cents_divided_by_100(self, code: str, points: int, cpp: Decimal):
        b = PointBalance(program_code=code, points=points, cpp_baseline=cpp)
        assert b.estimated_value_dollars == Decimal(b.estimated_value_cents) / Decimal(100)


class TestUserPortfolioProperties:
    @given(
        user_id=_nonempty_text,
        n_balances=st.integers(min_value=0, max_value=5),
    )
    @settings(max_examples=50)
    def test_total_value_is_sum_of_parts(self, user_id: str, n_balances: int):
        balances = tuple(
            PointBalance(program_code=f"prog-{i}", points=1000 * (i + 1), cpp_baseline=Decimal("1.5"))
            for i in range(n_balances)
        )
        portfolio = UserPortfolio(user_id=user_id, balances=balances)
        expected_cents = sum(b.estimated_value_cents for b in balances)
        assert portfolio.total_estimated_value_cents == expected_cents

    def test_empty_portfolio_zero_value(self):
        portfolio = UserPortfolio(user_id="test-user", balances=())
        assert portfolio.total_estimated_value_cents == 0
        assert portfolio.total_estimated_value_dollars == Decimal("0")

    def test_balance_for_existing_program(self):
        b = PointBalance(program_code="chase-ur", points=50000, cpp_baseline=Decimal("1.5"))
        portfolio = UserPortfolio(user_id="test-user", balances=(b,))
        found = portfolio.balance_for("chase-ur")
        assert found is not None
        assert found.program_code == "chase-ur"

    def test_balance_for_missing_program(self):
        portfolio = UserPortfolio(user_id="test-user", balances=())
        assert portfolio.balance_for("nonexistent") is None

    def test_program_codes(self):
        balances = (
            PointBalance(program_code="chase-ur", points=50000, cpp_baseline=Decimal("1.5")),
            PointBalance(program_code="amex-mr", points=30000, cpp_baseline=Decimal("1.0")),
        )
        portfolio = UserPortfolio(user_id="test-user", balances=balances)
        assert portfolio.program_codes == frozenset({"chase-ur", "amex-mr"})

    def test_frozen_immutability(self):
        portfolio = UserPortfolio(user_id="test-user", balances=())
        with pytest.raises(AttributeError):
            portfolio.user_id = "changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# 5. OptimizationAction
# ---------------------------------------------------------------------------


class TestOptimizationActionProperties:
    @given(
        action_type=_action_type,
        code=_program_code,
        points=_positive_int,
        expected_value=_positive_decimal,
    )
    @settings(max_examples=100)
    def test_frozen_and_valid(self, action_type: ActionType, code: str, points: int, expected_value: Decimal):
        action = OptimizationAction(
            action_type=action_type,
            program_code=code,
            points=points,
            expected_value=expected_value,
            description="test action",
        )
        assert action.expected_value > 0
        with pytest.raises(AttributeError):
            action.points = 0  # type: ignore[misc]

    def test_zero_expected_value_raises(self):
        with pytest.raises(ValueError, match="expected_value"):
            OptimizationAction(
                action_type=ActionType.TRANSFER,
                program_code="chase-ur",
                points=10000,
                expected_value=Decimal("0"),
                description="bad",
            )

    def test_negative_expected_value_raises(self):
        with pytest.raises(ValueError, match="expected_value"):
            OptimizationAction(
                action_type=ActionType.HOLD,
                program_code="chase-ur",
                points=10000,
                expected_value=Decimal("-5.00"),
                description="bad",
            )

    def test_all_action_types_constructable(self):
        for at in ActionType:
            action = OptimizationAction(
                action_type=at,
                program_code="test",
                points=1000,
                expected_value=Decimal("10.00"),
                description=f"test {at.value}",
            )
            assert action.action_type == at

    def test_target_program_optional(self):
        action = OptimizationAction(
            action_type=ActionType.TRANSFER,
            program_code="chase-ur",
            points=10000,
            expected_value=Decimal("150.00"),
            description="transfer to hyatt",
            target_program="hyatt",
        )
        assert action.target_program == "hyatt"

    def test_target_program_default_none(self):
        action = OptimizationAction(
            action_type=ActionType.HOLD,
            program_code="chase-ur",
            points=10000,
            expected_value=Decimal("150.00"),
            description="hold points",
        )
        assert action.target_program is None


# ---------------------------------------------------------------------------
# 6. CharityOrganization (CharityPartner)
# ---------------------------------------------------------------------------


class TestCharityOrganizationProperties:
    @given(
        name=_nonempty_text,
        category=_charity_category,
        state=_us_state,
    )
    @settings(max_examples=100)
    def test_frozen_with_valid_state(self, name: str, category: CharityCategory, state: str):
        org = CharityOrganization(
            name=name,
            category=category,
            state=state,
            national_url="https://example.org",
            is_501c3=True,
        )
        assert org.state in VALID_US_STATES
        with pytest.raises(AttributeError):
            org.name = "changed"  # type: ignore[misc]

    def test_invalid_state_raises(self):
        with pytest.raises(ValueError, match="Invalid US state"):
            CharityOrganization(
                name="Test",
                category=CharityCategory.EDUCATION,
                state="ZZ",
                national_url="https://example.org",
                is_501c3=True,
            )

    def test_valid_ein_format(self):
        org = CharityOrganization(
            name="Test",
            category=CharityCategory.EDUCATION,
            state="CA",
            national_url="https://example.org",
            is_501c3=True,
            ein="12-3456789",
        )
        assert org.ein == "12-3456789"

    def test_invalid_ein_format_raises(self):
        with pytest.raises(ValueError, match="Invalid EIN"):
            CharityOrganization(
                name="Test",
                category=CharityCategory.EDUCATION,
                state="CA",
                national_url="https://example.org",
                is_501c3=True,
                ein="invalid",
            )

    def test_ein_wrong_digit_count_raises(self):
        with pytest.raises(ValueError, match="Invalid EIN"):
            CharityOrganization(
                name="Test",
                category=CharityCategory.EDUCATION,
                state="CA",
                national_url="https://example.org",
                is_501c3=True,
                ein="1-23456789",
            )

    def test_ein_none_is_valid(self):
        org = CharityOrganization(
            name="Test",
            category=CharityCategory.EDUCATION,
            state="CA",
            national_url="https://example.org",
            is_501c3=True,
            ein=None,
        )
        assert org.ein is None

    def test_501c3_flag(self):
        org = CharityOrganization(
            name="Test",
            category=CharityCategory.EDUCATION,
            state="NY",
            national_url="https://example.org",
            is_501c3=False,
        )
        assert org.is_501c3 is False

    @given(state=_us_state)
    @settings(max_examples=51)
    def test_all_valid_states_accepted(self, state: str):
        org = CharityOrganization(
            name="Test",
            category=CharityCategory.COMMUNITY,
            state=state,
            national_url="https://example.org",
            is_501c3=True,
        )
        assert org.state == state


# ---------------------------------------------------------------------------
# 7. Donation (DonationTransaction) + CommunityPool
# ---------------------------------------------------------------------------


class TestDonationProperties:
    @given(
        points=_positive_int,
        dollar_value=_positive_decimal,
    )
    @settings(max_examples=100)
    def test_frozen_with_positive_values(self, points: int, dollar_value: Decimal):
        d = Donation(
            id="don-001",
            user_id="auth0|test",
            charity_name="Test Charity",
            charity_state="CA",
            program_code="chase-ur",
            points_donated=points,
            dollar_value=dollar_value,
            status=DonationStatus.PENDING,
            created_at="2026-03-11T00:00:00Z",
        )
        assert d.points_donated > 0
        assert d.dollar_value > 0
        with pytest.raises(AttributeError):
            d.status = DonationStatus.COMPLETED  # type: ignore[misc]

    def test_zero_points_raises(self):
        with pytest.raises(ValueError, match="points_donated"):
            Donation(
                id="don-001",
                user_id="auth0|test",
                charity_name="Test",
                charity_state="CA",
                program_code="chase-ur",
                points_donated=0,
                dollar_value=Decimal("10.00"),
                status=DonationStatus.PENDING,
                created_at="2026-03-11T00:00:00Z",
            )

    def test_negative_dollar_value_raises(self):
        with pytest.raises(ValueError, match="dollar_value"):
            Donation(
                id="don-001",
                user_id="auth0|test",
                charity_name="Test",
                charity_state="CA",
                program_code="chase-ur",
                points_donated=1000,
                dollar_value=Decimal("-5.00"),
                status=DonationStatus.PENDING,
                created_at="2026-03-11T00:00:00Z",
            )

    def test_cpp_at_donation_optional(self):
        d = Donation(
            id="don-001",
            user_id="auth0|test",
            charity_name="Test",
            charity_state="CA",
            program_code="chase-ur",
            points_donated=1000,
            dollar_value=Decimal("15.00"),
            status=DonationStatus.COMPLETED,
            created_at="2026-03-11T00:00:00Z",
            cpp_at_donation=Decimal("1.5"),
        )
        assert d.cpp_at_donation == Decimal("1.5")


class TestCommunityPoolProperties:
    def test_no_double_pledge(self):
        pool = CommunityPool(
            id="pool-1",
            name="Test Pool",
            creator_id="auth0|eric",
            target_charity_name="Test Charity",
            target_charity_state="CA",
            goal_amount=Decimal("500.00"),
            status=PoolStatus.OPEN,
            pledges=[],
            created_at="2026-03-11T00:00:00Z",
        )
        pledge = Pledge(
            id="pledge-1",
            user_id="auth0|eric",
            pool_id="pool-1",
            program_code="chase-ur",
            points_pledged=10000,
            dollar_value=Decimal("170.00"),
            pledged_at="2026-03-11T00:00:00Z",
        )
        pool.add_pledge(pledge)
        with pytest.raises(ValueError, match="Duplicate"):
            pool.add_pledge(pledge)

    def test_different_pledges_allowed(self):
        pool = CommunityPool(
            id="pool-1",
            name="Test Pool",
            creator_id="auth0|eric",
            target_charity_name="Test Charity",
            target_charity_state="CA",
            goal_amount=Decimal("500.00"),
            status=PoolStatus.OPEN,
            pledges=[],
            created_at="2026-03-11T00:00:00Z",
        )
        p1 = Pledge(
            id="pledge-1",
            user_id="auth0|eric",
            pool_id="pool-1",
            program_code="chase-ur",
            points_pledged=10000,
            dollar_value=Decimal("170.00"),
            pledged_at="2026-03-11T00:00:00Z",
        )
        p2 = Pledge(
            id="pledge-2",
            user_id="auth0|steve",
            pool_id="pool-1",
            program_code="amex-mr",
            points_pledged=5000,
            dollar_value=Decimal("85.00"),
            pledged_at="2026-03-11T00:00:00Z",
        )
        pool.add_pledge(p1)
        pool.add_pledge(p2)
        assert len(pool.pledges) == 2

    @given(
        goal=_dec_st("1.00", "100000", places=2),
    )
    @settings(max_examples=50)
    def test_empty_pool_not_goal_reached(self, goal: Decimal):
        pool = CommunityPool(
            id="pool-1",
            name="Test",
            creator_id="auth0|test",
            target_charity_name="Test",
            target_charity_state="CA",
            goal_amount=goal,
            status=PoolStatus.OPEN,
            pledges=[],
            created_at="2026-03-11T00:00:00Z",
        )
        assert not pool.is_goal_reached()

    def test_pledge_frozen_immutability(self):
        p = Pledge(
            id="pledge-1",
            user_id="auth0|eric",
            pool_id="pool-1",
            program_code="chase-ur",
            points_pledged=10000,
            dollar_value=Decimal("170.00"),
            pledged_at="2026-03-11T00:00:00Z",
        )
        with pytest.raises(AttributeError):
            p.id = "changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# 8. Subscription
# ---------------------------------------------------------------------------


class TestSubscriptionProperties:
    @given(tier=_tier)
    @settings(max_examples=30)
    def test_frozen_immutability(self, tier: SubscriptionTier):
        sub = Subscription(
            id="sub-001",
            user_id="auth0|test",
            tier=tier,
            status="active",
            current_period_start="2026-03-01",
            current_period_end="2026-04-01",
        )
        with pytest.raises(AttributeError):
            sub.status = "cancelled"  # type: ignore[misc]

    def test_charity_flavor_optional(self):
        sub = Subscription(
            id="sub-001",
            user_id="auth0|test",
            tier=SubscriptionTier.PREMIUM,
            status="active",
            current_period_start="2026-03-01",
            current_period_end="2026-04-01",
            charity_flavor="girl-scouts",
        )
        assert sub.charity_flavor == "girl-scouts"

    def test_charity_flavor_default_none(self):
        sub = Subscription(
            id="sub-001",
            user_id="auth0|test",
            tier=SubscriptionTier.FREE,
            status="active",
            current_period_start="2026-03-01",
            current_period_end="2026-04-01",
        )
        assert sub.charity_flavor is None

    def test_all_tiers_constructable(self):
        for tier in SubscriptionTier:
            sub = Subscription(
                id=f"sub-{tier.value}",
                user_id="auth0|test",
                tier=tier,
                status="active",
                current_period_start="2026-03-01",
                current_period_end="2026-04-01",
            )
            assert sub.tier == tier


# ---------------------------------------------------------------------------
# 9. Cross-cutting: JSON serialization, dataclass roundtrip
# ---------------------------------------------------------------------------


class TestSerializationProperties:
    def test_loyalty_program_asdict(self):
        prog = LoyaltyProgram(code="chase-ur", name="Chase UR", category=ProgramCategory.CREDIT_CARD)
        d = asdict(prog)
        assert d["code"] == "chase-ur"
        assert d["category"] == ProgramCategory.CREDIT_CARD
        # JSON serializable (enum needs .value)
        d["category"] = d["category"].value
        json.dumps(d)

    def test_transfer_partner_asdict(self):
        tp = TransferPartner(source_program="chase-ur", target_program="hyatt", transfer_ratio=1.0)
        d = asdict(tp)
        json.dumps(d)

    def test_point_balance_asdict(self):
        b = PointBalance(program_code="chase-ur", points=50000, cpp_baseline=Decimal("1.5"))
        d = asdict(b)
        d["cpp_baseline"] = str(d["cpp_baseline"])
        json.dumps(d)

    def test_optimization_action_asdict(self):
        a = OptimizationAction(
            action_type=ActionType.TRANSFER,
            program_code="chase-ur",
            points=10000,
            expected_value=Decimal("150.00"),
            description="transfer to hyatt",
            target_program="hyatt",
        )
        d = asdict(a)
        d["action_type"] = d["action_type"].value
        d["expected_value"] = str(d["expected_value"])
        json.dumps(d)

    def test_charity_organization_asdict(self):
        org = CharityOrganization(
            name="Test",
            category=CharityCategory.EDUCATION,
            state="CA",
            national_url="https://example.org",
            is_501c3=True,
            ein="12-3456789",
        )
        d = asdict(org)
        d["category"] = d["category"].value
        json.dumps(d)

    def test_subscription_asdict(self):
        sub = Subscription(
            id="sub-001",
            user_id="auth0|test",
            tier=SubscriptionTier.PREMIUM,
            status="active",
            current_period_start="2026-03-01",
            current_period_end="2026-04-01",
            charity_flavor="girl-scouts",
        )
        d = asdict(sub)
        d["tier"] = d["tier"].value
        json.dumps(d)

    def test_user_portfolio_asdict(self):
        balances = (
            PointBalance(program_code="chase-ur", points=50000, cpp_baseline=Decimal("1.5")),
            PointBalance(program_code="amex-mr", points=30000, cpp_baseline=Decimal("1.0")),
        )
        portfolio = UserPortfolio(user_id="auth0|test", balances=balances)
        d = asdict(portfolio)
        # Convert Decimal to str for JSON
        for b in d["balances"]:
            b["cpp_baseline"] = str(b["cpp_baseline"])
        json.dumps(d)

    def test_donation_asdict(self):
        d_obj = Donation(
            id="don-001",
            user_id="auth0|test",
            charity_name="Test",
            charity_state="CA",
            program_code="chase-ur",
            points_donated=1000,
            dollar_value=Decimal("15.00"),
            status=DonationStatus.COMPLETED,
            created_at="2026-03-11T00:00:00Z",
        )
        d = asdict(d_obj)
        d["dollar_value"] = str(d["dollar_value"])
        d["status"] = d["status"].value
        if d.get("cpp_at_donation"):
            d["cpp_at_donation"] = str(d["cpp_at_donation"])
        json.dumps(d)

    def test_pledge_asdict(self):
        p = Pledge(
            id="pledge-1",
            user_id="auth0|eric",
            pool_id="pool-1",
            program_code="chase-ur",
            points_pledged=10000,
            dollar_value=Decimal("170.00"),
            pledged_at="2026-03-11T00:00:00Z",
        )
        d = asdict(p)
        d["dollar_value"] = str(d["dollar_value"])
        json.dumps(d)

    def test_program_valuation_asdict(self):
        v = ProgramValuation(
            program_code="chase-ur",
            program_name="Chase UR",
            valuations={ValuationSource.TPG: Decimal("2.0")},
            timestamp="2026-03-11T00:00:00Z",
        )
        d = asdict(v)
        d["valuations"] = {k.value: str(v_) for k, v_ in d["valuations"].items()}
        d["cash_back_cpp"] = str(d["cash_back_cpp"])
        json.dumps(d)


# ---------------------------------------------------------------------------
# 10. All models importable and constructable (smoke test)
# ---------------------------------------------------------------------------


class TestAllModelsConstructable:
    def test_all_ten_entities_importable(self):
        """Verify all 10 core entities from Sprint 1 are importable and constructable."""
        # 1. LoyaltyProgram
        prog = LoyaltyProgram(code="test", name="Test", category=ProgramCategory.AIRLINE)
        assert prog.code == "test"

        # 2. TransferPartner
        tp = TransferPartner(source_program="a", target_program="b", transfer_ratio=1.0)
        assert tp.effective_ratio == 1.0

        # 3. ProgramValuation (PointValuation)
        pv = ProgramValuation(
            program_code="test",
            program_name="Test",
            valuations={ValuationSource.TPG: Decimal("2.0")},
            timestamp="2026-03-11T00:00:00Z",
        )
        assert pv.min_cpp == Decimal("2.0")

        # 4. UserPortfolio + PointBalance (ProgramBalance)
        balance = PointBalance(program_code="test", points=10000, cpp_baseline=Decimal("1.5"))
        portfolio = UserPortfolio(user_id="test-user", balances=(balance,))
        assert portfolio.total_estimated_value_cents == 15000

        # 5. OptimizationAction
        action = OptimizationAction(
            action_type=ActionType.TRANSFER,
            program_code="test",
            points=10000,
            expected_value=Decimal("150.00"),
            description="transfer",
        )
        assert action.expected_value == Decimal("150.00")

        # 6. CharityOrganization (CharityPartner)
        charity = CharityOrganization(
            name="Test",
            category=CharityCategory.EDUCATION,
            state="CA",
            national_url="https://example.org",
            is_501c3=True,
            ein="12-3456789",
        )
        assert charity.is_501c3 is True

        # 7. Donation (DonationTransaction) + CommunityPool
        donation = Donation(
            id="don-001",
            user_id="auth0|test",
            charity_name="Test",
            charity_state="CA",
            program_code="test",
            points_donated=1000,
            dollar_value=Decimal("15.00"),
            status=DonationStatus.PENDING,
            created_at="2026-03-11T00:00:00Z",
        )
        assert donation.points_donated == 1000

        pool = CommunityPool(
            id="pool-1",
            name="Test Pool",
            creator_id="auth0|test",
            target_charity_name="Test",
            target_charity_state="CA",
            goal_amount=Decimal("500.00"),
            status=PoolStatus.OPEN,
            pledges=[],
            created_at="2026-03-11T00:00:00Z",
        )
        assert pool.status == PoolStatus.OPEN

        # 8. Subscription
        sub = Subscription(
            id="sub-001",
            user_id="auth0|test",
            tier=SubscriptionTier.PREMIUM,
            status="active",
            current_period_start="2026-03-01",
            current_period_end="2026-04-01",
            charity_flavor="girl-scouts",
        )
        assert sub.charity_flavor == "girl-scouts"
