"""OpenAPI contract snapshot — locks API schema against accidental drift.

Beck: If the API shape changes, it must be intentional.
Fowler: Contract-first design — the schema is the shared agreement.

When routes are added or modified, update the snapshot:
    uv run pytest tests/contract/test_openapi_snapshot.py --snapshot-update

The snapshot lives in tests/contract/openapi_snapshot.json. Any diff
between the live schema and the snapshot fails the test.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from redeemflow.app import create_app

SNAPSHOT_PATH = Path(__file__).parent / "openapi_snapshot.json"


def _normalize_schema(schema: dict) -> dict:
    """Strip volatile fields (servers, description details) for stable comparison."""
    # Keep paths, components, info.version, info.title — the contract surface
    normalized = {
        "info": {
            "title": schema.get("info", {}).get("title"),
            "version": schema.get("info", {}).get("version"),
        },
        "paths": {},
    }

    # Sort paths and extract method + response codes (the contract)
    for path in sorted(schema.get("paths", {})):
        path_item = schema["paths"][path]
        normalized_path: dict = {}
        for method in sorted(path_item):
            if method in ("get", "post", "put", "delete", "patch"):
                endpoint = path_item[method]
                normalized_endpoint: dict = {
                    "responses": {},
                }
                # Capture request body schema reference if present
                if "requestBody" in endpoint:
                    normalized_endpoint["requestBody"] = endpoint["requestBody"]
                # Capture response status codes and their schema references
                for status_code in sorted(endpoint.get("responses", {})):
                    resp = endpoint["responses"][status_code]
                    normalized_endpoint["responses"][status_code] = resp
                # Capture parameters
                if "parameters" in endpoint:
                    normalized_endpoint["parameters"] = endpoint["parameters"]
                normalized_path[method] = normalized_endpoint
        normalized["paths"][path] = normalized_path

    # Include component schemas — the data contract
    if "components" in schema:
        normalized["components"] = schema["components"]

    return normalized


def _load_snapshot() -> dict | None:
    """Load existing snapshot, or None if it doesn't exist."""
    if not SNAPSHOT_PATH.exists():
        return None
    with SNAPSHOT_PATH.open() as f:
        return json.load(f)


def _save_snapshot(schema: dict) -> None:
    """Write snapshot to disk."""
    with SNAPSHOT_PATH.open("w") as f:
        json.dump(schema, f, indent=2, sort_keys=True)
        f.write("\n")


@pytest.mark.contract
class TestOpenApiSnapshot:
    """Verify the API schema matches the locked snapshot."""

    def test_openapi_schema_is_valid(self):
        """Schema generates without errors and has expected top-level keys."""
        app = create_app()
        schema = app.openapi()
        assert "info" in schema
        assert "paths" in schema
        assert schema["info"]["title"] == "RedeemFlow"

    def test_all_route_groups_present(self):
        """Every route group is mounted — the walking skeleton is complete."""
        app = create_app()
        schema = app.openapi()
        paths = set(schema["paths"].keys())

        # Valuations
        assert "/api/calculate" in paths, "Valuations routes missing"
        assert "/api/programs" in paths, "Programs list route missing"

        # Billing
        assert "/api/billing/subscribe" in paths, "Billing routes missing"
        assert "/api/billing/cancel" in paths, "Billing cancel route missing"

        # Charity
        assert "/api/charities" in paths, "Charity routes missing"
        assert "/api/donate" in paths, "Donate route missing"

        # Optimization
        assert "/api/optimize" in paths, "Optimization routes missing"

        # Search
        assert "/api/award-search" in paths, "Search routes missing"

        # Community
        assert "/api/pools" in paths, "Community pool routes missing"
        assert "/api/forum/posts" in paths, "Forum routes missing"
        assert "/api/founders/apply" in paths, "Founders routes missing"

        # Portfolio
        assert "/api/portfolio" in paths, "Portfolio routes missing"
        assert "/api/portfolio/sync" in paths, "Portfolio sync route missing"
        assert "/api/recommendations" in paths, "Recommendations route missing"

        # Health
        assert "/health" in paths, "Health route missing"

    def test_schema_matches_snapshot(self):
        """The normalized schema matches the locked snapshot.

        If this fails after an intentional change, update the snapshot:
            uv run pytest tests/contract/test_openapi_snapshot.py --snapshot-update
        """
        app = create_app()
        schema = app.openapi()
        normalized = _normalize_schema(schema)

        existing = _load_snapshot()
        if existing is None:
            # First run — create the snapshot
            _save_snapshot(normalized)
            pytest.skip("Snapshot created — re-run to verify")

        # Compare normalized schemas
        current_json = json.dumps(normalized, indent=2, sort_keys=True)
        snapshot_json = json.dumps(existing, indent=2, sort_keys=True)

        if current_json != snapshot_json:
            # Find what changed
            current_paths = set(normalized.get("paths", {}).keys())
            snapshot_paths = set(existing.get("paths", {}).keys())
            added = current_paths - snapshot_paths
            removed = snapshot_paths - current_paths

            msg_parts = ["OpenAPI schema has drifted from snapshot."]
            if added:
                msg_parts.append(f"  Added paths: {sorted(added)}")
            if removed:
                msg_parts.append(f"  Removed paths: {sorted(removed)}")
            msg_parts.append("Update snapshot: uv run pytest tests/contract/test_openapi_snapshot.py --snapshot-update")
            pytest.fail("\n".join(msg_parts))

    def test_minimum_endpoint_count(self):
        """The API has at least 25 endpoints — prevents accidental route deletion."""
        app = create_app()
        schema = app.openapi()
        endpoint_count = 0
        for _path, methods in schema["paths"].items():
            for method in methods:
                if method in ("get", "post", "put", "delete", "patch"):
                    endpoint_count += 1
        assert endpoint_count >= 25, f"Only {endpoint_count} endpoints — expected at least 25"
