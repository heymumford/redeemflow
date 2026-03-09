"""Unit tests for Women Founders Travel Network.

TDD: These tests define the contract for FounderDirectory, FounderProfile.
"""

from __future__ import annotations

import pytest

from redeemflow.community.founders_network import FounderDirectory, FounderProfile, FounderStatus


class TestFounderStatus:
    def test_pending(self):
        assert FounderStatus.PENDING == "pending"

    def test_verified(self):
        assert FounderStatus.VERIFIED == "verified"

    def test_active(self):
        assert FounderStatus.ACTIVE == "active"

    def test_suspended(self):
        assert FounderStatus.SUSPENDED == "suspended"

    def test_all_statuses_count(self):
        assert len(FounderStatus) == 4


class TestFounderProfile:
    def test_creation_with_all_fields(self):
        profile = FounderProfile(
            user_id="auth0|eric",
            name="Eric",
            email="eric@example.com",
            company_name="TravelCo",
            industry="Travel Tech",
            verification_source="NAWBO",
            status=FounderStatus.PENDING,
            joined_at="2026-01-01T00:00:00+00:00",
            bio="Passionate about travel rewards.",
            travel_interests=["Tokyo", "Paris", "Southeast Asia"],
            is_mentor=True,
            mentor_topics=["fundraising", "travel hacking"],
        )
        assert profile.user_id == "auth0|eric"
        assert profile.name == "Eric"
        assert profile.email == "eric@example.com"
        assert profile.company_name == "TravelCo"
        assert profile.industry == "Travel Tech"
        assert profile.verification_source == "NAWBO"
        assert profile.status == FounderStatus.PENDING
        assert profile.bio == "Passionate about travel rewards."
        assert profile.travel_interests == ["Tokyo", "Paris", "Southeast Asia"]
        assert profile.is_mentor is True
        assert profile.mentor_topics == ["fundraising", "travel hacking"]

    def test_defaults(self):
        profile = FounderProfile(
            user_id="auth0|eric",
            name="Eric",
            email="eric@example.com",
            status=FounderStatus.PENDING,
            joined_at="2026-01-01T00:00:00+00:00",
        )
        assert profile.company_name is None
        assert profile.industry is None
        assert profile.verification_source is None
        assert profile.bio is None
        assert profile.travel_interests == []
        assert profile.is_mentor is False
        assert profile.mentor_topics == []

    def test_mutable_status(self):
        """FounderProfile is a mutable state holder."""
        profile = FounderProfile(
            user_id="auth0|eric",
            name="Eric",
            email="eric@example.com",
            status=FounderStatus.PENDING,
            joined_at="2026-01-01T00:00:00+00:00",
        )
        profile.status = FounderStatus.ACTIVE
        assert profile.status == FounderStatus.ACTIVE


class TestFounderDirectory:
    def setup_method(self):
        self.directory = FounderDirectory()

    def test_apply_creates_pending_profile(self):
        profile = self.directory.apply(
            user_id="auth0|eric",
            name="Eric",
            email="eric@example.com",
            company_name="TravelCo",
            verification_source="NAWBO",
            bio="Travel enthusiast",
            travel_interests=["Tokyo", "Paris"],
        )
        assert profile.user_id == "auth0|eric"
        assert profile.status == FounderStatus.PENDING
        assert profile.company_name == "TravelCo"
        assert profile.verification_source == "NAWBO"
        assert profile.travel_interests == ["Tokyo", "Paris"]

    def test_verify_transitions_to_active(self):
        self.directory.apply(
            user_id="auth0|eric",
            name="Eric",
            email="eric@example.com",
            company_name="TravelCo",
            verification_source="WBENC",
            bio="Founder",
            travel_interests=["London"],
        )
        profile = self.directory.verify("auth0|eric")
        assert profile.status == FounderStatus.ACTIVE

    def test_verify_nonexistent_raises(self):
        with pytest.raises(ValueError, match="Member not found"):
            self.directory.verify("nonexistent")

    def test_get_profile(self):
        self.directory.apply(
            user_id="auth0|eric",
            name="Eric",
            email="eric@example.com",
            company_name="TravelCo",
            verification_source="SBA",
            bio="Builder",
            travel_interests=["Berlin"],
        )
        profile = self.directory.get_profile("auth0|eric")
        assert profile is not None
        assert profile.name == "Eric"

    def test_get_profile_not_found(self):
        assert self.directory.get_profile("nonexistent") is None

    def test_list_members_all(self):
        self.directory.apply("auth0|eric", "Eric", "eric@example.com", "Co1", "NAWBO", "Bio1", ["Tokyo"])
        self.directory.apply("auth0|steve", "Steve", "steve@example.com", "Co2", "WBENC", "Bio2", ["Paris"])
        members = self.directory.list_members()
        assert len(members) == 2

    def test_list_members_with_status_filter(self):
        self.directory.apply("auth0|eric", "Eric", "eric@example.com", "Co1", "NAWBO", "Bio1", ["Tokyo"])
        self.directory.apply("auth0|steve", "Steve", "steve@example.com", "Co2", "WBENC", "Bio2", ["Paris"])
        self.directory.verify("auth0|eric")

        pending = self.directory.list_members(status=FounderStatus.PENDING)
        assert len(pending) == 1
        assert pending[0].user_id == "auth0|steve"

        active = self.directory.list_members(status=FounderStatus.ACTIVE)
        assert len(active) == 1
        assert active[0].user_id == "auth0|eric"

    def test_search_members_matches_name(self):
        self.directory.apply("auth0|eric", "Eric Mumford", "eric@example.com", "Co1", "NAWBO", "Bio1", ["Tokyo"])
        self.directory.apply("auth0|steve", "Steve Jobs", "steve@example.com", "Co2", "WBENC", "Bio2", ["Paris"])
        results = self.directory.search_members("Eric")
        assert len(results) == 1
        assert results[0].user_id == "auth0|eric"

    def test_search_members_matches_company(self):
        self.directory.apply("auth0|eric", "Eric", "eric@example.com", "TravelCo", "NAWBO", "Bio1", ["Tokyo"])
        self.directory.apply("auth0|steve", "Steve", "steve@example.com", "FinTech Inc", "WBENC", "Bio2", ["Paris"])
        results = self.directory.search_members("TravelCo")
        assert len(results) == 1
        assert results[0].user_id == "auth0|eric"

    def test_search_members_case_insensitive(self):
        self.directory.apply("auth0|eric", "Eric", "eric@example.com", "TravelCo", "NAWBO", "Bio1", ["Tokyo"])
        results = self.directory.search_members("travelco")
        assert len(results) == 1

    def test_find_travel_companions(self):
        self.directory.apply("auth0|eric", "Eric", "eric@example.com", "Co1", "NAWBO", "Bio1", ["Tokyo", "Paris"])
        self.directory.apply("auth0|steve", "Steve", "steve@example.com", "Co2", "WBENC", "Bio2", ["London"])
        self.directory.apply("auth0|jane", "Jane", "jane@example.com", "Co3", "SBA", "Bio3", ["Tokyo", "Berlin"])

        companions = self.directory.find_travel_companions("Tokyo")
        assert len(companions) == 2
        user_ids = {c.user_id for c in companions}
        assert user_ids == {"auth0|eric", "auth0|jane"}

    def test_find_travel_companions_case_insensitive(self):
        self.directory.apply("auth0|eric", "Eric", "eric@example.com", "Co1", "NAWBO", "Bio1", ["Tokyo"])
        companions = self.directory.find_travel_companions("tokyo")
        assert len(companions) == 1

    def test_find_mentors(self):
        self.directory.apply("auth0|eric", "Eric", "eric@example.com", "Co1", "NAWBO", "Bio1", ["Tokyo"])
        profile = self.directory.get_profile("auth0|eric")
        assert profile is not None
        profile.is_mentor = True
        profile.mentor_topics = ["fundraising", "travel hacking"]

        self.directory.apply("auth0|steve", "Steve", "steve@example.com", "Co2", "WBENC", "Bio2", ["Paris"])
        profile2 = self.directory.get_profile("auth0|steve")
        assert profile2 is not None
        profile2.is_mentor = True
        profile2.mentor_topics = ["marketing"]

        mentors = self.directory.find_mentors("fundraising")
        assert len(mentors) == 1
        assert mentors[0].user_id == "auth0|eric"

    def test_find_mentors_case_insensitive(self):
        self.directory.apply("auth0|eric", "Eric", "eric@example.com", "Co1", "NAWBO", "Bio1", ["Tokyo"])
        profile = self.directory.get_profile("auth0|eric")
        assert profile is not None
        profile.is_mentor = True
        profile.mentor_topics = ["Fundraising"]

        mentors = self.directory.find_mentors("fundraising")
        assert len(mentors) == 1

    def test_update_profile(self):
        self.directory.apply("auth0|eric", "Eric", "eric@example.com", "Co1", "NAWBO", "Bio1", ["Tokyo"])
        updated = self.directory.update_profile("auth0|eric", company_name="NewCo", bio="Updated bio")
        assert updated.company_name == "NewCo"
        assert updated.bio == "Updated bio"
        # Other fields unchanged
        assert updated.name == "Eric"

    def test_update_profile_not_found_raises(self):
        with pytest.raises(ValueError, match="Member not found"):
            self.directory.update_profile("nonexistent", bio="test")
