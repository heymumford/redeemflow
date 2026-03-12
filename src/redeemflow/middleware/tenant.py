"""Tenant middleware — sets the tenant context per-request from JWT.

Extracts tenant_id from the authenticated user and binds it to the
contextvar so repositories can filter by tenant without explicit threading.
Also binds tenant_id to structlog context for observability.
"""

from __future__ import annotations

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from redeemflow.identity.auth import AuthError, get_current_user
from redeemflow.identity.tenant import DEFAULT_TENANT_ID, set_current_tenant_id

logger = structlog.get_logger()

# Paths that don't require tenant context (no auth).
_PUBLIC_PATHS = frozenset(
    {
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
    }
)


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        if path in _PUBLIC_PATHS or request.method == "OPTIONS":
            set_current_tenant_id(DEFAULT_TENANT_ID)
            return await call_next(request)

        try:
            user = get_current_user(request)
            tenant_id = user.tenant_id
        except AuthError:
            # No valid auth — default tenant (routes will still enforce auth)
            tenant_id = DEFAULT_TENANT_ID
        except Exception:
            logger.exception("unexpected_error_determining_tenant")
            raise

        set_current_tenant_id(tenant_id)
        structlog.contextvars.bind_contextvars(tenant_id=tenant_id)

        try:
            return await call_next(request)
        finally:
            set_current_tenant_id(DEFAULT_TENANT_ID)
            structlog.contextvars.unbind_contextvars("tenant_id")
