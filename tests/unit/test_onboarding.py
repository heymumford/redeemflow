"""Tests for onboarding flow."""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from redeemflow.identity.onboarding import (
    OnboardingProfile,
    OnboardingReport,
    OnboardingStep,
    ProgramSelection,
    TravelStyle,
    complete_onboarding,
    generate_quick_wins,
    suggest_goals,
)


class TestProgramSelection:
    def test_frozen(self):
        p = ProgramSelection(program_code="chase-ur", estimated_balance=50000)
        with pytest.raises(AttributeError):
            p.estimated_balance = 0

    def test_defaults(self):
        p = ProgramSelection(program_code="chase-ur")
        assert p.estimated_balance == 0
        assert p.is_primary is False


class TestSuggestGoals:
    def test_airline_budget_traveler(self):
        programs = [ProgramSelection(program_code="united")]
        profile = OnboardingProfile(travel_style=TravelStyle.BUDGET, home_airport="SFO")
        goals = suggest_goals(programs, profile)
        assert len(goals) == 1
        assert goals[0].target_points == 25000
        assert goals[0].category == "flight"

    def test_airline_luxury_traveler(self):
        programs = [ProgramSelection(program_code="united")]
        profile = OnboardingProfile(travel_style=TravelStyle.LUXURY, home_airport="JFK")
        goals = suggest_goals(programs, profile)
        assert goals[0].target_points == 80000

    def test_hotel_program(self):
        programs = [ProgramSelection(program_code="hyatt")]
        profile = OnboardingProfile(travel_style=TravelStyle.COMFORT, home_airport="LAX")
        goals = suggest_goals(programs, profile)
        assert len(goals) == 1
        assert goals[0].category == "hotel"

    def test_bank_program(self):
        programs = [ProgramSelection(program_code="chase-ur")]
        profile = OnboardingProfile(travel_style=TravelStyle.COMFORT, home_airport="ORD")
        goals = suggest_goals(programs, profile)
        assert len(goals) == 1
        assert goals[0].category == "transfer"

    def test_multiple_programs(self):
        programs = [
            ProgramSelection(program_code="chase-ur"),
            ProgramSelection(program_code="united"),
            ProgramSelection(program_code="hyatt"),
        ]
        profile = OnboardingProfile(travel_style=TravelStyle.COMFORT, home_airport="SFO")
        goals = suggest_goals(programs, profile)
        assert len(goals) == 3

    def test_unknown_program_skipped(self):
        programs = [ProgramSelection(program_code="unknown-program")]
        profile = OnboardingProfile(travel_style=TravelStyle.BUDGET, home_airport="SFO")
        goals = suggest_goals(programs, profile)
        assert len(goals) == 0

    def test_not_interested_in_hotels(self):
        programs = [ProgramSelection(program_code="hyatt")]
        profile = OnboardingProfile(travel_style=TravelStyle.COMFORT, home_airport="SFO", interested_in_hotels=False)
        goals = suggest_goals(programs, profile)
        assert len(goals) == 0

    def test_goal_value_is_positive(self):
        programs = [ProgramSelection(program_code="chase-ur")]
        profile = OnboardingProfile(travel_style=TravelStyle.COMFORT, home_airport="SFO")
        goals = suggest_goals(programs, profile)
        assert goals[0].estimated_value > Decimal("0")


class TestGenerateQuickWins:
    def test_bank_program_quick_win(self):
        programs = [ProgramSelection(program_code="chase-ur")]
        profile = OnboardingProfile(travel_style=TravelStyle.COMFORT, home_airport="SFO")
        wins = generate_quick_wins(programs, profile)
        assert any("transfer bonus" in w.lower() for w in wins)

    def test_airline_quick_win(self):
        programs = [ProgramSelection(program_code="united")]
        profile = OnboardingProfile(travel_style=TravelStyle.COMFORT, home_airport="SFO")
        wins = generate_quick_wins(programs, profile)
        assert any("seasonal" in w.lower() for w in wins)

    def test_hotel_quick_win(self):
        programs = [ProgramSelection(program_code="hyatt")]
        profile = OnboardingProfile(travel_style=TravelStyle.COMFORT, home_airport="SFO")
        wins = generate_quick_wins(programs, profile)
        assert any("hotel" in w.lower() for w in wins)

    def test_frequent_traveler_gets_saved_search_tip(self):
        programs = [ProgramSelection(program_code="chase-ur")]
        profile = OnboardingProfile(travel_style=TravelStyle.COMFORT, home_airport="SFO", travel_frequency=8)
        wins = generate_quick_wins(programs, profile)
        assert any("saved search" in w.lower() for w in wins)

    def test_always_includes_expiration_tip(self):
        programs = [ProgramSelection(program_code="chase-ur")]
        profile = OnboardingProfile(travel_style=TravelStyle.BUDGET, home_airport="SFO")
        wins = generate_quick_wins(programs, profile)
        assert any("expiration" in w.lower() for w in wins)


class TestCompleteOnboarding:
    def test_produces_report(self):
        programs = [ProgramSelection(program_code="chase-ur", estimated_balance=50000)]
        profile = OnboardingProfile(travel_style=TravelStyle.COMFORT, home_airport="SFO")
        report = complete_onboarding("user1", programs, profile)
        assert isinstance(report, OnboardingReport)
        assert report.current_step == OnboardingStep.COMPLETE
        assert report.user_id == "user1"

    def test_estimated_value(self):
        programs = [ProgramSelection(program_code="chase-ur", estimated_balance=100000)]
        profile = OnboardingProfile(travel_style=TravelStyle.COMFORT, home_airport="SFO")
        report = complete_onboarding("user1", programs, profile)
        assert report.estimated_portfolio_value > Decimal("0")

    def test_zero_balance_zero_value(self):
        programs = [ProgramSelection(program_code="chase-ur", estimated_balance=0)]
        profile = OnboardingProfile(travel_style=TravelStyle.COMFORT, home_airport="SFO")
        report = complete_onboarding("user1", programs, profile)
        assert report.estimated_portfolio_value == Decimal("0")

    def test_has_next_actions(self):
        programs = [ProgramSelection(program_code="chase-ur")]
        profile = OnboardingProfile(travel_style=TravelStyle.COMFORT, home_airport="SFO")
        report = complete_onboarding("user1", programs, profile)
        assert len(report.next_actions) >= 3

    def test_multi_program_extra_action(self):
        programs = [
            ProgramSelection(program_code="chase-ur"),
            ProgramSelection(program_code="united"),
        ]
        profile = OnboardingProfile(travel_style=TravelStyle.COMFORT, home_airport="SFO")
        report = complete_onboarding("user1", programs, profile)
        assert any("transfer" in a.lower() for a in report.next_actions)

    def test_report_frozen(self):
        programs = [ProgramSelection(program_code="chase-ur")]
        profile = OnboardingProfile(travel_style=TravelStyle.BUDGET, home_airport="SFO")
        report = complete_onboarding("user1", programs, profile)
        with pytest.raises(AttributeError):
            report.user_id = "hacked"


class TestOnboardingAPI:
    AUTH_HEADERS = {"Authorization": "Bearer test-token-eric"}

    @pytest.fixture
    def client(self):
        from redeemflow.app import create_app
        from redeemflow.ports import PortBundle

        return TestClient(create_app(ports=PortBundle()))

    def test_onboarding_endpoint(self, client):
        resp = client.post(
            "/api/onboarding/complete",
            json={
                "programs": [{"program_code": "chase-ur", "estimated_balance": 50000}],
                "travel_style": "comfort",
                "home_airport": "SFO",
            },
            headers=self.AUTH_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "suggested_goals" in data
        assert "quick_wins" in data
        assert "estimated_portfolio_value" in data
        assert data["current_step"] == "complete"

    def test_onboarding_requires_auth(self, client):
        resp = client.post(
            "/api/onboarding/complete",
            json={
                "programs": [{"program_code": "chase-ur"}],
                "travel_style": "budget",
                "home_airport": "SFO",
            },
        )
        assert resp.status_code == 401

    def test_onboarding_minimal(self, client):
        resp = client.post(
            "/api/onboarding/complete",
            json={
                "programs": [],
                "travel_style": "budget",
                "home_airport": "LAX",
            },
            headers=self.AUTH_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["suggested_goals"] == []
