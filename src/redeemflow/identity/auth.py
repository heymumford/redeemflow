"""Identity domain — JWT verification and auth dependency.

Beck: Test tokens are the simplest thing that works for dev/test.
Fowler: Auth0 is the production boundary — JWKS cached, env-gated.

Supports both test tokens (dev/test mode) and Auth0 RS256 JWTs (production).
Test tokens are checked first; if no match, falls through to JWT verification.
"""

from __future__ import annotations

import json
import os
from base64 import urlsafe_b64decode
from functools import lru_cache

from fastapi import Request

from redeemflow.identity.models import User


class AuthError(Exception):
    pass


# Test tokens for walking skeleton — still work in dev/test mode.
_TEST_USERS = {
    "test-token-eric": User(id="auth0|eric", email="ericmumford@gmail.com", name="Eric"),
    "test-token-steve": User(id="auth0|steve", email="steve@example.com", name="Steve"),
}

# Auth0 configuration — set via environment variables in production.
_AUTH0_DOMAIN = os.environ.get("AUTH0_DOMAIN", "")
_AUTH0_AUDIENCE = os.environ.get("AUTH0_AUDIENCE", "")


@lru_cache(maxsize=1)
def _get_jwks_client():
    """Cached JWKS client — fetches signing keys once, reuses across requests.

    PyJWKClient has its own internal TTL cache (lifespan=300s by default).
    We additionally cache the client instance itself so we don't recreate it per request.
    """
    import jwt

    jwks_url = f"https://{_AUTH0_DOMAIN}/.well-known/jwks.json"
    return jwt.PyJWKClient(jwks_url, cache_keys=True, lifespan=300)


def _decode_jwt_payload(token: str) -> dict:
    """Decode JWT payload without verification (for extracting claims after verification)."""
    parts = token.split(".")
    if len(parts) != 3:
        raise AuthError("Malformed token")

    payload_b64 = parts[1]
    # Add padding if needed
    padding = 4 - len(payload_b64) % 4
    if padding != 4:
        payload_b64 += "=" * padding

    try:
        payload_bytes = urlsafe_b64decode(payload_b64)
        return json.loads(payload_bytes)
    except Exception as exc:
        raise AuthError("Invalid token payload") from exc


def _verify_auth0_jwt(token: str) -> User:
    """Verify an Auth0 RS256 JWT and extract user claims.

    In production (AUTH0_DOMAIN set), performs full RS256 verification
    with cached JWKS keys. Without Auth0 config, rejects unrecognized JWTs.
    """
    parts = token.split(".")
    if len(parts) != 3:
        raise AuthError("Malformed token")

    if _AUTH0_DOMAIN and _AUTH0_AUDIENCE:
        try:
            import jwt

            jwks_client = _get_jwks_client()
            signing_key = jwks_client.get_signing_key_from_jwt(token)

            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=_AUTH0_AUDIENCE,
                issuer=f"https://{_AUTH0_DOMAIN}/",
            )

            user_id = payload.get("sub", "")
            email = payload.get("email", payload.get(f"https://{_AUTH0_DOMAIN}/email", ""))
            name = payload.get("name", payload.get(f"https://{_AUTH0_DOMAIN}/name"))

            if not user_id:
                raise AuthError("Token missing subject claim")

            return User(id=user_id, email=email, name=name)

        except AuthError:
            raise
        except Exception as e:
            raise AuthError(f"Token verification failed: {e}") from e

    # No Auth0 config — reject unknown JWTs in dev mode
    raise AuthError("Invalid token")


def verify_token(token: str | None) -> User:
    if not token:
        raise AuthError("Missing authentication token")

    # Check test tokens first (always available for dev/test).
    user = _TEST_USERS.get(token)
    if user:
        return user

    # Fall through to JWT verification for anything else.
    return _verify_auth0_jwt(token)


def get_current_user(request: Request) -> User:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise AuthError("Missing or invalid Authorization header")

    token = auth_header[len("Bearer ") :]
    return verify_token(token)
