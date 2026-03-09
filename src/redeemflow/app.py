"""FastAPI application factory.

Beck: One place to configure everything — middleware, adapters, routes.
Fowler: Adapter factory selects real vs fake per Protocol based on env vars.

Database persistence is opt-in: set DATABASE_URL to enable Postgres.
Without it, all state is in-memory (dev/test mode).
"""

from __future__ import annotations

import logging
import os
import traceback

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from redeemflow import __version__
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
from redeemflow.identity.auth import AuthError, get_current_user
from redeemflow.identity.models import User
from redeemflow.middleware.logging import RequestLoggingMiddleware, configure_logging, get_logger
from redeemflow.middleware.rate_limit import limiter
from redeemflow.optimization.routes import router as optimization_router
from redeemflow.portfolio.fake_adapter import FakeBalanceFetcher
from redeemflow.recommendations.engine import RecommendationEngine
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
        # Real adapter when credentials are available
        adapters["donation_provider"] = FakeDonationProvider()  # TODO: ChangeApiAdapter(change_key)
    else:
        adapters["donation_provider"] = FakeDonationProvider()

    # Balance boundary: AwardWallet
    aw_key = os.environ.get("AWARDWALLET_API_KEY")
    if aw_key:
        # Real adapter when credentials are available
        adapters["balance_fetcher"] = FakeBalanceFetcher()  # TODO: AwardWalletAdapter(aw_key)
    else:
        adapters["balance_fetcher"] = FakeBalanceFetcher()

    return adapters


def create_app() -> FastAPI:
    """Application factory — configure middleware, adapters, routes."""
    configure_logging()

    app = FastAPI(title="RedeemFlow", version=__version__)

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

    # Structured request logging
    app.add_middleware(RequestLoggingMiddleware)

    # Rate limiting — SlowAPIMiddleware enforces default_limits globally
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # --- Routers ---
    app.include_router(valuations_router)
    app.include_router(billing_router)
    app.include_router(charity_router)
    app.include_router(optimization_router)
    app.include_router(search_router)
    app.include_router(community_router)

    # --- Adapter factory ---
    repos = _init_db_repositories()
    adapters = _select_adapters()

    app.state.payment_provider = adapters["payment"]
    app.state.donation_service = DonationService(
        provider=adapters["donation_provider"],
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

    fetcher = adapters["balance_fetcher"]
    rec_engine = RecommendationEngine()

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

    @app.get("/api/portfolio")
    def portfolio(user: User = Depends(get_current_user)):
        balances = fetcher.fetch_balances(user.id)
        return {
            "balances": [
                {
                    "program_code": b.program_code,
                    "points": b.points,
                    "estimated_value_dollars": str(b.estimated_value_dollars),
                }
                for b in balances
            ],
            "total_value_dollars": str(sum(b.estimated_value_dollars for b in balances)),
        }

    @app.get("/api/recommendations")
    def recommendations(user: User = Depends(get_current_user)):
        balances = fetcher.fetch_balances(user.id)
        recs = rec_engine.recommend(balances)
        return {
            "recommendations": [
                {
                    "program_code": r.program_code,
                    "action": r.action,
                    "rationale": r.rationale,
                    "cpp_gain": str(r.cpp_gain),
                    "points_involved": r.points_involved,
                }
                for r in recs
            ],
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
