"""Contract test conftest — snapshot update support."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

SNAPSHOT_PATH = Path(__file__).parent / "openapi_snapshot.json"


def pytest_addoption(parser):
    """Add --snapshot-update flag for OpenAPI schema updates."""
    parser.addoption("--snapshot-update", action="store_true", default=False, help="Update OpenAPI snapshot")


@pytest.fixture(autouse=True)
def _update_snapshot_if_requested(request):
    """When --snapshot-update is passed, regenerate the OpenAPI snapshot."""
    yield
    if request.config.getoption("--snapshot-update", default=False):
        from redeemflow.app import create_app
        from tests.contract.test_openapi_snapshot import _normalize_schema

        app = create_app()
        schema = app.openapi()
        normalized = _normalize_schema(schema)
        with SNAPSHOT_PATH.open("w") as f:
            json.dump(normalized, f, indent=2, sort_keys=True)
            f.write("\n")
