"""FastAPI application factory — walking skeleton."""

from __future__ import annotations

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse

from redeemflow import __version__
from redeemflow.billing.routes import router as billing_router
from redeemflow.billing.stripe_adapter import FakePaymentProvider
from redeemflow.charity.donation_flow import DonationService, FakeDonationProvider
from redeemflow.charity.routes import router as charity_router
from redeemflow.charity.seed_data import CHARITY_NETWORK
from redeemflow.identity.auth import AuthError, get_current_user
from redeemflow.identity.models import User
from redeemflow.optimization.routes import router as optimization_router
from redeemflow.portfolio.fake_adapter import FakeBalanceFetcher
from redeemflow.recommendations.engine import RecommendationEngine
from redeemflow.search.routes import router as search_router
from redeemflow.valuations.routes import router as valuations_router
from redeemflow.valuations.seed_data import PROGRAM_VALUATIONS


def create_app() -> FastAPI:
    app = FastAPI(title="RedeemFlow", version=__version__)
    app.include_router(valuations_router)
    app.include_router(billing_router)
    app.include_router(charity_router)
    app.include_router(optimization_router)
    app.include_router(search_router)
    app.state.payment_provider = FakePaymentProvider()
    app.state.donation_service = DonationService(
        provider=FakeDonationProvider(),
        valuations=PROGRAM_VALUATIONS,
        charity_network=CHARITY_NETWORK,
    )
    fetcher = FakeBalanceFetcher()
    engine = RecommendationEngine()

    @app.get("/health")
    def health():
        return {"status": "ok", "version": __version__}

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
        recs = engine.recommend(balances)
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

    @app.exception_handler(AuthError)
    async def auth_error_handler(request: Request, exc: AuthError):
        return JSONResponse(status_code=401, content={"detail": str(exc)})

    return app
