"""E2E smoke tests — health and docs endpoints prove the app boots and serves.

Beck: The simplest possible proof of life.
Fowler: Walking skeleton — if these fail, nothing else matters.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from redeemflow.app import create_app
from redeemflow.ports import PortBundle


def _make_client() -> TestClient:
    """Create a deterministic test client using fake adapters."""
    return TestClient(create_app(ports=PortBundle()))


class TestHealthSmoke:
    """Health endpoint returns 200 with correct structure."""

    def setup_method(self):
        self.client = _make_client()

    def test_health_returns_200(self):
        response = self.client.get("/health")
        assert response.status_code == 200

    def test_health_returns_json(self):
        response = self.client.get("/health")
        body = response.json()
        assert isinstance(body, dict)

    def test_health_has_status_field(self):
        response = self.client.get("/health")
        body = response.json()
        assert body["status"] in ("ok", "degraded")

    def test_health_has_version_field(self):
        response = self.client.get("/health")
        body = response.json()
        assert "version" in body
        # Version is a non-empty string
        assert len(body["version"]) > 0

    def test_health_has_dependencies(self):
        response = self.client.get("/health")
        body = response.json()
        assert "dependencies" in body
        assert "database" in body["dependencies"]


class TestDocsSmoke:
    """OpenAPI docs endpoint is available and renders."""

    def setup_method(self):
        self.client = _make_client()

    def test_docs_returns_200(self):
        """Swagger UI renders at /docs."""
        response = self.client.get("/docs")
        assert response.status_code == 200

    def test_docs_returns_html(self):
        response = self.client.get("/docs")
        assert "text/html" in response.headers.get("content-type", "")

    def test_redoc_returns_200(self):
        """ReDoc renders at /redoc."""
        response = self.client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_json_returns_200(self):
        """Raw OpenAPI spec is served at /openapi.json."""
        response = self.client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert schema["info"]["title"] == "RedeemFlow"

    def test_openapi_has_paths(self):
        """OpenAPI spec contains route paths."""
        response = self.client.get("/openapi.json")
        schema = response.json()
        assert len(schema["paths"]) > 0


class TestPortBundleDI:
    """App factory accepts a PortBundle for DI — tests can inject fakes."""

    def test_create_app_accepts_port_bundle(self):
        ports = PortBundle()
        app = create_app(ports=ports)
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200

    def test_create_app_without_ports_defaults_to_env(self):
        app = create_app()
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200

    def test_portfolio_uses_injected_port(self):
        """Verify the injected adapter is actually used by checking its data."""
        from redeemflow.portfolio.fake_adapter import FakePortfolioAdapter

        # Create a custom adapter with known empty data
        empty_adapter = FakePortfolioAdapter()
        # Clear the test data to prove we're using THIS adapter
        empty_adapter._data = {"auth0|eric": []}

        ports = PortBundle(portfolio=empty_adapter)
        app = create_app(ports=ports)
        client = TestClient(app)
        response = client.get(
            "/api/portfolio",
            headers={"Authorization": "Bearer test-token-eric"},
        )
        assert response.status_code == 200
        body = response.json()
        # Empty adapter returns empty balances — proves injection works
        assert body["balances"] == []
        assert body["total_value_dollars"] == "0"

    def test_portfolio_sync_endpoint_exists(self):
        ports = PortBundle()
        app = create_app(ports=ports)
        client = TestClient(app)
        response = client.post(
            "/api/portfolio/sync",
            headers={"Authorization": "Bearer test-token-eric"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] in ("success", "partial", "failed")
        assert "programs_synced" in body

    def test_portfolio_default_returns_balances(self):
        """Default PortBundle has test data — portfolios are non-empty."""
        ports = PortBundle()
        app = create_app(ports=ports)
        client = TestClient(app)
        response = client.get(
            "/api/portfolio",
            headers={"Authorization": "Bearer test-token-eric"},
        )
        assert response.status_code == 200
        body = response.json()
        assert len(body["balances"]) > 0
