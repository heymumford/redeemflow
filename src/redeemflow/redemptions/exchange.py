"""Exchange platform modeling — buy/sell/swap points through third-party marketplaces.

Fowler: Strategy pattern for exchange rate calculation.
Beck: Make the implicit explicit — exchange platforms have hidden fees and variable rates.

Models platforms like Points.com where users can:
- Buy additional points (at a cost per point)
- Sell points for cash (at a discount)
- Swap between programs (with exchange fees)
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class ExchangeType(str, Enum):
    BUY = "buy"
    SELL = "sell"
    SWAP = "swap"


@dataclass(frozen=True)
class ExchangeRate:
    """A point exchange rate on a platform."""

    platform: str
    program_code: str
    exchange_type: ExchangeType
    rate: Decimal  # Cost per point (buy), value per point (sell), or swap ratio
    fee_pct: Decimal  # Platform fee as percentage
    min_transaction: int  # Minimum points per transaction
    max_transaction: int  # Maximum points per transaction

    @property
    def effective_rate(self) -> Decimal:
        """Rate after platform fees."""
        if self.exchange_type == ExchangeType.BUY:
            return (self.rate * (1 + self.fee_pct / 100)).quantize(Decimal("0.0001"))
        elif self.exchange_type == ExchangeType.SELL:
            return (self.rate * (1 - self.fee_pct / 100)).quantize(Decimal("0.0001"))
        else:  # SWAP
            return (self.rate * (1 - self.fee_pct / 100)).quantize(Decimal("0.0001"))


@dataclass(frozen=True)
class SwapRate:
    """A point-to-point swap rate between two programs."""

    platform: str
    source_program: str
    target_program: str
    swap_ratio: Decimal  # How many target points per source point
    fee_pct: Decimal
    min_points: int

    @property
    def effective_ratio(self) -> Decimal:
        """Swap ratio after fees."""
        return (self.swap_ratio * (1 - self.fee_pct / 100)).quantize(Decimal("0.0001"))


@dataclass(frozen=True)
class ExchangeAnalysis:
    """Analysis of whether a point exchange transaction is worthwhile."""

    exchange_type: ExchangeType
    program_code: str
    points: int
    cash_cost_or_value: Decimal
    effective_cpp_impact: Decimal  # How the exchange affects your portfolio CPP
    baseline_cpp: Decimal  # What those points are normally worth
    recommendation: str  # "buy", "sell", "hold", "swap"
    rationale: str
    break_even_redemption_cpp: Decimal  # CPP needed at redemption to justify the buy


# Seed data: real-world exchange platform rates (Points.com, airline buy programs)
EXCHANGE_RATES: list[ExchangeRate] = [
    # Points.com buy rates (typically 1.5-3.5 cents per point)
    ExchangeRate(
        platform="points.com",
        program_code="united",
        exchange_type=ExchangeType.BUY,
        rate=Decimal("0.035"),
        fee_pct=Decimal("0"),
        min_transaction=2000,
        max_transaction=175000,
    ),
    ExchangeRate(
        platform="points.com",
        program_code="hilton",
        exchange_type=ExchangeType.BUY,
        rate=Decimal("0.010"),
        fee_pct=Decimal("0"),
        min_transaction=5000,
        max_transaction=160000,
    ),
    ExchangeRate(
        platform="points.com",
        program_code="marriott",
        exchange_type=ExchangeType.BUY,
        rate=Decimal("0.0125"),
        fee_pct=Decimal("0"),
        min_transaction=2000,
        max_transaction=100000,
    ),
    ExchangeRate(
        platform="points.com",
        program_code="ihg",
        exchange_type=ExchangeType.BUY,
        rate=Decimal("0.010"),
        fee_pct=Decimal("0"),
        min_transaction=1000,
        max_transaction=150000,
    ),
    ExchangeRate(
        platform="points.com",
        program_code="delta",
        exchange_type=ExchangeType.BUY,
        rate=Decimal("0.035"),
        fee_pct=Decimal("0"),
        min_transaction=2000,
        max_transaction=120000,
    ),
    ExchangeRate(
        platform="points.com",
        program_code="american",
        exchange_type=ExchangeType.BUY,
        rate=Decimal("0.035"),
        fee_pct=Decimal("0"),
        min_transaction=2000,
        max_transaction=150000,
    ),
    # Sell rates (typically 50-70% of buy rate)
    ExchangeRate(
        platform="points.com",
        program_code="united",
        exchange_type=ExchangeType.SELL,
        rate=Decimal("0.015"),
        fee_pct=Decimal("5"),
        min_transaction=10000,
        max_transaction=100000,
    ),
    ExchangeRate(
        platform="points.com",
        program_code="hilton",
        exchange_type=ExchangeType.SELL,
        rate=Decimal("0.004"),
        fee_pct=Decimal("5"),
        min_transaction=25000,
        max_transaction=100000,
    ),
]

SWAP_RATES: list[SwapRate] = [
    # Points.com swap marketplace
    SwapRate(
        platform="points.com",
        source_program="marriott",
        target_program="united",
        swap_ratio=Decimal("0.33"),
        fee_pct=Decimal("10"),
        min_points=3000,
    ),
    SwapRate(
        platform="points.com",
        source_program="hilton",
        target_program="american",
        swap_ratio=Decimal("0.10"),
        fee_pct=Decimal("10"),
        min_points=10000,
    ),
]


def analyze_buy(
    program_code: str,
    points_to_buy: int,
    target_redemption_cpp: Decimal = Decimal("1.5"),
) -> ExchangeAnalysis | None:
    """Analyze whether buying points is worthwhile for a target redemption."""
    rate = next(
        (r for r in EXCHANGE_RATES if r.program_code == program_code and r.exchange_type == ExchangeType.BUY),
        None,
    )
    if rate is None:
        return None

    if points_to_buy < rate.min_transaction or points_to_buy > rate.max_transaction:
        return ExchangeAnalysis(
            exchange_type=ExchangeType.BUY,
            program_code=program_code,
            points=points_to_buy,
            cash_cost_or_value=Decimal("0"),
            effective_cpp_impact=Decimal("0"),
            baseline_cpp=target_redemption_cpp,
            recommendation="hold",
            rationale=(f"Transaction outside limits ({rate.min_transaction:,}-{rate.max_transaction:,} points)"),
            break_even_redemption_cpp=Decimal("0"),
        )

    cost_per_point = rate.effective_rate
    total_cost = (cost_per_point * points_to_buy).quantize(Decimal("0.01"))
    # Break-even: what CPP do you need at redemption to recover the purchase cost?
    break_even_cpp = (total_cost / points_to_buy * 100).quantize(Decimal("0.01"))

    if target_redemption_cpp > break_even_cpp * Decimal("1.5"):
        recommendation = "buy"
        rationale = (
            f"Buying at {break_even_cpp} CPP cost, redeeming at {target_redemption_cpp} CPP "
            f"yields {((target_redemption_cpp / break_even_cpp - 1) * 100).quantize(Decimal('0.1'))}% profit"
        )
    elif target_redemption_cpp > break_even_cpp:
        recommendation = "hold"
        rationale = f"Marginal value: break-even at {break_even_cpp} CPP, target at {target_redemption_cpp} CPP"
    else:
        recommendation = "hold"
        rationale = f"Buying at {break_even_cpp} CPP cost exceeds redemption value of {target_redemption_cpp} CPP"

    return ExchangeAnalysis(
        exchange_type=ExchangeType.BUY,
        program_code=program_code,
        points=points_to_buy,
        cash_cost_or_value=total_cost,
        effective_cpp_impact=break_even_cpp,
        baseline_cpp=target_redemption_cpp,
        recommendation=recommendation,
        rationale=rationale,
        break_even_redemption_cpp=break_even_cpp,
    )


def analyze_sell(program_code: str, points_to_sell: int) -> ExchangeAnalysis | None:
    """Analyze the value of selling points for cash."""
    rate = next(
        (r for r in EXCHANGE_RATES if r.program_code == program_code and r.exchange_type == ExchangeType.SELL),
        None,
    )
    if rate is None:
        return None

    cash_value = (rate.effective_rate * points_to_sell).quantize(Decimal("0.01"))
    sell_cpp = (cash_value / points_to_sell * 100).quantize(Decimal("0.01")) if points_to_sell > 0 else Decimal("0")

    recommendation = "sell" if sell_cpp >= Decimal("1.0") else "hold"
    rationale = (
        f"Selling yields {sell_cpp} CPP cash value"
        if sell_cpp >= Decimal("1.0")
        else (f"Selling at {sell_cpp} CPP is poor — hold for travel redemptions")
    )

    return ExchangeAnalysis(
        exchange_type=ExchangeType.SELL,
        program_code=program_code,
        points=points_to_sell,
        cash_cost_or_value=cash_value,
        effective_cpp_impact=sell_cpp,
        baseline_cpp=Decimal("1.5"),
        recommendation=recommendation,
        rationale=rationale,
        break_even_redemption_cpp=sell_cpp,
    )


def find_exchange_rates(program_code: str) -> list[ExchangeRate]:
    """Find all exchange rates for a program."""
    return [r for r in EXCHANGE_RATES if r.program_code == program_code]


def find_swap_rates(source_program: str) -> list[SwapRate]:
    """Find all swap rates from a source program."""
    return [r for r in SWAP_RATES if r.source_program == source_program]
