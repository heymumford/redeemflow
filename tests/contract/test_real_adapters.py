"""Contract tests — real adapter Protocol conformance.

Each real adapter must satisfy the same Protocol as its fake counterpart.
All external API calls are mocked via httpx transport.

Beck: Test the contract, not the wiring.
Fowler: Both sides of each adapter boundary prove they keep their promises.
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import patch

import httpx
import pytest

from redeemflow.charity.donation_flow import (
    ChangeApiAdapter,
    DonationProvider,
    FakeDonationProvider,
)
from redeemflow.portfolio.awardwallet import (
    AwardWalletAdapter,
    AwardWalletError,
    FakeAwardWalletAdapter,
)
from redeemflow.portfolio.ports import BalanceFetcher
from redeemflow.search.award_search import (
    AwardSearchProvider,
    FakeAwardSearchProvider,
    SeatsAeroAdapter,
    SeatsAeroError,
)


def _mock_response(status_code: int, json_data: dict, method: str = "GET", url: str = "https://test") -> httpx.Response:
    """Create an httpx.Response with a request attached (required for raise_for_status)."""
    resp = httpx.Response(status_code, json=json_data)
    resp._request = httpx.Request(method, url)
    return resp


# --- AwardWallet Protocol conformance ---


class TestAwardWalletProtocol:
    """Both adapters satisfy BalanceFetcher Protocol."""

    def test_fake_is_balance_fetcher(self):
        assert isinstance(FakeAwardWalletAdapter(), BalanceFetcher)

    def test_real_is_balance_fetcher(self):
        adapter = AwardWalletAdapter(api_key="test-key")
        assert isinstance(adapter, BalanceFetcher)


class TestAwardWalletAdapter:
    """Real adapter returns PointBalance list from API response."""

    def test_fetch_balances_parses_response(self):
        mock_response = _mock_response(
            200,
            {
                "accounts": [
                    {"program": "Chase Ultimate Rewards", "balance": 95000},
                    {"program": "United MileagePlus", "balance": 45000},
                    {"program": "Unknown Program", "balance": 0},
                ]
            },
        )
        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__ = lambda s: s
            mock_client.return_value.__exit__ = lambda s, *a: None
            mock_client.return_value.get.return_value = mock_response

            adapter = AwardWalletAdapter(api_key="test-key")
            balances = adapter.fetch_balances("user-1")

        assert len(balances) == 2  # zero-balance account filtered
        assert balances[0].program_code == "chase-ur"
        assert balances[0].points == 95000
        assert balances[1].program_code == "united"

    def test_fetch_balances_handles_timeout(self):
        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__ = lambda s: s
            mock_client.return_value.__exit__ = lambda s, *a: None
            mock_client.return_value.get.side_effect = httpx.TimeoutException("timeout")

            adapter = AwardWalletAdapter(api_key="test-key")
            with pytest.raises(AwardWalletError, match="timeout"):
                adapter.fetch_balances("user-1")

    def test_fetch_balances_handles_auth_error(self):
        mock_response = _mock_response(401, {"error": "unauthorized"})
        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__ = lambda s: s
            mock_client.return_value.__exit__ = lambda s, *a: None
            mock_client.return_value.get.return_value = mock_response

            adapter = AwardWalletAdapter(api_key="bad-key")
            with pytest.raises(AwardWalletError, match="auth failure"):
                adapter.fetch_balances("user-1")

    def test_fetch_balances_empty_accounts(self):
        mock_response = _mock_response(200, {"accounts": []})
        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__ = lambda s: s
            mock_client.return_value.__exit__ = lambda s, *a: None
            mock_client.return_value.get.return_value = mock_response

            adapter = AwardWalletAdapter(api_key="test-key")
            balances = adapter.fetch_balances("user-1")

        assert balances == []


# --- Change API Protocol conformance ---


class TestChangeApiProtocol:
    """Both adapters satisfy DonationProvider Protocol."""

    def test_fake_is_donation_provider(self):
        assert isinstance(FakeDonationProvider(), DonationProvider)

    def test_real_is_donation_provider(self):
        adapter = ChangeApiAdapter(api_key="test-key")
        assert isinstance(adapter, DonationProvider)


class TestChangeApiAdapter:
    """Real adapter processes donations through Change API."""

    def test_process_donation_returns_reference(self):
        mock_response = _mock_response(200, {"id": "don_change_abc123", "status": "completed"}, method="POST")
        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__ = lambda s: s
            mock_client.return_value.__exit__ = lambda s, *a: None
            mock_client.return_value.post.return_value = mock_response

            adapter = ChangeApiAdapter(api_key="test-key")
            result = adapter.process_donation("user-1", "Girl Scouts", Decimal("50.00"))

        assert result["reference_id"] == "don_change_abc123"
        assert result["status"] == "completed"

    def test_process_donation_sends_cents(self):
        mock_response = _mock_response(200, {"id": "don_1", "status": "completed"}, method="POST")
        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__ = lambda s: s
            mock_client.return_value.__exit__ = lambda s, *a: None
            mock_client.return_value.post.return_value = mock_response

            adapter = ChangeApiAdapter(api_key="test-key")
            adapter.process_donation("user-1", "Test Charity", Decimal("25.50"))

            call_args = mock_client.return_value.post.call_args
            assert call_args.kwargs["json"]["amount"] == 2550

    def test_get_donation_status_returns_status(self):
        mock_response = _mock_response(200, {"status": "completed"})
        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__ = lambda s: s
            mock_client.return_value.__exit__ = lambda s, *a: None
            mock_client.return_value.get.return_value = mock_response

            adapter = ChangeApiAdapter(api_key="test-key")
            status = adapter.get_donation_status("don_abc")

        assert status == "completed"

    def test_get_donation_status_handles_error(self):
        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__ = lambda s: s
            mock_client.return_value.__exit__ = lambda s, *a: None
            mock_client.return_value.get.side_effect = httpx.ConnectError("connection refused")

            adapter = ChangeApiAdapter(api_key="test-key")
            status = adapter.get_donation_status("don_abc")

        assert status == "unknown"


# --- Seats.aero Protocol conformance ---


class TestSeatsAeroProtocol:
    """Both adapters satisfy AwardSearchProvider Protocol."""

    def test_fake_is_provider(self):
        assert isinstance(FakeAwardSearchProvider(), AwardSearchProvider)

    def test_real_is_provider(self):
        adapter = SeatsAeroAdapter(api_key="test-key")
        assert isinstance(adapter, AwardSearchProvider)


class TestSeatsAeroAdapter:
    """Real adapter returns AwardResult list from API response."""

    def test_search_parses_results(self):
        mock_response = _mock_response(
            200,
            {
                "data": [
                    {
                        "source": "United",
                        "miles": 80000,
                        "cash_price": "5600.00",
                        "stops": 0,
                        "seats": 2,
                    },
                    {
                        "source": "ANA",
                        "points": 88000,
                        "cash_price": "6200.00",
                        "stops": 0,
                        "seats": 1,
                    },
                ]
            },
        )
        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__ = lambda s: s
            mock_client.return_value.__exit__ = lambda s, *a: None
            mock_client.return_value.get.return_value = mock_response

            adapter = SeatsAeroAdapter(api_key="test-key")
            results = adapter.search("SFO", "NRT", "2026-06-15", "business")

        assert len(results) == 2
        assert results[0].program == "united"
        assert results[0].points_required == 80000
        assert results[0].direct is True
        assert results[0].source == "seats.aero"
        assert results[1].program == "ana"

    def test_search_handles_timeout(self):
        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__ = lambda s: s
            mock_client.return_value.__exit__ = lambda s, *a: None
            mock_client.return_value.get.side_effect = httpx.TimeoutException("timeout")

            adapter = SeatsAeroAdapter(api_key="test-key")
            with pytest.raises(SeatsAeroError, match="timeout"):
                adapter.search("SFO", "NRT", "2026-06-15", "business")

    def test_search_empty_results(self):
        mock_response = _mock_response(200, {"data": []})
        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__ = lambda s: s
            mock_client.return_value.__exit__ = lambda s, *a: None
            mock_client.return_value.get.return_value = mock_response

            adapter = SeatsAeroAdapter(api_key="test-key")
            results = adapter.search("SFO", "NRT", "2026-06-15", "business")

        assert results == []

    def test_search_filters_zero_points(self):
        mock_response = _mock_response(
            200,
            {
                "data": [
                    {"source": "United", "miles": 0, "cash_price": "100", "stops": 0},
                    {"source": "ANA", "miles": 88000, "cash_price": "6200", "stops": 0},
                ]
            },
        )
        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__ = lambda s: s
            mock_client.return_value.__exit__ = lambda s, *a: None
            mock_client.return_value.get.return_value = mock_response

            adapter = SeatsAeroAdapter(api_key="test-key")
            results = adapter.search("SFO", "NRT", "2026-06-15", "business")

        assert len(results) == 1
        assert results[0].program == "ana"


# --- Adapter factory env dispatch ---


class TestAdapterFactoryDispatch:
    """Env-based adapter selection for all Protocol boundaries."""

    def test_awardwallet_selected_when_key_set(self, monkeypatch):
        monkeypatch.setenv("AWARDWALLET_API_KEY", "aw_test_key")
        from redeemflow.app import _select_adapters

        adapters = _select_adapters()
        assert isinstance(adapters["balance_fetcher"], AwardWalletAdapter)

    def test_seats_aero_selected_when_key_set(self, monkeypatch):
        monkeypatch.setenv("SEATS_AERO_API_KEY", "seats_test_key")
        from redeemflow.app import _select_adapters

        adapters = _select_adapters()
        assert isinstance(adapters["award_search"], SeatsAeroAdapter)

    def test_change_api_selected_when_key_set(self, monkeypatch):
        monkeypatch.setenv("CHANGE_API_KEY", "change_test_key")
        from redeemflow.app import _select_adapters

        adapters = _select_adapters()
        assert isinstance(adapters["donation_provider"], ChangeApiAdapter)

    def test_fakes_when_no_keys(self):
        from redeemflow.app import _select_adapters

        adapters = _select_adapters()
        assert (
            isinstance(adapters["balance_fetcher"], FakeAwardWalletAdapter.__class__)
            or "Fake" in type(adapters["balance_fetcher"]).__name__
        )
        assert "Fake" in type(adapters["award_search"]).__name__
        assert "Fake" in type(adapters["donation_provider"]).__name__
