"""Contract tests — FakeDonationProvider response schema and lifecycle.

Verifies the DonationProvider protocol contract: every response from
process_donation contains reference_id and status, and the lifecycle
create -> process -> complete is consistent.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from redeemflow.charity.donation_flow import FakeDonationProvider


@pytest.mark.contract
class TestFakeDonationProviderContract:
    @pytest.fixture
    def provider(self):
        return FakeDonationProvider()

    def test_process_donation_returns_reference_and_status(self, provider):
        result = provider.process_donation(
            user_id="user-contract",
            charity_name="Kiva",
            dollar_amount=Decimal("50.00"),
        )

        assert "reference_id" in result, "Response must contain reference_id"
        assert "status" in result, "Response must contain status"
        assert isinstance(result["reference_id"], str)
        assert len(result["reference_id"]) > 0

    def test_process_donation_status_is_completed(self, provider):
        result = provider.process_donation(
            user_id="user-status",
            charity_name="Kiva",
            dollar_amount=Decimal("25.00"),
        )

        assert result["status"] == "completed"

    def test_donation_lifecycle_create_process_complete(self, provider):
        """Full lifecycle: create donation -> query status -> verify completed."""
        result = provider.process_donation(
            user_id="user-lifecycle",
            charity_name="She's the First",
            dollar_amount=Decimal("100.00"),
        )

        reference_id = result["reference_id"]
        status = provider.get_donation_status(reference_id)

        assert status == "completed"

    def test_get_status_unknown_reference(self, provider):
        status = provider.get_donation_status("nonexistent-ref")
        assert status == "unknown"

    def test_multiple_donations_independent(self, provider):
        """Each donation gets a unique reference_id."""
        r1 = provider.process_donation("u1", "Kiva", Decimal("10.00"))
        r2 = provider.process_donation("u2", "Kiva", Decimal("20.00"))

        assert r1["reference_id"] != r2["reference_id"]
        assert provider.get_donation_status(r1["reference_id"]) == "completed"
        assert provider.get_donation_status(r2["reference_id"]) == "completed"

    def test_reference_id_format(self, provider):
        result = provider.process_donation("u1", "Kiva", Decimal("5.00"))
        assert result["reference_id"].startswith("fake-ref-")

    def test_response_has_no_unexpected_keys(self, provider):
        """Contract: response contains exactly reference_id and status."""
        result = provider.process_donation("u1", "Kiva", Decimal("5.00"))
        expected_keys = {"reference_id", "status"}
        assert set(result.keys()) == expected_keys
