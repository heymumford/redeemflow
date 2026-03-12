"""Identity domain — User value object."""

from __future__ import annotations

from dataclasses import dataclass

from redeemflow.identity.tenant import DEFAULT_TENANT_ID


@dataclass(frozen=True, eq=False)
class User:
    id: str
    email: str
    name: str | None = None
    tier: str = "free"  # free, premium, pro — looked up from billing on auth
    tenant_id: str = DEFAULT_TENANT_ID

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
