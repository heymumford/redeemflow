"""Portfolio domain — points expiration tracking.

Monitors loyalty program balances against expiration policies and generates
alerts at 90/60/30 day thresholds before points expire due to inactivity.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from redeemflow.portfolio.models import PointBalance


@dataclass(frozen=True)
class ExpirationPolicy:
    program_code: str
    expires: bool
    months_inactivity: int | None
    activity_types: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ExpirationAlert:
    program_code: str
    points_at_risk: int
    days_until_expiry: int
    alert_level: int  # 90, 60, or 30


class ExpirationTracker:
    """Checks balances against expiration policies and generates alerts.

    For programs that expire due to inactivity, calculates days until expiry
    based on the inactivity window and assigns an alert level (90/60/30).
    """

    def check_expirations(
        self,
        balances: list[PointBalance],
        policies: list[ExpirationPolicy],
    ) -> list[ExpirationAlert]:
        policy_map = {p.program_code: p for p in policies}
        alerts: list[ExpirationAlert] = []

        for balance in balances:
            if balance.points == 0:
                continue

            policy = policy_map.get(balance.program_code)
            if policy is None or not policy.expires:
                continue

            # Calculate days until expiry from inactivity months.
            # Without real activity data, assume worst case: inactivity
            # window is half-consumed, generating a proactive alert.
            months = policy.months_inactivity or 0
            if months <= 0:
                continue

            days_until_expiry = months * 15  # conservative: assume halfway through inactivity window

            if days_until_expiry <= 30:
                alert_level = 30
            elif days_until_expiry <= 60:
                alert_level = 60
            else:
                alert_level = 90

            alerts.append(
                ExpirationAlert(
                    program_code=balance.program_code,
                    points_at_risk=balance.points,
                    days_until_expiry=days_until_expiry,
                    alert_level=alert_level,
                )
            )

        return alerts


# --- Seed data: expiration policies for the 23 programs from Sprint 1 ---

EXPIRATION_POLICIES: list[ExpirationPolicy] = [
    # Bank currencies — generally don't expire while account is open
    ExpirationPolicy(program_code="chase-ur", expires=False, months_inactivity=None, activity_types=[]),
    ExpirationPolicy(program_code="amex-mr", expires=False, months_inactivity=None, activity_types=[]),
    ExpirationPolicy(program_code="citi-ty", expires=False, months_inactivity=None, activity_types=[]),
    ExpirationPolicy(program_code="capital-one", expires=False, months_inactivity=None, activity_types=[]),
    ExpirationPolicy(program_code="bilt", expires=False, months_inactivity=None, activity_types=[]),
    ExpirationPolicy(program_code="wells-fargo", expires=False, months_inactivity=None, activity_types=[]),
    # Airlines — most expire after 18-24 months inactivity
    ExpirationPolicy(
        program_code="united",
        expires=True,
        months_inactivity=18,
        activity_types=["flight", "earn", "redeem", "transfer"],
    ),
    ExpirationPolicy(program_code="delta", expires=False, months_inactivity=None, activity_types=[]),
    ExpirationPolicy(
        program_code="american",
        expires=True,
        months_inactivity=24,
        activity_types=["flight", "earn", "redeem"],
    ),
    ExpirationPolicy(
        program_code="southwest",
        expires=True,
        months_inactivity=24,
        activity_types=["flight", "earn", "redeem"],
    ),
    ExpirationPolicy(
        program_code="alaska",
        expires=True,
        months_inactivity=24,
        activity_types=["flight", "earn", "redeem", "transfer"],
    ),
    ExpirationPolicy(
        program_code="jetblue",
        expires=True,
        months_inactivity=24,
        activity_types=["flight", "earn", "redeem"],
    ),
    # International airlines
    ExpirationPolicy(
        program_code="british-airways",
        expires=True,
        months_inactivity=36,
        activity_types=["flight", "earn", "redeem"],
    ),
    ExpirationPolicy(
        program_code="virgin-atlantic",
        expires=True,
        months_inactivity=36,
        activity_types=["flight", "earn", "redeem"],
    ),
    ExpirationPolicy(
        program_code="air-france-klm",
        expires=True,
        months_inactivity=24,
        activity_types=["flight", "earn", "redeem"],
    ),
    ExpirationPolicy(
        program_code="singapore",
        expires=True,
        months_inactivity=36,
        activity_types=["flight", "earn", "redeem"],
    ),
    ExpirationPolicy(
        program_code="turkish",
        expires=True,
        months_inactivity=36,
        activity_types=["flight", "earn", "redeem"],
    ),
    ExpirationPolicy(
        program_code="ana",
        expires=True,
        months_inactivity=36,
        activity_types=["flight", "earn", "redeem"],
    ),
    ExpirationPolicy(
        program_code="air-canada",
        expires=False,
        months_inactivity=None,
        activity_types=[],
    ),
    # Hotels
    ExpirationPolicy(
        program_code="hyatt",
        expires=True,
        months_inactivity=24,
        activity_types=["stay", "earn", "redeem"],
    ),
    ExpirationPolicy(
        program_code="marriott",
        expires=True,
        months_inactivity=24,
        activity_types=["stay", "earn", "redeem"],
    ),
    ExpirationPolicy(
        program_code="hilton",
        expires=True,
        months_inactivity=12,
        activity_types=["stay", "earn", "redeem"],
    ),
    ExpirationPolicy(
        program_code="ihg",
        expires=True,
        months_inactivity=12,
        activity_types=["stay", "earn", "redeem"],
    ),
]
