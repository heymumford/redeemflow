"""Multi-tenancy domain — Tenant, TenantMembership, and tenant context.

Individual users share a default tenant. Commercial accounts get isolated tenants
with separate billing, point pools, and API rate limits.

Tenant context uses contextvars so middleware can set the tenant per-request
and repositories can read it without explicit parameter threading.
"""

from __future__ import annotations

from contextvars import ContextVar, Token
from dataclasses import dataclass
from enum import StrEnum

DEFAULT_TENANT_ID = "tenant-individual"


class TenantType(StrEnum):
    INDIVIDUAL = "individual"
    COMMERCIAL = "commercial"


class TenantRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


@dataclass(frozen=True)
class Tenant:
    id: str
    name: str
    type: TenantType

    @property
    def is_individual(self) -> bool:
        return self.type == TenantType.INDIVIDUAL


@dataclass(frozen=True)
class TenantMembership:
    user_id: str
    tenant_id: str
    role: TenantRole = TenantRole.MEMBER


# --- Tenant context (per-request via middleware) ---

_current_tenant_id: ContextVar[str] = ContextVar("current_tenant_id", default=DEFAULT_TENANT_ID)


def get_current_tenant_id() -> str:
    return _current_tenant_id.get()


def set_current_tenant_id(tenant_id: str) -> Token[str]:
    return _current_tenant_id.set(tenant_id)
