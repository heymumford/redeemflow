"""Slice 2: Identity domain — User model and JWT verification."""

from __future__ import annotations

import pytest

from redeemflow.identity.models import User
from redeemflow.identity.auth import verify_token, AuthError


class TestUserModel:
    def test_user_is_frozen(self):
        user = User(id="auth0|abc123", email="eric@example.com", name="Eric")
        with pytest.raises(AttributeError):
            user.id = "changed"

    def test_user_requires_id_and_email(self):
        user = User(id="auth0|abc123", email="eric@example.com")
        assert user.id == "auth0|abc123"
        assert user.email == "eric@example.com"
        assert user.name is None

    def test_user_equality_by_id(self):
        a = User(id="auth0|abc123", email="eric@example.com", name="Eric")
        b = User(id="auth0|abc123", email="different@example.com", name="Other")
        assert a == b

    def test_users_with_different_ids_not_equal(self):
        a = User(id="auth0|abc123", email="same@example.com")
        b = User(id="auth0|def456", email="same@example.com")
        assert a != b


class TestAuthVerification:
    def test_missing_token_raises_auth_error(self):
        with pytest.raises(AuthError):
            verify_token(None)

    def test_empty_token_raises_auth_error(self):
        with pytest.raises(AuthError):
            verify_token("")

    def test_malformed_token_raises_auth_error(self):
        with pytest.raises(AuthError):
            verify_token("not.a.valid.jwt")
