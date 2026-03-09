"""Search domain — women-first safety scoring for travel destinations.

Provides safety ratings for destinations, neighborhoods, and hotels
with specific attention to women traveler safety indicators:
walkability, lighting, transit access, and community recommendations.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable


class SafetyRating(str, Enum):
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    MODERATE = "MODERATE"
    CAUTION = "CAUTION"
    AVOID = "AVOID"


class SafetySource(str, Enum):
    COMMUNITY = "COMMUNITY"
    GOVERNMENT = "GOVERNMENT"
    TRAVEL_ADVISORY = "TRAVEL_ADVISORY"
    WOMEN_TRAVELERS = "WOMEN_TRAVELERS"


@dataclass(frozen=True)
class HotelSafetyScore:
    """Safety score for a specific hotel, emphasizing women traveler safety."""

    hotel_name: str
    city: str
    country: str
    overall_rating: SafetyRating
    walkability_score: int  # 1-10
    neighborhood_safety: SafetyRating
    women_recommend: bool
    women_recommend_count: int
    lighting_score: int  # 1-5
    transit_access_score: int  # 1-5
    notes: list[str]


@dataclass(frozen=True)
class NeighborhoodSafety:
    """Safety profile for a neighborhood within a destination city."""

    name: str
    city: str
    country: str
    rating: SafetyRating
    walkability: int  # 1-10
    women_traveler_notes: list[str]


@dataclass(frozen=True)
class DestinationSafety:
    """Complete safety profile for a travel destination."""

    city: str
    country: str
    overall_rating: SafetyRating
    neighborhoods: list[NeighborhoodSafety]
    women_travel_advisory: str | None
    emergency_number: str | None
    recommended_hotels: list[HotelSafetyScore]


@runtime_checkable
class SafetyDataProvider(Protocol):
    def get_destination_safety(self, city: str, country: str) -> DestinationSafety: ...
    def get_hotel_safety(self, hotel_name: str, city: str) -> HotelSafetyScore | None: ...


# --- Deterministic seed data for FakeSafetyDataProvider ---


def _tokyo_data() -> DestinationSafety:
    neighborhoods = [
        NeighborhoodSafety(
            name="Shinjuku",
            city="Tokyo",
            country="Japan",
            rating=SafetyRating.GOOD,
            walkability=8,
            women_traveler_notes=[
                "Well-lit main streets, quieter back alleys at night",
                "Kabukicho area less comfortable for solo women late at night",
                "Excellent transit connections from Shinjuku Station",
            ],
        ),
        NeighborhoodSafety(
            name="Shibuya",
            city="Tokyo",
            country="Japan",
            rating=SafetyRating.EXCELLENT,
            walkability=9,
            women_traveler_notes=[
                "Very safe at all hours, well-lit shopping district",
                "Popular with women travelers and locals alike",
            ],
        ),
        NeighborhoodSafety(
            name="Roppongi",
            city="Tokyo",
            country="Japan",
            rating=SafetyRating.MODERATE,
            walkability=7,
            women_traveler_notes=[
                "Nightlife district — exercise normal caution after dark",
                "Roppongi Hills area is upscale and well-patrolled",
            ],
        ),
    ]
    hotels = [
        HotelSafetyScore(
            hotel_name="Park Hyatt Tokyo",
            city="Tokyo",
            country="Japan",
            overall_rating=SafetyRating.EXCELLENT,
            walkability_score=9,
            neighborhood_safety=SafetyRating.EXCELLENT,
            women_recommend=True,
            women_recommend_count=450,
            lighting_score=5,
            transit_access_score=5,
            notes=["24hr concierge", "Women-only floor available", "Shinjuku location with great views"],
        ),
        HotelSafetyScore(
            hotel_name="Andaz Tokyo Toranomon Hills",
            city="Tokyo",
            country="Japan",
            overall_rating=SafetyRating.EXCELLENT,
            walkability_score=8,
            neighborhood_safety=SafetyRating.EXCELLENT,
            women_recommend=True,
            women_recommend_count=320,
            lighting_score=5,
            transit_access_score=5,
            notes=["Modern design", "Excellent security", "Direct metro access"],
        ),
        HotelSafetyScore(
            hotel_name="The Peninsula Tokyo",
            city="Tokyo",
            country="Japan",
            overall_rating=SafetyRating.EXCELLENT,
            walkability_score=9,
            neighborhood_safety=SafetyRating.EXCELLENT,
            women_recommend=True,
            women_recommend_count=380,
            lighting_score=5,
            transit_access_score=5,
            notes=["Ginza location", "Exceptional service", "Well-lit surroundings"],
        ),
    ]
    return DestinationSafety(
        city="Tokyo",
        country="Japan",
        overall_rating=SafetyRating.EXCELLENT,
        neighborhoods=neighborhoods,
        women_travel_advisory=(
            "Tokyo is consistently ranked among the safest cities globally for women travelers. "
            "Public transit runs late and is well-lit. Convenience stores (konbini) are open 24/7 "
            "providing safe waypoints. Low crime rate and respectful culture."
        ),
        emergency_number="110",
        recommended_hotels=hotels,
    )


def _london_data() -> DestinationSafety:
    neighborhoods = [
        NeighborhoodSafety(
            name="Westminster",
            city="London",
            country="UK",
            rating=SafetyRating.GOOD,
            walkability=9,
            women_traveler_notes=[
                "Tourist area with high police presence",
                "Well-lit at all hours near major landmarks",
            ],
        ),
        NeighborhoodSafety(
            name="Shoreditch",
            city="London",
            country="UK",
            rating=SafetyRating.GOOD,
            walkability=8,
            women_traveler_notes=[
                "Trendy area, busy streets provide safety in numbers",
                "Good nightlife scene with reputable venues",
            ],
        ),
        NeighborhoodSafety(
            name="Camden",
            city="London",
            country="UK",
            rating=SafetyRating.GOOD,
            walkability=7,
            women_traveler_notes=[
                "Vibrant market area, busier during daytime",
                "Stick to main roads after dark",
            ],
        ),
    ]
    hotels = [
        HotelSafetyScore(
            hotel_name="The Langham London",
            city="London",
            country="UK",
            overall_rating=SafetyRating.EXCELLENT,
            walkability_score=9,
            neighborhood_safety=SafetyRating.GOOD,
            women_recommend=True,
            women_recommend_count=520,
            lighting_score=5,
            transit_access_score=5,
            notes=["Marylebone location", "24hr doorman", "Oxford Street walkable"],
        ),
        HotelSafetyScore(
            hotel_name="Shangri-La The Shard",
            city="London",
            country="UK",
            overall_rating=SafetyRating.EXCELLENT,
            walkability_score=8,
            neighborhood_safety=SafetyRating.GOOD,
            women_recommend=True,
            women_recommend_count=410,
            lighting_score=5,
            transit_access_score=5,
            notes=["London Bridge area", "Iconic views", "Excellent security"],
        ),
        HotelSafetyScore(
            hotel_name="Claridge's",
            city="London",
            country="UK",
            overall_rating=SafetyRating.EXCELLENT,
            walkability_score=9,
            neighborhood_safety=SafetyRating.EXCELLENT,
            women_recommend=True,
            women_recommend_count=600,
            lighting_score=5,
            transit_access_score=4,
            notes=["Mayfair location", "Art Deco elegance", "Discreet and secure"],
        ),
    ]
    return DestinationSafety(
        city="London",
        country="UK",
        overall_rating=SafetyRating.GOOD,
        neighborhoods=neighborhoods,
        women_travel_advisory=(
            "London is generally safe for women travelers. The Tube runs until late and "
            "Uber/black cabs are widely available. Avoid poorly lit side streets at night. "
            "Emergency contacts are well-marked throughout the city."
        ),
        emergency_number="999",
        recommended_hotels=hotels,
    )


def _paris_data() -> DestinationSafety:
    neighborhoods = [
        NeighborhoodSafety(
            name="Le Marais",
            city="Paris",
            country="France",
            rating=SafetyRating.GOOD,
            walkability=9,
            women_traveler_notes=[
                "Charming, walkable neighborhood popular with tourists",
                "Busy cafes and shops provide natural surveillance",
            ],
        ),
        NeighborhoodSafety(
            name="Montmartre",
            city="Paris",
            country="France",
            rating=SafetyRating.MODERATE,
            walkability=7,
            women_traveler_notes=[
                "Beautiful by day, some areas less comfortable at night",
                "Watch for pickpockets near Sacre-Coeur",
                "Stick to well-traveled paths after dark",
            ],
        ),
        NeighborhoodSafety(
            name="Saint-Germain",
            city="Paris",
            country="France",
            rating=SafetyRating.GOOD,
            walkability=9,
            women_traveler_notes=[
                "Upscale Left Bank neighborhood, very safe",
                "Literary cafes and boutiques create welcoming atmosphere",
            ],
        ),
    ]
    hotels = [
        HotelSafetyScore(
            hotel_name="Le Meurice",
            city="Paris",
            country="France",
            overall_rating=SafetyRating.EXCELLENT,
            walkability_score=9,
            neighborhood_safety=SafetyRating.GOOD,
            women_recommend=True,
            women_recommend_count=380,
            lighting_score=5,
            transit_access_score=5,
            notes=["Tuileries location", "Palace hotel", "Exceptional doorman service"],
        ),
        HotelSafetyScore(
            hotel_name="Hotel Lutetia",
            city="Paris",
            country="France",
            overall_rating=SafetyRating.EXCELLENT,
            walkability_score=9,
            neighborhood_safety=SafetyRating.GOOD,
            women_recommend=True,
            women_recommend_count=290,
            lighting_score=5,
            transit_access_score=5,
            notes=["Saint-Germain location", "Art Deco landmark", "Safe Left Bank area"],
        ),
    ]
    return DestinationSafety(
        city="Paris",
        country="France",
        overall_rating=SafetyRating.GOOD,
        neighborhoods=neighborhoods,
        women_travel_advisory=(
            "Paris is generally safe for women travelers. The Metro is efficient but "
            "watch for pickpockets on crowded lines. Avoid isolated areas after dark. "
            "Many arrondissements are lively and well-lit until late."
        ),
        emergency_number="112",
        recommended_hotels=hotels,
    )


def _new_york_data() -> DestinationSafety:
    neighborhoods = [
        NeighborhoodSafety(
            name="Midtown",
            city="New York",
            country="US",
            rating=SafetyRating.GOOD,
            walkability=9,
            women_traveler_notes=[
                "Always busy, which provides safety in numbers",
                "Well-lit major avenues like 5th and Park",
                "Avoid empty side streets late at night",
            ],
        ),
        NeighborhoodSafety(
            name="Greenwich Village",
            city="New York",
            country="US",
            rating=SafetyRating.GOOD,
            walkability=9,
            women_traveler_notes=[
                "Vibrant neighborhood with active street life until late",
                "NYU campus area feels safe and busy",
            ],
        ),
        NeighborhoodSafety(
            name="Upper West Side",
            city="New York",
            country="US",
            rating=SafetyRating.EXCELLENT,
            walkability=8,
            women_traveler_notes=[
                "Residential and family-friendly neighborhood",
                "Central Park proximity is great for morning runs",
                "Well-lit Broadway corridor",
            ],
        ),
    ]
    hotels = [
        HotelSafetyScore(
            hotel_name="The Beekman",
            city="New York",
            country="US",
            overall_rating=SafetyRating.EXCELLENT,
            walkability_score=8,
            neighborhood_safety=SafetyRating.GOOD,
            women_recommend=True,
            women_recommend_count=310,
            lighting_score=4,
            transit_access_score=5,
            notes=["FiDi location", "Historic building", "Close to subway"],
        ),
        HotelSafetyScore(
            hotel_name="Park Hyatt New York",
            city="New York",
            country="US",
            overall_rating=SafetyRating.EXCELLENT,
            walkability_score=9,
            neighborhood_safety=SafetyRating.GOOD,
            women_recommend=True,
            women_recommend_count=420,
            lighting_score=5,
            transit_access_score=5,
            notes=["Midtown West", "Carnegie Hall adjacent", "24hr concierge"],
        ),
        HotelSafetyScore(
            hotel_name="The Greenwich Hotel",
            city="New York",
            country="US",
            overall_rating=SafetyRating.EXCELLENT,
            walkability_score=8,
            neighborhood_safety=SafetyRating.GOOD,
            women_recommend=True,
            women_recommend_count=280,
            lighting_score=4,
            transit_access_score=4,
            notes=["Tribeca location", "Boutique feel", "Robert De Niro owned"],
        ),
    ]
    return DestinationSafety(
        city="New York",
        country="US",
        overall_rating=SafetyRating.GOOD,
        neighborhoods=neighborhoods,
        women_travel_advisory=(
            "New York is generally safe for women travelers, especially in Manhattan. "
            "The subway runs 24/7 but consider rideshare late at night. "
            "Stick to well-lit, populated areas. The city never sleeps, which works in your favor."
        ),
        emergency_number="911",
        recommended_hotels=hotels,
    )


def _bangkok_data() -> DestinationSafety:
    neighborhoods = [
        NeighborhoodSafety(
            name="Silom",
            city="Bangkok",
            country="Thailand",
            rating=SafetyRating.GOOD,
            walkability=7,
            women_traveler_notes=[
                "Business district, safe during day",
                "Night markets are busy and well-lit",
            ],
        ),
        NeighborhoodSafety(
            name="Sukhumvit",
            city="Bangkok",
            country="Thailand",
            rating=SafetyRating.MODERATE,
            walkability=6,
            women_traveler_notes=[
                "Mixed area — upscale hotels alongside nightlife",
                "BTS Skytrain provides safe elevated transit",
                "Avoid Nana area late at night as solo woman",
            ],
        ),
        NeighborhoodSafety(
            name="Riverside",
            city="Bangkok",
            country="Thailand",
            rating=SafetyRating.GOOD,
            walkability=6,
            women_traveler_notes=[
                "Hotel zone along the river, generally safe",
                "Water taxis are a safe transport option",
            ],
        ),
    ]
    hotels = [
        HotelSafetyScore(
            hotel_name="Mandarin Oriental Bangkok",
            city="Bangkok",
            country="Thailand",
            overall_rating=SafetyRating.EXCELLENT,
            walkability_score=6,
            neighborhood_safety=SafetyRating.GOOD,
            women_recommend=True,
            women_recommend_count=340,
            lighting_score=5,
            transit_access_score=3,
            notes=["Riverside legend", "Exceptional service", "Boat shuttle to BTS"],
        ),
        HotelSafetyScore(
            hotel_name="Park Hyatt Bangkok",
            city="Bangkok",
            country="Thailand",
            overall_rating=SafetyRating.EXCELLENT,
            walkability_score=7,
            neighborhood_safety=SafetyRating.GOOD,
            women_recommend=True,
            women_recommend_count=210,
            lighting_score=4,
            transit_access_score=5,
            notes=["Central Embassy mall", "Direct BTS access", "Modern and secure"],
        ),
    ]
    return DestinationSafety(
        city="Bangkok",
        country="Thailand",
        overall_rating=SafetyRating.MODERATE,
        neighborhoods=neighborhoods,
        women_travel_advisory=(
            "Bangkok requires normal urban caution. Tuk-tuk scams target tourists; "
            "use Grab (rideshare) or BTS/MRT instead. Dress modestly at temples. "
            "Generally safe but exercise extra caution in nightlife areas."
        ),
        emergency_number="191",
        recommended_hotels=hotels,
    )


def _singapore_data() -> DestinationSafety:
    neighborhoods = [
        NeighborhoodSafety(
            name="Marina Bay",
            city="Singapore",
            country="Singapore",
            rating=SafetyRating.EXCELLENT,
            walkability=9,
            women_traveler_notes=[
                "Extremely safe waterfront district",
                "Well-lit boardwalks perfect for evening walks",
            ],
        ),
        NeighborhoodSafety(
            name="Orchard Road",
            city="Singapore",
            country="Singapore",
            rating=SafetyRating.EXCELLENT,
            walkability=9,
            women_traveler_notes=[
                "Major shopping belt, safe at all hours",
                "Excellent MRT connectivity",
            ],
        ),
        NeighborhoodSafety(
            name="Chinatown",
            city="Singapore",
            country="Singapore",
            rating=SafetyRating.GOOD,
            walkability=8,
            women_traveler_notes=[
                "Historic area with active street life",
                "Food stalls and shops keep streets busy until late",
            ],
        ),
    ]
    hotels = [
        HotelSafetyScore(
            hotel_name="Marina Bay Sands",
            city="Singapore",
            country="Singapore",
            overall_rating=SafetyRating.EXCELLENT,
            walkability_score=9,
            neighborhood_safety=SafetyRating.EXCELLENT,
            women_recommend=True,
            women_recommend_count=550,
            lighting_score=5,
            transit_access_score=5,
            notes=["Iconic infinity pool", "Integrated resort", "24hr security"],
        ),
        HotelSafetyScore(
            hotel_name="Raffles Singapore",
            city="Singapore",
            country="Singapore",
            overall_rating=SafetyRating.EXCELLENT,
            walkability_score=8,
            neighborhood_safety=SafetyRating.EXCELLENT,
            women_recommend=True,
            women_recommend_count=480,
            lighting_score=5,
            transit_access_score=4,
            notes=["Heritage hotel", "Impeccable service", "City Hall area"],
        ),
    ]
    return DestinationSafety(
        city="Singapore",
        country="Singapore",
        overall_rating=SafetyRating.EXCELLENT,
        neighborhoods=neighborhoods,
        women_travel_advisory=(
            "Singapore is one of the safest cities in the world for women travelers. "
            "Strict laws, clean streets, and efficient public transit. "
            "Safe to walk alone at any hour in most areas."
        ),
        emergency_number="999",
        recommended_hotels=hotels,
    )


def _dubai_data() -> DestinationSafety:
    neighborhoods = [
        NeighborhoodSafety(
            name="Downtown Dubai",
            city="Dubai",
            country="UAE",
            rating=SafetyRating.EXCELLENT,
            walkability=7,
            women_traveler_notes=[
                "Burj Khalifa area, very safe and modern",
                "Dubai Mall provides air-conditioned walking",
            ],
        ),
        NeighborhoodSafety(
            name="Dubai Marina",
            city="Dubai",
            country="UAE",
            rating=SafetyRating.GOOD,
            walkability=8,
            women_traveler_notes=[
                "Waterfront promenade, popular with expats",
                "Well-lit and patrolled",
            ],
        ),
    ]
    hotels = [
        HotelSafetyScore(
            hotel_name="Burj Al Arab",
            city="Dubai",
            country="UAE",
            overall_rating=SafetyRating.EXCELLENT,
            walkability_score=5,
            neighborhood_safety=SafetyRating.EXCELLENT,
            women_recommend=True,
            women_recommend_count=390,
            lighting_score=5,
            transit_access_score=3,
            notes=["Iconic sail shape", "Private beach", "Chauffeur service"],
        ),
        HotelSafetyScore(
            hotel_name="Atlantis The Royal",
            city="Dubai",
            country="UAE",
            overall_rating=SafetyRating.EXCELLENT,
            walkability_score=6,
            neighborhood_safety=SafetyRating.GOOD,
            women_recommend=True,
            women_recommend_count=260,
            lighting_score=5,
            transit_access_score=3,
            notes=["Palm Jumeirah", "Ultra-luxury", "Resort setting"],
        ),
    ]
    return DestinationSafety(
        city="Dubai",
        country="UAE",
        overall_rating=SafetyRating.GOOD,
        neighborhoods=neighborhoods,
        women_travel_advisory=(
            "Dubai is very safe but conservative. Dress modestly outside resorts. "
            "Public transit is segregated with women-only sections on metro. "
            "Alcohol only in licensed venues. Very low crime rate."
        ),
        emergency_number="999",
        recommended_hotels=hotels,
    )


def _lisbon_data() -> DestinationSafety:
    neighborhoods = [
        NeighborhoodSafety(
            name="Alfama",
            city="Lisbon",
            country="Portugal",
            rating=SafetyRating.GOOD,
            walkability=7,
            women_traveler_notes=[
                "Historic neighborhood with narrow winding streets",
                "Charming but watch footing on cobblestones at night",
            ],
        ),
        NeighborhoodSafety(
            name="Chiado",
            city="Lisbon",
            country="Portugal",
            rating=SafetyRating.GOOD,
            walkability=8,
            women_traveler_notes=[
                "Elegant shopping and cafe district",
                "Well-lit and busy until late",
            ],
        ),
    ]
    hotels = [
        HotelSafetyScore(
            hotel_name="Four Seasons Ritz Lisbon",
            city="Lisbon",
            country="Portugal",
            overall_rating=SafetyRating.EXCELLENT,
            walkability_score=8,
            neighborhood_safety=SafetyRating.GOOD,
            women_recommend=True,
            women_recommend_count=220,
            lighting_score=5,
            transit_access_score=4,
            notes=["Eduardo VII Park views", "Classic luxury", "Safe Marquis area"],
        ),
        HotelSafetyScore(
            hotel_name="Bairro Alto Hotel",
            city="Lisbon",
            country="Portugal",
            overall_rating=SafetyRating.GOOD,
            walkability_score=8,
            neighborhood_safety=SafetyRating.GOOD,
            women_recommend=True,
            women_recommend_count=180,
            lighting_score=4,
            transit_access_score=4,
            notes=["Chiado location", "Rooftop terrace", "Boutique charm"],
        ),
    ]
    return DestinationSafety(
        city="Lisbon",
        country="Portugal",
        overall_rating=SafetyRating.GOOD,
        neighborhoods=neighborhoods,
        women_travel_advisory=(
            "Lisbon is a safe and welcoming city for women travelers. "
            "Petty theft can occur in tourist areas — keep valuables secure. "
            "The tram system is efficient but crowded; watch for pickpockets on Tram 28."
        ),
        emergency_number="112",
        recommended_hotels=hotels,
    )


# Pre-built destination data keyed by (city_lower, country_lower)
_DESTINATION_DATA: dict[tuple[str, str], DestinationSafety] = {}


def _init_data() -> None:
    for builder in [
        _tokyo_data,
        _london_data,
        _paris_data,
        _new_york_data,
        _bangkok_data,
        _singapore_data,
        _dubai_data,
        _lisbon_data,
    ]:
        dest = builder()
        _DESTINATION_DATA[(dest.city.lower(), dest.country.lower())] = dest


_init_data()


class FakeSafetyDataProvider:
    """In-memory safety data provider with deterministic data for major destinations."""

    def get_destination_safety(self, city: str, country: str) -> DestinationSafety:
        key = (city.lower(), country.lower())
        cached = _DESTINATION_DATA.get(key)
        if cached is not None:
            return cached

        # Return a default MODERATE rating for unknown cities
        return DestinationSafety(
            city=city,
            country=country,
            overall_rating=SafetyRating.MODERATE,
            neighborhoods=[],
            women_travel_advisory=None,
            emergency_number=None,
            recommended_hotels=[],
        )

    def get_hotel_safety(self, hotel_name: str, city: str) -> HotelSafetyScore | None:
        # Search through all destination data for the hotel
        for dest in _DESTINATION_DATA.values():
            if dest.city.lower() == city.lower():
                for hotel in dest.recommended_hotels:
                    if hotel.hotel_name == hotel_name:
                        return hotel
        return None
