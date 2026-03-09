"""Identity domain — JWT verification and auth dependency."""

from __future__ import annotations

from fastapi import Request

from redeemflow.identity.models import User


class AuthError(Exception):
    pass


# Test tokens for walking skeleton — replaced by real Auth0 JWT verification in Sprint 2.
_TEST_USERS = {
    "test-token-eric": User(id="auth0|eric", email="ericmumford@gmail.com", name="Eric"),
    "test-token-steve": User(id="auth0|steve", email="steve@example.com", name="Steve"),
}


def verify_token(token: str | None) -> User:
    if not token:
        raise AuthError("Missing authentication token")

    # Walking skeleton: accept test tokens.
    user = _TEST_USERS.get(token)
    if user:
        return user

    # Reject anything that doesn't look like a JWT (3 dot-separated parts).
    parts = token.split(".")
    if len(parts) != 3:
        raise AuthError("Malformed token")

    raise AuthError("Invalid token")


def get_current_user(request: Request) -> User:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise AuthError("Missing or invalid Authorization header")

    token = auth_header[len("Bearer ") :]
    return verify_token(token)
