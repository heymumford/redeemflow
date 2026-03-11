"""FastAPI application factory with DI container.

Beck: One place to configure everything — middleware, adapters, routes.
Fowler: PortBundle is the DI container — tests inject fakes, production injects real adapters.

Database persistence is opt-in: set DATABASE_URL to enable Postgres.
Without it, all state is in-memory (dev/test mode).
"""

from __future__ import annotations

import logging
import os
import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from redeemflow import __version__
from redeemflow.admin.routes import router as admin_router
from redeemflow.billing.models import SubscriptionTier
from redeemflow.billing.routes import router as billing_router
from redeemflow.billing.stripe_adapter import FakePaymentProvider
from redeemflow.charity.donation_flow import DonationService, FakeDonationProvider
from redeemflow.charity.routes import router as charity_router
from redeemflow.charity.seed_data import CHARITY_NETWORK
from redeemflow.community.forum import ForumService
from redeemflow.community.founders_network import FounderDirectory
from redeemflow.community.models import PoolService
from redeemflow.community.routes import router as community_router
from redeemflow.identity.auth import AuthError
from redeemflow.identity.routes import router as identity_router
from redeemflow.middleware.logging import RequestLoggingMiddleware, configure_logging, get_logger
from redeemflow.middleware.rate_limit import limiter
from redeemflow.middleware.security_headers import SecurityHeadersMiddleware
from redeemflow.notifications.routes import router as notifications_router
from redeemflow.optimization.routes import router as optimization_router
from redeemflow.portfolio.fake_adapter import FakeBalanceFetcher
from redeemflow.portfolio.routes import router as portfolio_router
from redeemflow.ports import PortBundle
from redeemflow.redemptions.routes import router as redemptions_router
from redeemflow.search.routes import router as search_router
from redeemflow.valuations.routes import router as valuations_router
from redeemflow.valuations.seed_data import PROGRAM_VALUATIONS

# Suppress noisy uvicorn access logs when structured logging is active
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def _get_allowed_origins() -> list[str]:
    """CORS allowed origins from env, with sensible defaults."""
    origins_str = os.environ.get("ALLOWED_ORIGINS", "")
    if origins_str:
        return [o.strip() for o in origins_str.split(",") if o.strip()]
    # Default: localhost dev + production frontend
    return [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://redeemflow.com",
        "https://www.redeemflow.com",
    ]


def _init_db_repositories() -> dict | None:
    """Initialize Postgres repositories if DATABASE_URL is set."""
    from redeemflow.infra.database import create_engine, get_database_url, get_session_factory

    url = get_database_url()
    if not url:
        return None

    engine = create_engine(url)
    sf = get_session_factory(engine)

    from redeemflow.infra.pg_repositories import (
        PgDonationRepository,
        PgForumRepository,
        PgFounderRepository,
        PgPoolRepository,
    )

    return {
        "donation": PgDonationRepository(sf),
        "pool": PgPoolRepository(sf),
        "forum": PgForumRepository(sf),
        "founder": PgFounderRepository(sf),
    }


def _probe_database() -> str:
    """Check database connectivity. Returns 'ok' or error description."""
    from redeemflow.infra.database import get_database_url

    url = get_database_url()
    if not url:
        return "not_configured"

    engine = None
    try:
        from sqlalchemy import text

        from redeemflow.infra.database import create_engine

        engine = create_engine(url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        return "unreachable"
    finally:
        if engine is not None:
            engine.dispose()


def _select_adapters() -> dict:
    """Adapter factory — env-based dispatch for each Protocol boundary.

    Each boundary checks for its API key/config. If present, creates the real
    adapter. If absent, falls back to the fake. Zero code changes needed to switch.
    """
    adapters: dict = {}

    # Payment boundary: Stripe
    stripe_key = os.environ.get("STRIPE_SECRET_KEY")
    if stripe_key:
        webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
        from redeemflow.billing.stripe_adapter import TIER_PRICE_MAP, StripeAdapter

        # Override price IDs from environment if provided
        premium_price = os.environ.get("STRIPE_PREMIUM_PRICE_ID")
        pro_price = os.environ.get("STRIPE_PRO_PRICE_ID")
        if premium_price:
            TIER_PRICE_MAP[SubscriptionTier.PREMIUM] = premium_price
        if pro_price:
            TIER_PRICE_MAP[SubscriptionTier.PRO] = pro_price

        adapters["payment"] = StripeAdapter(api_key=stripe_key, webhook_secret=webhook_secret)
    else:
        adapters["payment"] = FakePaymentProvider()

    # Donation boundary: Change API
    change_key = os.environ.get("CHANGE_API_KEY")
    if change_key:
        from redeemflow.charity.donation_flow import ChangeApiAdapter

        adapters["donation_provider"] = ChangeApiAdapter(api_key=change_key)
    else:
        adapters["donation_provider"] = FakeDonationProvider()

    # Balance boundary: AwardWallet
    aw_key = os.environ.get("AWARDWALLET_API_KEY")
    if aw_key:
        from redeemflow.portfolio.awardwallet import AwardWalletAdapter

        adapters["balance_fetcher"] = AwardWalletAdapter(api_key=aw_key)
    else:
        adapters["balance_fetcher"] = FakeBalanceFetcher()

    # Award search boundary: Seats.aero
    seats_key = os.environ.get("SEATS_AERO_API_KEY")
    if seats_key:
        from redeemflow.search.award_search import SeatsAeroAdapter

        adapters["award_search"] = SeatsAeroAdapter(api_key=seats_key)
    else:
        from redeemflow.search.award_search import FakeAwardSearchProvider

        adapters["award_search"] = FakeAwardSearchProvider()

    return adapters


def create_app(ports: PortBundle | None = None) -> FastAPI:
    """Application factory — configure middleware, adapters, routes.

    Args:
        ports: Optional DI container. When None, adapters are selected
               from environment variables (real if keys present, fakes otherwise).
               Tests pass a PortBundle of fakes for zero-I/O verification.
    """
    configure_logging()

    app = FastAPI(
        title="RedeemFlow",
        version=__version__,
        description="Loyalty points optimization platform",
    )

    # --- Middleware (order matters: outermost first) ---

    # CORS — must be first so preflight OPTIONS requests get handled
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_get_allowed_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-Id"],
    )

    # Security headers — strip server ID, add OWASP headers
    app.add_middleware(SecurityHeadersMiddleware)

    # Structured request logging
    app.add_middleware(RequestLoggingMiddleware)

    # Rate limiting — SlowAPIMiddleware enforces default_limits globally
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # --- Routers (all 9 route groups) ---
    app.include_router(valuations_router)
    app.include_router(billing_router)
    app.include_router(charity_router)
    app.include_router(optimization_router)
    app.include_router(search_router)
    app.include_router(community_router)
    app.include_router(portfolio_router)
    app.include_router(redemptions_router)
    app.include_router(notifications_router)
    app.include_router(admin_router)
    app.include_router(identity_router)

    # --- Adapter factory ---
    # When ports is provided (testing), use its adapters directly.
    # Otherwise, select adapters from environment variables.
    repos = _init_db_repositories()

    if ports is not None:
        # DI path — tests inject all fakes via PortBundle
        app.state.payment_provider = ports.billing
        donation_provider = ports.donation
        app.state.award_search_provider = ports.award_search
        app.state.portfolio_port = ports.portfolio
    else:
        # Environment path — real adapters when API keys are present
        adapters = _select_adapters()
        app.state.payment_provider = adapters["payment"]
        donation_provider = adapters["donation_provider"]
        app.state.award_search_provider = adapters["award_search"]
        # Portfolio port must satisfy full PortfolioPort (fetch_balances + sync + fetch_portfolio).
        # AwardWalletAdapter only implements fetch_balances, so we use FakePortfolioAdapter
        # as the default until the real adapter implements the full Protocol.
        app.state.portfolio_port = adapters["balance_fetcher"]

    app.state.donation_service = DonationService(
        provider=donation_provider,
        valuations=PROGRAM_VALUATIONS,
        charity_network=CHARITY_NETWORK,
        repository=repos["donation"] if repos else None,
    )
    app.state.pool_service = PoolService(
        donation_service=app.state.donation_service,
        repository=repos["pool"] if repos else None,
    )
    app.state.forum_service = ForumService(repository=repos["forum"] if repos else None)
    app.state.founder_directory = FounderDirectory(repository=repos["founder"] if repos else None)

    # --- Inline routes ---

    @app.get("/health")
    def health():
        """Deep health check — probes DB connectivity when configured."""
        db_status = _probe_database()
        overall = "ok" if db_status in ("ok", "not_configured") else "degraded"
        return {
            "status": overall,
            "version": __version__,
            "dependencies": {
                "database": db_status,
            },
        }

    # --- Error handlers ---

    @app.exception_handler(AuthError)
    async def auth_error_handler(request: Request, exc: AuthError):
        return JSONResponse(status_code=401, content={"detail": str(exc)})

    @app.exception_handler(Exception)
    async def global_error_handler(request: Request, exc: Exception):
        """Global error boundary — structured JSON, never leaks stack traces."""
        import structlog

        logger = get_logger("error")
        # Prefer request_id from structlog context (set by logging middleware),
        # fall back to header, then "unknown"
        ctx = structlog.contextvars.get_contextvars()
        request_id = ctx.get("request_id", request.headers.get("X-Request-Id", "unknown"))
        logger.error(
            "unhandled_exception",
            exc_type=type(exc).__name__,
            exc_message=str(exc),
            path=request.url.path,
            request_id=request_id,
            traceback=traceback.format_exc(),
        )
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "request_id": request_id,
            },
        )

    return app
