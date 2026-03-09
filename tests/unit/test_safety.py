"""Tests for safety layer — women-first safety scoring for travel destinations."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from redeemflow.search.safety_scores import (
    DestinationSafety,
    FakeSafetyDataProvider,
    HotelSafetyScore,
    NeighborhoodSafety,
    SafetyDataProvider,
    SafetyRating,
    SafetySource,
)


class TestSafetyRating:
    def test_enum_values(self) -> None:
        assert SafetyRating.EXCELLENT == "EXCELLENT"
        assert SafetyRating.GOOD == "GOOD"
        assert SafetyRating.MODERATE == "MODERATE"
        assert SafetyRating.CAUTION == "CAUTION"
        assert SafetyRating.AVOID == "AVOID"

    def test_is_str_enum(self) -> None:
        assert isinstance(SafetyRating.EXCELLENT, str)

    def test_all_values_present(self) -> None:
        values = {r.value for r in SafetyRating}
        assert values == {"EXCELLENT", "GOOD", "MODERATE", "CAUTION", "AVOID"}


class TestSafetySource:
    def test_enum_values(self) -> None:
        assert SafetySource.COMMUNITY == "COMMUNITY"
        assert SafetySource.GOVERNMENT == "GOVERNMENT"
        assert SafetySource.TRAVEL_ADVISORY == "TRAVEL_ADVISORY"
        assert SafetySource.WOMEN_TRAVELERS == "WOMEN_TRAVELERS"

    def test_is_str_enum(self) -> None:
        assert isinstance(SafetySource.COMMUNITY, str)


class TestHotelSafetyScore:
    def test_frozen_dataclass(self) -> None:
        score = HotelSafetyScore(
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
            notes=["24hr concierge", "Well-lit area"],
        )
        assert score.hotel_name == "Park Hyatt Tokyo"
        assert score.city == "Tokyo"
        assert score.country == "Japan"
        assert score.overall_rating == SafetyRating.EXCELLENT
        assert score.walkability_score == 9
        assert score.neighborhood_safety == SafetyRating.EXCELLENT
        assert score.women_recommend is True
        assert score.women_recommend_count == 450
        assert score.lighting_score == 5
        assert score.transit_access_score == 5
        assert len(score.notes) == 2

    def test_immutable(self) -> None:
        score = HotelSafetyScore(
            hotel_name="Test",
            city="Test",
            country="Test",
            overall_rating=SafetyRating.GOOD,
            walkability_score=5,
            neighborhood_safety=SafetyRating.GOOD,
            women_recommend=True,
            women_recommend_count=100,
            lighting_score=3,
            transit_access_score=3,
            notes=[],
        )
        with pytest.raises(FrozenInstanceError):
            score.hotel_name = "Changed"  # type: ignore[misc]


class TestNeighborhoodSafety:
    def test_frozen_dataclass(self) -> None:
        nb = NeighborhoodSafety(
            name="Shinjuku",
            city="Tokyo",
            country="Japan",
            rating=SafetyRating.GOOD,
            walkability=8,
            women_traveler_notes=["Well-lit main streets", "Busy at night"],
        )
        assert nb.name == "Shinjuku"
        assert nb.city == "Tokyo"
        assert nb.country == "Japan"
        assert nb.rating == SafetyRating.GOOD
        assert nb.walkability == 8
        assert len(nb.women_traveler_notes) == 2

    def test_immutable(self) -> None:
        nb = NeighborhoodSafety(
            name="Test",
            city="Test",
            country="Test",
            rating=SafetyRating.MODERATE,
            walkability=5,
            women_traveler_notes=[],
        )
        with pytest.raises(FrozenInstanceError):
            nb.name = "Changed"  # type: ignore[misc]


class TestDestinationSafety:
    def test_frozen_dataclass(self) -> None:
        neighborhood = NeighborhoodSafety(
            name="Shinjuku",
            city="Tokyo",
            country="Japan",
            rating=SafetyRating.GOOD,
            walkability=8,
            women_traveler_notes=["Safe area"],
        )
        hotel = HotelSafetyScore(
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
            notes=["Top rated"],
        )
        dest = DestinationSafety(
            city="Tokyo",
            country="Japan",
            overall_rating=SafetyRating.EXCELLENT,
            neighborhoods=[neighborhood],
            women_travel_advisory="Very safe for solo women travelers",
            emergency_number="110",
            recommended_hotels=[hotel],
        )
        assert dest.city == "Tokyo"
        assert dest.country == "Japan"
        assert dest.overall_rating == SafetyRating.EXCELLENT
        assert len(dest.neighborhoods) == 1
        assert dest.women_travel_advisory is not None
        assert dest.emergency_number == "110"
        assert len(dest.recommended_hotels) == 1

    def test_optional_fields_none(self) -> None:
        dest = DestinationSafety(
            city="Unknown",
            country="Unknown",
            overall_rating=SafetyRating.MODERATE,
            neighborhoods=[],
            women_travel_advisory=None,
            emergency_number=None,
            recommended_hotels=[],
        )
        assert dest.women_travel_advisory is None
        assert dest.emergency_number is None

    def test_immutable(self) -> None:
        dest = DestinationSafety(
            city="Test",
            country="Test",
            overall_rating=SafetyRating.MODERATE,
            neighborhoods=[],
            women_travel_advisory=None,
            emergency_number=None,
            recommended_hotels=[],
        )
        with pytest.raises(FrozenInstanceError):
            dest.city = "Changed"  # type: ignore[misc]


class TestFakeSafetyDataProvider:
    def setup_method(self) -> None:
        self.provider = FakeSafetyDataProvider()

    def test_implements_protocol(self) -> None:
        assert isinstance(self.provider, SafetyDataProvider)

    def test_tokyo_returns_excellent(self) -> None:
        dest = self.provider.get_destination_safety("Tokyo", "Japan")
        assert dest.city == "Tokyo"
        assert dest.country == "Japan"
        assert dest.overall_rating == SafetyRating.EXCELLENT

    def test_tokyo_has_neighborhoods(self) -> None:
        dest = self.provider.get_destination_safety("Tokyo", "Japan")
        names = {n.name for n in dest.neighborhoods}
        assert "Shinjuku" in names
        assert "Shibuya" in names
        assert "Roppongi" in names
        assert len(dest.neighborhoods) >= 3

    def test_london_returns_good(self) -> None:
        dest = self.provider.get_destination_safety("London", "UK")
        assert dest.overall_rating == SafetyRating.GOOD

    def test_london_has_neighborhoods(self) -> None:
        dest = self.provider.get_destination_safety("London", "UK")
        names = {n.name for n in dest.neighborhoods}
        assert "Westminster" in names
        assert "Shoreditch" in names
        assert "Camden" in names

    def test_paris_returns_good(self) -> None:
        dest = self.provider.get_destination_safety("Paris", "France")
        assert dest.overall_rating == SafetyRating.GOOD

    def test_paris_has_neighborhoods(self) -> None:
        dest = self.provider.get_destination_safety("Paris", "France")
        names = {n.name for n in dest.neighborhoods}
        assert "Le Marais" in names
        assert "Montmartre" in names
        assert "Saint-Germain" in names

    def test_new_york_returns_good(self) -> None:
        dest = self.provider.get_destination_safety("New York", "US")
        assert dest.overall_rating == SafetyRating.GOOD

    def test_new_york_has_neighborhoods(self) -> None:
        dest = self.provider.get_destination_safety("New York", "US")
        names = {n.name for n in dest.neighborhoods}
        assert "Midtown" in names
        assert "Greenwich Village" in names
        assert "Upper West Side" in names

    def test_bangkok_returns_moderate(self) -> None:
        dest = self.provider.get_destination_safety("Bangkok", "Thailand")
        assert dest.overall_rating == SafetyRating.MODERATE

    def test_unknown_city_returns_moderate_default(self) -> None:
        dest = self.provider.get_destination_safety("Atlantis", "Ocean")
        assert dest.overall_rating == SafetyRating.MODERATE
        assert dest.city == "Atlantis"
        assert dest.country == "Ocean"

    def test_at_least_6_destinations_have_data(self) -> None:
        """The provider must have rich deterministic data for at least 6 major destinations."""
        known_cities = [
            ("Tokyo", "Japan"),
            ("London", "UK"),
            ("Paris", "France"),
            ("New York", "US"),
            ("Bangkok", "Thailand"),
            ("Singapore", "Singapore"),
        ]
        for city, country in known_cities:
            dest = self.provider.get_destination_safety(city, country)
            assert dest.city == city
            assert len(dest.neighborhoods) >= 2, f"{city} should have at least 2 neighborhoods"

    def test_destinations_have_recommended_hotels(self) -> None:
        """Each major destination should have 2-3 recommended hotels."""
        cities = [
            ("Tokyo", "Japan"),
            ("London", "UK"),
            ("Paris", "France"),
            ("New York", "US"),
        ]
        for city, country in cities:
            dest = self.provider.get_destination_safety(city, country)
            assert len(dest.recommended_hotels) >= 2, f"{city} should have at least 2 recommended hotels"

    def test_hotel_lookup(self) -> None:
        score = self.provider.get_hotel_safety("Park Hyatt Tokyo", "Tokyo")
        assert score is not None
        assert score.hotel_name == "Park Hyatt Tokyo"
        assert score.city == "Tokyo"
        assert score.overall_rating == SafetyRating.EXCELLENT

    def test_hotel_lookup_unknown(self) -> None:
        score = self.provider.get_hotel_safety("Nonexistent Hotel", "Nowhere")
        assert score is None

    def test_women_recommend_flag(self) -> None:
        """At least some hotels should be women-recommended."""
        dest = self.provider.get_destination_safety("Tokyo", "Japan")
        recommended = [h for h in dest.recommended_hotels if h.women_recommend]
        assert len(recommended) >= 1

    def test_emergency_numbers_present(self) -> None:
        dest = self.provider.get_destination_safety("Tokyo", "Japan")
        assert dest.emergency_number is not None

    def test_women_travel_advisory_present(self) -> None:
        dest = self.provider.get_destination_safety("Tokyo", "Japan")
        assert dest.women_travel_advisory is not None
        assert len(dest.women_travel_advisory) > 10
