"""RED tests for the 50-state charity seed data.

Fitness tests: structural guarantees about seed data coverage and correctness.
"""

from __future__ import annotations

from redeemflow.charity.models import CharityCategory
from redeemflow.charity.seed_data import ALL_CHARITIES, CHARITY_NETWORK

# All 50 US states + DC
ALL_STATES = {
    "AL",
    "AK",
    "AZ",
    "AR",
    "CA",
    "CO",
    "CT",
    "DE",
    "FL",
    "GA",
    "HI",
    "ID",
    "IL",
    "IN",
    "IA",
    "KS",
    "KY",
    "LA",
    "ME",
    "MD",
    "MA",
    "MI",
    "MN",
    "MS",
    "MO",
    "MT",
    "NE",
    "NV",
    "NH",
    "NJ",
    "NM",
    "NY",
    "NC",
    "ND",
    "OH",
    "OK",
    "OR",
    "PA",
    "RI",
    "SC",
    "SD",
    "TN",
    "TX",
    "UT",
    "VT",
    "VA",
    "WA",
    "WV",
    "WI",
    "WY",
    "DC",
}

ANCHOR_ORG_NAMES = {
    "SBA Women's Business Centers",
    "Girl Scouts of the USA",
    "Girls Who Code",
    "Junior League",
    "League of Women Voters",
    "AAUW",
    "GFWC",
    "National PTA",
    "Best Friends Animal Society",
    "Habitat for Humanity Women Build",
}


class TestCharitySeedData:
    def test_all_50_states_plus_dc_covered(self):
        covered = CHARITY_NETWORK.states_covered()
        assert len(covered) >= 51
        assert ALL_STATES.issubset(covered)

    def test_minimum_10_orgs_per_state(self):
        for state in ALL_STATES:
            orgs = CHARITY_NETWORK.by_state(state)
            assert len(orgs) >= 10, f"State {state} has only {len(orgs)} orgs, expected >= 10"

    def test_all_anchor_orgs_present(self):
        names_in_data = {c.name for c in ALL_CHARITIES}
        for anchor in ANCHOR_ORG_NAMES:
            assert anchor in names_in_data, f"Missing anchor org: {anchor}"

    def test_all_categories_covered(self):
        categories = CHARITY_NETWORK.categories_covered()
        # At minimum, the categories used by anchor orgs
        expected_categories = {
            CharityCategory.BUSINESS,
            CharityCategory.YOUTH,
            CharityCategory.STEM,
            CharityCategory.COMMUNITY,
            CharityCategory.CIVIC,
            CharityCategory.EDUCATION,
            CharityCategory.ANIMAL_WELFARE,
        }
        assert expected_categories.issubset(categories)

    def test_total_charity_count(self):
        assert len(ALL_CHARITIES) >= 510

    def test_501c3_status_correct(self):
        for charity in ALL_CHARITIES:
            if charity.name == "SBA Women's Business Centers":
                assert charity.is_501c3 is False, f"SBA WBC in {charity.state} should not be 501c3"
            else:
                assert charity.is_501c3 is True, f"{charity.name} in {charity.state} should be 501c3"

    def test_all_charities_have_national_url(self):
        for charity in ALL_CHARITIES:
            assert charity.national_url, f"{charity.name} in {charity.state} missing national_url"

    def test_all_charities_have_chapter_name(self):
        for charity in ALL_CHARITIES:
            assert charity.chapter_name, f"{charity.name} in {charity.state} missing chapter_name"

    def test_charity_network_instance_matches_all_charities(self):
        assert len(CHARITY_NETWORK.charities) == len(ALL_CHARITIES)

    def test_supplementary_orgs_present(self):
        names = {c.name for c in ALL_CHARITIES}
        assert "YWCA" in names
        assert "Dress for Success" in names
        assert "Girls Inc." in names
