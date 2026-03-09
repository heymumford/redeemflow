"""Root conftest — shared fixtures for all test tiers."""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from redeemflow.app import create_app
from redeemflow.identity.models import User


@pytest.fixture()
def app():
    """Create a fresh FastAPI app instance."""
    return create_app()


@pytest.fixture()
def client(app):
    """TestClient wired to the app — no auth."""
    return TestClient(app)


@pytest.fixture()
def auth_client(app):
    """TestClient with test-token auth header."""
    c = TestClient(app)
    c.headers["Authorization"] = "Bearer test-token-eric"
    return c


@pytest.fixture()
def test_user() -> User:
    """Standard test user (free tier)."""
    return User(id="user-test-1", email="test@example.com", name="Test User", tier="free")


@pytest.fixture()
def premium_user() -> User:
    """Premium tier test user."""
    return User(id="user-premium-1", email="premium@example.com", name="Premium User", tier="premium")


@pytest.fixture()
def sample_decimal() -> Decimal:
    """Standard Decimal for financial assertions."""
    return Decimal("1.50")
