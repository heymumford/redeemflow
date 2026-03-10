"""E2E test conftest — configurable base URL for local or production testing."""

from __future__ import annotations

import os

import httpx
import pytest


@pytest.fixture(scope="session")
def base_url() -> str:
    """Base URL for e2e tests. Defaults to local TestClient, override with E2E_BASE_URL."""
    return os.environ.get("E2E_BASE_URL", "http://testserver")


@pytest.fixture()
def e2e_client(base_url) -> httpx.Client:
    """HTTP client for e2e tests."""
    return httpx.Client(base_url=base_url, timeout=30.0)


@pytest.fixture()
def auth_headers() -> dict[str, str]:
    """Auth headers for authenticated e2e tests."""
    token = os.environ.get("E2E_AUTH_TOKEN", "test-token-eric")
    return {"Authorization": f"Bearer {token}"}
