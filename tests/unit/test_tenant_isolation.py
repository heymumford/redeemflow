"""Tests for multi-tenancy: tenant model, auth extraction, row-level isolation."""

from __future__ import annotations

import pytest

from redeemflow.identity.models import User
from redeemflow.identity.tenant import (
    DEFAULT_TENANT_ID,
    Tenant,
    TenantMembership,
    TenantRole,
    TenantType,
)


class TestTenantModel:
    def test_create_individual_tenant(self):
        t = Tenant(id=DEFAULT_TENANT_ID, name="Individual", type=TenantType.INDIVIDUAL)
        assert t.id == DEFAULT_TENANT_ID
        assert t.type == TenantType.INDIVIDUAL
        assert t.is_individual

    def test_create_commercial_tenant(self):
        t = Tenant(id="tenant-acme", name="Acme Corp", type=TenantType.COMMERCIAL)
        assert t.type == TenantType.COMMERCIAL
        assert not t.is_individual

    def test_tenant_is_frozen(self):
        t = Tenant(id="t1", name="Test", type=TenantType.INDIVIDUAL)
        with pytest.raises(AttributeError):
            t.id = "changed"


class TestTenantMembership:
    def test_create_membership(self):
        m = TenantMembership(user_id="auth0|eric", tenant_id="tenant-acme", role=TenantRole.OWNER)
        assert m.user_id == "auth0|eric"
        assert m.tenant_id == "tenant-acme"
        assert m.role == TenantRole.OWNER

    def test_default_role_is_member(self):
        m = TenantMembership(user_id="auth0|steve", tenant_id=DEFAULT_TENANT_ID)
        assert m.role == TenantRole.MEMBER

    def test_membership_is_frozen(self):
        m = TenantMembership(user_id="u1", tenant_id="t1")
        with pytest.raises(AttributeError):
            m.role = TenantRole.ADMIN


class TestUserTenantId:
    def test_user_has_tenant_id(self):
        u = User(id="auth0|eric", email="e@e.com", tenant_id="tenant-acme")
        assert u.tenant_id == "tenant-acme"

    def test_user_default_tenant_is_individual(self):
        u = User(id="auth0|eric", email="e@e.com")
        assert u.tenant_id == DEFAULT_TENANT_ID

    def test_user_equality_unchanged(self):
        u1 = User(id="auth0|eric", email="e@e.com", tenant_id="t1")
        u2 = User(id="auth0|eric", email="e@e.com", tenant_id="t2")
        assert u1 == u2  # equality is by id only


class TestTenantContext:
    def test_set_and_get_tenant(self):
        from redeemflow.identity.tenant import get_current_tenant_id, set_current_tenant_id

        set_current_tenant_id("tenant-acme")
        assert get_current_tenant_id() == "tenant-acme"
        # Reset
        set_current_tenant_id(DEFAULT_TENANT_ID)
        assert get_current_tenant_id() == DEFAULT_TENANT_ID

    def test_default_tenant_when_unset(self):
        from redeemflow.identity.tenant import get_current_tenant_id

        # In a fresh context, should return default
        assert get_current_tenant_id() == DEFAULT_TENANT_ID
