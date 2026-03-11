"""PortBundle — DI container for all Protocol port adapters.

Beck: One object to rule injection — test code swaps the whole bundle.
Fowler: Ports and Adapters — the application boundary is explicit.

create_app(ports) accepts an optional PortBundle. Without it, the adapter
factory selects real vs fake per environment variable. Tests pass a bundle
of fakes for zero-I/O verification.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from redeemflow.billing.fake_adapter import FakeBillingAdapter
from redeemflow.billing.ports import BillingPort
from redeemflow.charity.fake_adapter import FakeDonationAdapter
from redeemflow.charity.ports import DonationPort
from redeemflow.notifications.fake_adapter import FakeAlertAdapter
from redeemflow.notifications.ports import AlertPort
from redeemflow.optimization.fake_adapter import FakeTransferGraphAdapter
from redeemflow.optimization.ports import TransferGraphPort
from redeemflow.portfolio.fake_adapter import FakePortfolioAdapter
from redeemflow.portfolio.ports import PortfolioPort
from redeemflow.search.fake_adapter import FakeAwardSearchAdapter
from redeemflow.search.ports import AwardSearchPort
from redeemflow.valuations.fake_adapter import FakeValuationAdapter
from redeemflow.valuations.ports import ValuationPort


@dataclass
class PortBundle:
    """DI container for all external dependency adapters.

    Default: all fakes (zero I/O). Production: override per-port with real adapters.
    """

    billing: BillingPort = field(default_factory=FakeBillingAdapter)
    donation: DonationPort = field(default_factory=FakeDonationAdapter)
    alert: AlertPort = field(default_factory=FakeAlertAdapter)
    transfer_graph: TransferGraphPort = field(default_factory=FakeTransferGraphAdapter)
    portfolio: PortfolioPort = field(default_factory=FakePortfolioAdapter)
    award_search: AwardSearchPort = field(default_factory=FakeAwardSearchAdapter)
    valuation: ValuationPort = field(default_factory=FakeValuationAdapter)


def fake_ports() -> PortBundle:
    """Convenience: create a PortBundle with all fakes. Used by tests."""
    return PortBundle()
