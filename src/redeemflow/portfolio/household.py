"""Household points pooling — multi-member combined optimization.

Beck: A household is a collection of portfolios with a unified view.
Fowler: Aggregate root — household owns member balances for optimization.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class HouseholdMember:
    """A member of a household with their loyalty programs."""

    member_id: str
    name: str
    role: str  # "primary", "spouse", "child", "other"
    programs: dict[str, int]  # program_code -> points


@dataclass(frozen=True)
class PooledBalance:
    """Combined balance for a program across household members."""

    program_code: str
    total_points: int
    contributors: list[dict]  # [{member_id, name, points}]
    member_count: int


@dataclass(frozen=True)
class HouseholdSummary:
    """Aggregated view of the household portfolio."""

    household_id: str
    member_count: int
    total_programs: int
    total_points: int
    pooled_balances: list[PooledBalance]
    unique_programs: list[str]
    optimization_opportunities: list[dict]


@dataclass
class Household:
    """A household aggregate for points pooling."""

    household_id: str
    name: str
    members: list[HouseholdMember] = field(default_factory=list)

    def add_member(self, member: HouseholdMember) -> None:
        """Add a member to the household."""
        if any(m.member_id == member.member_id for m in self.members):
            return  # Already exists
        self.members.append(member)

    def remove_member(self, member_id: str) -> bool:
        """Remove a member by ID. Returns True if found."""
        before = len(self.members)
        self.members = [m for m in self.members if m.member_id != member_id]
        return len(self.members) < before

    def pool_balances(self) -> list[PooledBalance]:
        """Combine balances across all members by program."""
        program_totals: dict[str, dict] = {}

        for member in self.members:
            for program, points in member.programs.items():
                if points <= 0:
                    continue
                if program not in program_totals:
                    program_totals[program] = {"total": 0, "contributors": []}
                program_totals[program]["total"] += points
                program_totals[program]["contributors"].append(
                    {"member_id": member.member_id, "name": member.name, "points": points}
                )

        return sorted(
            [
                PooledBalance(
                    program_code=code,
                    total_points=data["total"],
                    contributors=data["contributors"],
                    member_count=len(data["contributors"]),
                )
                for code, data in program_totals.items()
            ],
            key=lambda p: p.total_points,
            reverse=True,
        )

    def find_optimization_opportunities(self) -> list[dict]:
        """Find opportunities where pooling unlocks better redemptions."""
        opportunities = []
        pooled = self.pool_balances()

        for balance in pooled:
            if balance.member_count < 2:
                continue  # Only one member has this program

            # Check if pooling crosses a sweet spot threshold
            individual_max = max(c["points"] for c in balance.contributors)
            if balance.total_points >= 50000 and individual_max < 50000:
                opportunities.append(
                    {
                        "type": "threshold_unlock",
                        "program": balance.program_code,
                        "pooled_total": balance.total_points,
                        "individual_max": individual_max,
                        "description": (
                            f"Pooling {balance.program_code} points from {balance.member_count} members "
                            f"reaches {balance.total_points:,} points — unlocking premium redemptions"
                        ),
                    }
                )

            # Check if transfer consolidation would help
            if balance.member_count >= 2 and balance.total_points >= 25000:
                opportunities.append(
                    {
                        "type": "consolidation",
                        "program": balance.program_code,
                        "pooled_total": balance.total_points,
                        "member_count": balance.member_count,
                        "description": (
                            f"Consolidate {balance.program_code} from {balance.member_count} members "
                            f"for a single {balance.total_points:,}-point redemption"
                        ),
                    }
                )

        return opportunities

    def summarize(self) -> HouseholdSummary:
        """Build complete household summary."""
        pooled = self.pool_balances()
        opportunities = self.find_optimization_opportunities()
        unique = sorted({code for m in self.members for code in m.programs if m.programs[code] > 0})

        return HouseholdSummary(
            household_id=self.household_id,
            member_count=len(self.members),
            total_programs=len(pooled),
            total_points=sum(p.total_points for p in pooled),
            pooled_balances=pooled,
            unique_programs=unique,
            optimization_opportunities=opportunities,
        )


# In-memory household store (replaced by DB in production)
_HOUSEHOLDS: dict[str, Household] = {}


def get_or_create_household(household_id: str, name: str = "My Household") -> Household:
    """Get existing household or create new one."""
    if household_id not in _HOUSEHOLDS:
        _HOUSEHOLDS[household_id] = Household(household_id=household_id, name=name)
    return _HOUSEHOLDS[household_id]


def get_household(household_id: str) -> Household | None:
    """Get household by ID."""
    return _HOUSEHOLDS.get(household_id)
