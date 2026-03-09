"""Search domain — conference travel planner for women's conferences.

Plans optimal travel to conferences by combining:
- Award search for flights/hotels
- Transfer graph optimization for point redemption
- Safety data for destination awareness
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from redeemflow.optimization.graph import TransferGraph
from redeemflow.portfolio.models import PointBalance
from redeemflow.search.safety_scores import DestinationSafety, SafetyDataProvider
from redeemflow.valuations.models import ProgramValuation


@dataclass(frozen=True)
class Conference:
    """A conference event with location and date details."""

    name: str
    city: str
    country: str
    start_date: str
    end_date: str
    category: str  # "tech", "business", "finance", "women_leadership"
    typical_attendees: int | None = None
    website: str | None = None


@dataclass(frozen=True)
class ConferenceTravelPlan:
    """A complete travel plan for attending a conference using points."""

    conference: Conference
    origin_city: str
    recommended_flights: list[dict]
    recommended_hotels: list[dict]
    points_options: list[dict]
    estimated_savings: Decimal
    safety_info: DestinationSafety | None


# --- Women's Conference Calendar ---

WOMEN_CONFERENCES: list[Conference] = [
    Conference(
        name="WBENC National Conference",
        city="Nashville",
        country="US",
        start_date="2026-06-15",
        end_date="2026-06-18",
        category="business",
        typical_attendees=5000,
        website="https://www.wbenc.org",
    ),
    Conference(
        name="Grace Hopper Celebration",
        city="Orlando",
        country="US",
        start_date="2026-10-06",
        end_date="2026-10-09",
        category="tech",
        typical_attendees=25000,
        website="https://ghc.anitab.org",
    ),
    Conference(
        name="BlogHer",
        city="New York",
        country="US",
        start_date="2026-08-10",
        end_date="2026-08-12",
        category="women_leadership",
        typical_attendees=3000,
        website="https://www.blogher.com",
    ),
    Conference(
        name="Wonder Women Tech",
        city="Long Beach",
        country="US",
        start_date="2026-04-20",
        end_date="2026-04-22",
        category="tech",
        typical_attendees=2000,
        website="https://wonderwomentech.com",
    ),
    Conference(
        name="AAUW National Conference",
        city="Washington",
        country="US",
        start_date="2026-06-22",
        end_date="2026-06-25",
        category="women_leadership",
        typical_attendees=2500,
        website="https://www.aauw.org",
    ),
]


class ConferencePlanner:
    """Plans optimal travel to conferences using points optimization."""

    def __init__(
        self,
        graph: TransferGraph,
        valuations: dict[str, ProgramValuation],
        safety_provider: SafetyDataProvider | None = None,
    ) -> None:
        self._graph = graph
        self._valuations = valuations
        self._safety_provider = safety_provider

    def plan(
        self,
        conference: Conference,
        origin_city: str,
        balances: list[PointBalance],
    ) -> ConferenceTravelPlan:
        """Create a travel plan for attending a conference.

        Analyzes user's point balances to find optimal redemption options,
        estimates savings vs cash booking, and includes safety data.
        """
        safety_info = None
        if self._safety_provider is not None:
            safety_info = self._safety_provider.get_destination_safety(conference.city, conference.country)

        if not balances:
            return ConferenceTravelPlan(
                conference=conference,
                origin_city=origin_city,
                recommended_flights=[],
                recommended_hotels=[],
                points_options=[],
                estimated_savings=Decimal("0"),
                safety_info=safety_info,
            )

        points_options = self._find_points_options(balances)
        recommended_flights = self._estimate_flights(conference, origin_city, balances)
        recommended_hotels = self._estimate_hotels(conference, balances)
        estimated_savings = self._estimate_savings(points_options)

        return ConferenceTravelPlan(
            conference=conference,
            origin_city=origin_city,
            recommended_flights=recommended_flights,
            recommended_hotels=recommended_hotels,
            points_options=points_options,
            estimated_savings=estimated_savings,
            safety_info=safety_info,
        )

    def _find_points_options(self, balances: list[PointBalance]) -> list[dict]:
        """Find the best point redemption options across all user balances."""
        options: list[dict] = []
        for balance in balances:
            best_path = self._graph.find_best_path(balance.program_code, balance.points)
            if best_path is not None:
                val = self._valuations.get(balance.program_code)
                median_cpp = val.median_cpp if val else balance.cpp_baseline
                estimated_value = (Decimal(best_path.source_points_needed) * median_cpp / Decimal(100)).quantize(
                    Decimal("0.01")
                )
                options.append(
                    {
                        "program": balance.program_code,
                        "points_available": balance.points,
                        "points_needed": best_path.source_points_needed,
                        "redemption": best_path.redemption.description,
                        "effective_cpp": round(best_path.effective_cpp, 2),
                        "estimated_value": str(estimated_value),
                        "hops": best_path.total_hops,
                    }
                )
        return sorted(options, key=lambda o: o.get("effective_cpp", 0), reverse=True)

    def _estimate_flights(self, conference: Conference, origin_city: str, balances: list[PointBalance]) -> list[dict]:
        """Estimate flight options using available balances."""
        flights: list[dict] = []
        for balance in balances:
            paths = self._graph.find_paths(balance.program_code, max_hops=2)
            for path in paths[:2]:  # Top 2 paths per program
                if "business" in path.redemption.description.lower() or "first" in path.redemption.description.lower():
                    if balance.points >= path.source_points_needed:
                        flights.append(
                            {
                                "program": balance.program_code,
                                "route": f"{origin_city} to {conference.city}",
                                "description": path.redemption.description,
                                "points_needed": path.source_points_needed,
                                "effective_cpp": round(path.effective_cpp, 2),
                            }
                        )
        return flights[:5]  # Cap at 5 recommendations

    def _estimate_hotels(self, conference: Conference, balances: list[PointBalance]) -> list[dict]:
        """Estimate hotel options using available balances."""
        hotels: list[dict] = []
        for balance in balances:
            paths = self._graph.find_paths(balance.program_code, max_hops=2)
            for path in paths:
                desc_lower = path.redemption.description.lower()
                if (
                    "hotel" in desc_lower
                    or "hyatt" in desc_lower
                    or "marriott" in desc_lower
                    or "hilton" in desc_lower
                    or "ihg" in desc_lower
                ):
                    if balance.points >= path.source_points_needed:
                        hotels.append(
                            {
                                "program": balance.program_code,
                                "description": path.redemption.description,
                                "points_needed": path.source_points_needed,
                                "nights_estimate": max(
                                    1,
                                    (int(conference.end_date.split("-")[2]) - int(conference.start_date.split("-")[2])),
                                ),
                            }
                        )
                        break  # One hotel option per program
        return hotels[:3]

    def _estimate_savings(self, points_options: list[dict]) -> Decimal:
        """Sum up estimated value from all points options as savings."""
        total = Decimal("0")
        for opt in points_options:
            total += Decimal(opt["estimated_value"])
        return total.quantize(Decimal("0.01"))
