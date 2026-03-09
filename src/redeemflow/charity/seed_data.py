"""50-state charity partner seed data — 10 anchor orgs x 51 jurisdictions + supplementary.

Beck: The simplest thing that could work. Systematic patterns over hand-curated accuracy.
Fowler: Seed data is a builder — the structure matters more than individual entries.
"""

from __future__ import annotations

from redeemflow.charity.models import CharityCategory, CharityOrganization, CharityPartnerNetwork

# All 50 US states + DC with capitals (for Junior League city references)
_STATES: dict[str, str] = {
    "AL": "Montgomery",
    "AK": "Juneau",
    "AZ": "Phoenix",
    "AR": "Little Rock",
    "CA": "Sacramento",
    "CO": "Denver",
    "CT": "Hartford",
    "DE": "Dover",
    "FL": "Tallahassee",
    "GA": "Atlanta",
    "HI": "Honolulu",
    "ID": "Boise",
    "IL": "Springfield",
    "IN": "Indianapolis",
    "IA": "Des Moines",
    "KS": "Topeka",
    "KY": "Frankfort",
    "LA": "Baton Rouge",
    "ME": "Augusta",
    "MD": "Annapolis",
    "MA": "Boston",
    "MI": "Lansing",
    "MN": "Saint Paul",
    "MS": "Jackson",
    "MO": "Jefferson City",
    "MT": "Helena",
    "NE": "Lincoln",
    "NV": "Carson City",
    "NH": "Concord",
    "NJ": "Trenton",
    "NM": "Santa Fe",
    "NY": "Albany",
    "NC": "Raleigh",
    "ND": "Bismarck",
    "OH": "Columbus",
    "OK": "Oklahoma City",
    "OR": "Salem",
    "PA": "Harrisburg",
    "RI": "Providence",
    "SC": "Columbia",
    "SD": "Pierre",
    "TN": "Nashville",
    "TX": "Austin",
    "UT": "Salt Lake City",
    "VT": "Montpelier",
    "VA": "Richmond",
    "WA": "Olympia",
    "WV": "Charleston",
    "WI": "Madison",
    "WY": "Cheyenne",
    "DC": "Washington",
}

_STATE_NAMES: dict[str, str] = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming",
    "DC": "District of Columbia",
}


# --- Anchor Org Definitions ---
# Each returns a CharityOrganization for a given state code.


def _sba_wbc(state: str) -> CharityOrganization:
    city = _STATES[state]
    return CharityOrganization(
        name="SBA Women's Business Centers",
        category=CharityCategory.BUSINESS,
        state=state,
        chapter_name=f"Women's Business Center of {city}",
        national_url="https://www.sba.gov/local-assistance/find/?type=Women%27s%20Business%20Center",
        is_501c3=False,
        description=(
            "SBA-funded centers providing counseling, training, and resources"
            " to women entrepreneurs. Government program, not a 501(c)(3)."
        ),
    )


def _girl_scouts(state: str) -> CharityOrganization:
    name = _STATE_NAMES[state]
    return CharityOrganization(
        name="Girl Scouts of the USA",
        category=CharityCategory.YOUTH,
        state=state,
        chapter_name=f"Girl Scouts of {name}",
        national_url="https://www.girlscouts.org",
        is_501c3=True,
        description="Building girls of courage, confidence, and character who make the world a better place.",
    )


def _girls_who_code(state: str) -> CharityOrganization:
    name = _STATE_NAMES[state]
    return CharityOrganization(
        name="Girls Who Code",
        category=CharityCategory.STEM,
        state=state,
        chapter_name=f"Girls Who Code - {name} Clubs",
        national_url="https://girlswhocode.com",
        is_501c3=True,
        description="Closing the gender gap in technology through coding clubs, summer programs, and college loops.",
    )


def _junior_league(state: str) -> CharityOrganization:
    city = _STATES[state]
    return CharityOrganization(
        name="Junior League",
        category=CharityCategory.COMMUNITY,
        state=state,
        chapter_name=f"Junior League of {city}",
        national_url="https://www.ajli.org",
        is_501c3=True,
        description="Women building better communities through trained volunteers and community leadership.",
    )


def _lwv(state: str) -> CharityOrganization:
    name = _STATE_NAMES[state]
    return CharityOrganization(
        name="League of Women Voters",
        category=CharityCategory.CIVIC,
        state=state,
        chapter_name=f"League of Women Voters of {name}",
        national_url="https://www.lwv.org",
        is_501c3=True,
        description="Empowering voters and defending democracy through advocacy, education, and litigation.",
    )


def _aauw(state: str) -> CharityOrganization:
    name = _STATE_NAMES[state]
    return CharityOrganization(
        name="AAUW",
        category=CharityCategory.EDUCATION,
        state=state,
        chapter_name=f"AAUW {name} Branch",
        national_url="https://www.aauw.org",
        is_501c3=True,
        description="Advancing equity for women and girls through advocacy, education, and research.",
    )


def _gfwc(state: str) -> CharityOrganization:
    name = _STATE_NAMES[state]
    return CharityOrganization(
        name="GFWC",
        category=CharityCategory.COMMUNITY,
        state=state,
        chapter_name=f"GFWC {name} Federation",
        national_url="https://www.gfwc.org",
        is_501c3=True,
        description="Community improvement through volunteer service in arts, conservation, education, and more.",
    )


def _national_pta(state: str) -> CharityOrganization:
    name = _STATE_NAMES[state]
    return CharityOrganization(
        name="National PTA",
        category=CharityCategory.EDUCATION,
        state=state,
        chapter_name=f"{name} PTA",
        national_url="https://www.pta.org",
        is_501c3=True,
        description="Connecting families, schools, and communities to support student success.",
    )


def _best_friends(state: str) -> CharityOrganization:
    name = _STATE_NAMES[state]
    return CharityOrganization(
        name="Best Friends Animal Society",
        category=CharityCategory.ANIMAL_WELFARE,
        state=state,
        chapter_name=f"Best Friends Network Partner - {name}",
        national_url="https://bestfriends.org",
        is_501c3=True,
        description="Leading the no-kill movement through shelter partnerships and community programs.",
    )


def _habitat(state: str) -> CharityOrganization:
    name = _STATE_NAMES[state]
    return CharityOrganization(
        name="Habitat for Humanity Women Build",
        category=CharityCategory.COMMUNITY,
        state=state,
        chapter_name=f"Habitat for Humanity Women Build - {name}",
        national_url="https://www.habitat.org",
        is_501c3=True,
        description="Empowering women to build homes and communities alongside families in need.",
    )


# --- Supplementary Org Definitions ---

# YWCA: ~45 states (exclude AK, MT, ND, SD, WV, WY)
_YWCA_EXCLUDE = {"AK", "MT", "ND", "SD", "WV", "WY"}


def _ywca(state: str) -> CharityOrganization:
    city = _STATES[state]
    return CharityOrganization(
        name="YWCA",
        category=CharityCategory.COMMUNITY,
        state=state,
        chapter_name=f"YWCA {city}",
        national_url="https://www.ywca.org",
        is_501c3=True,
        description="Eliminating racism, empowering women, and promoting peace, justice, and freedom.",
    )


# Dress for Success: ~35 states
_DFS_STATES = {
    "AL",
    "AZ",
    "AR",
    "CA",
    "CO",
    "CT",
    "FL",
    "GA",
    "HI",
    "IL",
    "IN",
    "IA",
    "KS",
    "KY",
    "LA",
    "MD",
    "MA",
    "MI",
    "MN",
    "MS",
    "MO",
    "NJ",
    "NY",
    "NC",
    "OH",
    "OK",
    "OR",
    "PA",
    "SC",
    "TN",
    "TX",
    "UT",
    "VA",
    "WA",
    "WI",
}


def _dress_for_success(state: str) -> CharityOrganization:
    city = _STATES[state]
    return CharityOrganization(
        name="Dress for Success",
        category=CharityCategory.WORKFORCE,
        state=state,
        chapter_name=f"Dress for Success {city}",
        national_url="https://dressforsuccess.org",
        is_501c3=True,
        description=(
            "Empowering women to achieve economic independence through professional attire and development tools."
        ),
    )


# Girls Inc.: ~30 states
_GIRLS_INC_STATES = {
    "AL",
    "AZ",
    "CA",
    "CO",
    "CT",
    "DE",
    "FL",
    "GA",
    "IL",
    "IN",
    "KY",
    "LA",
    "MA",
    "MI",
    "MN",
    "MS",
    "MO",
    "NE",
    "NJ",
    "NY",
    "NC",
    "OH",
    "OK",
    "OR",
    "PA",
    "SC",
    "TN",
    "TX",
    "VA",
    "WA",
}


def _girls_inc(state: str) -> CharityOrganization:
    city = _STATES[state]
    return CharityOrganization(
        name="Girls Inc.",
        category=CharityCategory.YOUTH,
        state=state,
        chapter_name=f"Girls Inc. of {city}",
        national_url="https://girlsinc.org",
        is_501c3=True,
        description="Inspiring all girls to be strong, smart, and bold through direct service and advocacy.",
    )


# --- Build the complete charity list ---


def _build_all_charities() -> list[CharityOrganization]:
    charities: list[CharityOrganization] = []

    # 10 anchor orgs x 51 states = 510 entries
    anchor_builders = [
        _sba_wbc,
        _girl_scouts,
        _girls_who_code,
        _junior_league,
        _lwv,
        _aauw,
        _gfwc,
        _national_pta,
        _best_friends,
        _habitat,
    ]
    for state in _STATES:
        for builder in anchor_builders:
            charities.append(builder(state))

    # Supplementary orgs
    for state in _STATES:
        if state not in _YWCA_EXCLUDE:
            charities.append(_ywca(state))

    for state in _DFS_STATES:
        charities.append(_dress_for_success(state))

    for state in _GIRLS_INC_STATES:
        charities.append(_girls_inc(state))

    return charities


ALL_CHARITIES: list[CharityOrganization] = _build_all_charities()
CHARITY_NETWORK: CharityPartnerNetwork = CharityPartnerNetwork(charities=ALL_CHARITIES)
