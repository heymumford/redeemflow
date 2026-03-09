"""RED tests for the charity domain model.

Beck: Write the test you wish you had. These define the behavior contract.
Fowler: Value objects are immutable. State holders are mutable.
"""

from __future__ import annotations

import pytest

from redeemflow.charity.models import CharityCategory, CharityOrganization, CharityPartnerNetwork


class TestCharityCategory:
    def test_all_enum_values_exist(self):
        expected = {
            "BUSINESS",
            "YOUTH",
            "STEM",
            "COMMUNITY",
            "CIVIC",
            "EDUCATION",
            "ANIMAL_WELFARE",
            "ARTS",
            "SAFETY",
            "WORKFORCE",
            "GRANTS",
            "MULTI",
        }
        actual = {c.name for c in CharityCategory}
        assert actual == expected

    def test_enum_values_are_lowercase(self):
        for c in CharityCategory:
            assert c.value == c.name.lower()


class TestCharityOrganization:
    def test_create_frozen_dataclass(self):
        org = CharityOrganization(
            name="Girl Scouts of the USA",
            category=CharityCategory.YOUTH,
            state="OH",
            chapter_name="Girl Scouts of Western Ohio",
            chapter_url="https://www.gswo.org",
            national_url="https://www.girlscouts.org",
            donation_url="https://www.girlscouts.org/donate",
            is_501c3=True,
            ein="13-1624016",
            description="Building girls of courage, confidence, and character.",
        )
        assert org.name == "Girl Scouts of the USA"
        assert org.category == CharityCategory.YOUTH
        assert org.state == "OH"
        assert org.chapter_name == "Girl Scouts of Western Ohio"
        assert org.is_501c3 is True

    def test_frozen_immutability(self):
        org = CharityOrganization(
            name="Girl Scouts of the USA",
            category=CharityCategory.YOUTH,
            state="OH",
            national_url="https://www.girlscouts.org",
            is_501c3=True,
        )
        with pytest.raises(AttributeError):
            org.name = "Something else"

    def test_defaults(self):
        org = CharityOrganization(
            name="AAUW",
            category=CharityCategory.EDUCATION,
            state="CA",
            national_url="https://www.aauw.org",
            is_501c3=True,
        )
        assert org.chapter_name is None
        assert org.chapter_url is None
        assert org.donation_url is None
        assert org.accepts_points_donation is False
        assert org.ein is None
        assert org.description is None

    def test_all_fields_present(self):
        org = CharityOrganization(
            name="Test Org",
            category=CharityCategory.COMMUNITY,
            state="TX",
            chapter_name="Texas Chapter",
            chapter_url="https://example.com/tx",
            national_url="https://example.com",
            donation_url="https://example.com/donate",
            is_501c3=True,
            accepts_points_donation=True,
            ein="12-3456789",
            description="A test org.",
        )
        assert org.accepts_points_donation is True
        assert org.ein == "12-3456789"
        assert org.description == "A test org."


class TestCharityPartnerNetwork:
    @pytest.fixture()
    def sample_network(self) -> CharityPartnerNetwork:
        charities = [
            CharityOrganization(
                name="Girl Scouts of the USA",
                category=CharityCategory.YOUTH,
                state="OH",
                chapter_name="Girl Scouts of Western Ohio",
                national_url="https://www.girlscouts.org",
                is_501c3=True,
            ),
            CharityOrganization(
                name="Girl Scouts of the USA",
                category=CharityCategory.YOUTH,
                state="TX",
                chapter_name="Girl Scouts of Texas Oklahoma Plains",
                national_url="https://www.girlscouts.org",
                is_501c3=True,
            ),
            CharityOrganization(
                name="AAUW",
                category=CharityCategory.EDUCATION,
                state="OH",
                chapter_name="AAUW Ohio Branch",
                national_url="https://www.aauw.org",
                is_501c3=True,
            ),
            CharityOrganization(
                name="Habitat for Humanity Women Build",
                category=CharityCategory.COMMUNITY,
                state="CA",
                chapter_name="Habitat for Humanity Women Build - California",
                national_url="https://www.habitat.org",
                is_501c3=True,
            ),
        ]
        return CharityPartnerNetwork(charities=charities)

    def test_by_state_returns_correct_orgs(self, sample_network: CharityPartnerNetwork):
        oh_orgs = sample_network.by_state("OH")
        assert len(oh_orgs) == 2
        assert all(o.state == "OH" for o in oh_orgs)

    def test_by_category_returns_correct_orgs(self, sample_network: CharityPartnerNetwork):
        youth_orgs = sample_network.by_category(CharityCategory.YOUTH)
        assert len(youth_orgs) == 2
        assert all(o.category == CharityCategory.YOUTH for o in youth_orgs)

    def test_by_state_and_category_intersection(self, sample_network: CharityPartnerNetwork):
        results = sample_network.by_state_and_category("OH", CharityCategory.YOUTH)
        assert len(results) == 1
        assert results[0].chapter_name == "Girl Scouts of Western Ohio"

    def test_search_matches_name_substring(self, sample_network: CharityPartnerNetwork):
        results = sample_network.search("girl scouts")
        assert len(results) == 2

    def test_search_matches_chapter_name(self, sample_network: CharityPartnerNetwork):
        results = sample_network.search("western ohio")
        assert len(results) == 1

    def test_search_matches_description(self):
        network = CharityPartnerNetwork(
            charities=[
                CharityOrganization(
                    name="Test Org",
                    category=CharityCategory.COMMUNITY,
                    state="NY",
                    national_url="https://example.com",
                    is_501c3=True,
                    description="Empowering women in technology.",
                ),
            ]
        )
        results = network.search("technology")
        assert len(results) == 1

    def test_search_case_insensitive(self, sample_network: CharityPartnerNetwork):
        results = sample_network.search("GIRL SCOUTS")
        assert len(results) == 2

    def test_states_covered(self, sample_network: CharityPartnerNetwork):
        states = sample_network.states_covered()
        assert states == {"OH", "TX", "CA"}

    def test_categories_covered(self, sample_network: CharityPartnerNetwork):
        cats = sample_network.categories_covered()
        assert cats == {CharityCategory.YOUTH, CharityCategory.EDUCATION, CharityCategory.COMMUNITY}

    def test_empty_network_returns_empty_lists(self):
        network = CharityPartnerNetwork(charities=[])
        assert network.by_state("OH") == []
        assert network.by_category(CharityCategory.YOUTH) == []
        assert network.by_state_and_category("OH", CharityCategory.YOUTH) == []
        assert network.search("anything") == []
        assert network.states_covered() == set()
        assert network.categories_covered() == set()
