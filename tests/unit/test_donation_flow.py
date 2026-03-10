"""Donation pipeline tests — TDD: written before implementation.

Tests the donation flow domain: value objects, fake provider, donation service.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from redeemflow.charity.donation_flow import (
    ChangeApiAdapter,
    Donation,
    DonationService,
    DonationStatus,
    FakeDonationProvider,
)
from redeemflow.charity.seed_data import CHARITY_NETWORK
from redeemflow.valuations.seed_data import PROGRAM_VALUATIONS


class TestDonationStatus:
    def test_enum_values(self):
        assert DonationStatus.PENDING == "pending"
        assert DonationStatus.PROCESSING == "processing"
        assert DonationStatus.COMPLETED == "completed"
        assert DonationStatus.FAILED == "failed"
        assert DonationStatus.REFUNDED == "refunded"

    def test_all_statuses_present(self):
        names = {s.value for s in DonationStatus}
        assert names == {"pending", "processing", "completed", "failed", "refunded"}


class TestDonation:
    def test_frozen_dataclass(self):
        d = Donation(
            id="d-1",
            user_id="auth0|eric",
            charity_name="Girl Scouts of the USA",
            charity_state="TX",
            program_code="chase-ur",
            points_donated=10000,
            dollar_value=Decimal("170.00"),
            status=DonationStatus.COMPLETED,
            created_at="2026-03-09T00:00:00Z",
        )
        with pytest.raises(AttributeError):
            d.id = "d-2"  # type: ignore[misc]

    def test_dollar_value_is_decimal(self):
        d = Donation(
            id="d-1",
            user_id="auth0|eric",
            charity_name="Girl Scouts of the USA",
            charity_state="TX",
            program_code="chase-ur",
            points_donated=10000,
            dollar_value=Decimal("170.00"),
            status=DonationStatus.COMPLETED,
            created_at="2026-03-09T00:00:00Z",
        )
        assert isinstance(d.dollar_value, Decimal)

    def test_optional_fields_default_none(self):
        d = Donation(
            id="d-1",
            user_id="auth0|eric",
            charity_name="Girl Scouts of the USA",
            charity_state="TX",
            program_code="chase-ur",
            points_donated=10000,
            dollar_value=Decimal("170.00"),
            status=DonationStatus.PENDING,
            created_at="2026-03-09T00:00:00Z",
        )
        assert d.completed_at is None
        assert d.change_api_reference is None


class TestFakeDonationProvider:
    def test_process_donation_returns_reference(self):
        provider = FakeDonationProvider()
        result = provider.process_donation("auth0|eric", "Girl Scouts of the USA", Decimal("50.00"))
        assert "reference_id" in result
        assert result["status"] == "completed"

    def test_get_donation_status(self):
        provider = FakeDonationProvider()
        result = provider.process_donation("auth0|eric", "Girl Scouts of the USA", Decimal("50.00"))
        ref_id = result["reference_id"]
        status = provider.get_donation_status(ref_id)
        assert status == "completed"

    def test_get_donation_status_unknown(self):
        provider = FakeDonationProvider()
        status = provider.get_donation_status("nonexistent-ref")
        assert status == "unknown"

    def test_multiple_donations_tracked(self):
        provider = FakeDonationProvider()
        r1 = provider.process_donation("auth0|eric", "Girl Scouts of the USA", Decimal("50.00"))
        r2 = provider.process_donation("auth0|steve", "AAUW", Decimal("100.00"))
        assert r1["reference_id"] != r2["reference_id"]
        assert provider.get_donation_status(r1["reference_id"]) == "completed"
        assert provider.get_donation_status(r2["reference_id"]) == "completed"


class TestChangeApiAdapter:
    def test_satisfies_protocol(self):
        from redeemflow.charity.donation_flow import DonationProvider

        adapter = ChangeApiAdapter(api_key="test-key")
        assert isinstance(adapter, DonationProvider)

    def test_requires_api_key(self):
        adapter = ChangeApiAdapter(api_key="test-key")
        assert adapter._api_key == "test-key"


class TestDonationService:
    def _make_service(self) -> DonationService:
        return DonationService(
            provider=FakeDonationProvider(),
            valuations=PROGRAM_VALUATIONS,
            charity_network=CHARITY_NETWORK,
        )

    def test_donate_valid_program_and_charity(self):
        service = self._make_service()
        donation = service.donate(
            user_id="auth0|eric",
            charity_name="Girl Scouts of the USA",
            charity_state="TX",
            program_code="chase-ur",
            points=10000,
        )
        assert isinstance(donation, Donation)
        assert donation.status == DonationStatus.COMPLETED
        assert donation.user_id == "auth0|eric"
        assert donation.charity_name == "Girl Scouts of the USA"
        assert donation.program_code == "chase-ur"
        assert donation.points_donated == 10000

    def test_donate_calculates_correct_dollar_value(self):
        service = self._make_service()
        donation = service.donate(
            user_id="auth0|eric",
            charity_name="Girl Scouts of the USA",
            charity_state="TX",
            program_code="chase-ur",
            points=10000,
        )
        # chase-ur median CPP is used by ProgramValuation.dollar_value()
        expected = PROGRAM_VALUATIONS["chase-ur"].dollar_value(10000)
        assert donation.dollar_value == expected

    def test_donate_zero_points_raises(self):
        service = self._make_service()
        with pytest.raises(ValueError, match="points"):
            service.donate(
                user_id="auth0|eric",
                charity_name="Girl Scouts of the USA",
                charity_state="TX",
                program_code="chase-ur",
                points=0,
            )

    def test_donate_negative_points_raises(self):
        service = self._make_service()
        with pytest.raises(ValueError, match="points"):
            service.donate(
                user_id="auth0|eric",
                charity_name="Girl Scouts of the USA",
                charity_state="TX",
                program_code="chase-ur",
                points=-100,
            )

    def test_donate_unknown_program_raises(self):
        service = self._make_service()
        with pytest.raises(ValueError, match="program"):
            service.donate(
                user_id="auth0|eric",
                charity_name="Girl Scouts of the USA",
                charity_state="TX",
                program_code="nonexistent-program",
                points=10000,
            )

    def test_donate_unknown_charity_raises(self):
        service = self._make_service()
        with pytest.raises(ValueError, match="charity"):
            service.donate(
                user_id="auth0|eric",
                charity_name="Nonexistent Charity XYZ",
                charity_state="TX",
                program_code="chase-ur",
                points=10000,
            )

    def test_get_user_donations_returns_history(self):
        service = self._make_service()
        service.donate(
            user_id="auth0|eric",
            charity_name="Girl Scouts of the USA",
            charity_state="TX",
            program_code="chase-ur",
            points=10000,
        )
        service.donate(
            user_id="auth0|eric",
            charity_name="AAUW",
            charity_state="CA",
            program_code="amex-mr",
            points=5000,
        )
        history = service.get_user_donations("auth0|eric")
        assert len(history) == 2

    def test_multiple_users_tracked_separately(self):
        service = self._make_service()
        service.donate(
            user_id="auth0|eric",
            charity_name="Girl Scouts of the USA",
            charity_state="TX",
            program_code="chase-ur",
            points=10000,
        )
        service.donate(
            user_id="auth0|steve",
            charity_name="AAUW",
            charity_state="CA",
            program_code="amex-mr",
            points=5000,
        )
        assert len(service.get_user_donations("auth0|eric")) == 1
        assert len(service.get_user_donations("auth0|steve")) == 1

    def test_get_user_donations_empty(self):
        service = self._make_service()
        assert service.get_user_donations("auth0|nobody") == []

    def test_donation_has_completed_at(self):
        service = self._make_service()
        donation = service.donate(
            user_id="auth0|eric",
            charity_name="Girl Scouts of the USA",
            charity_state="TX",
            program_code="chase-ur",
            points=10000,
        )
        assert donation.completed_at is not None

    def test_donation_has_change_api_reference(self):
        service = self._make_service()
        donation = service.donate(
            user_id="auth0|eric",
            charity_name="Girl Scouts of the USA",
            charity_state="TX",
            program_code="chase-ur",
            points=10000,
        )
        assert donation.change_api_reference is not None
