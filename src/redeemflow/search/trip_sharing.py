"""Trip sharing — shareable links with permissions and view tracking.

Beck: A share is a fact — the link exists or it doesn't.
Fowler: Value Object for the share token, Aggregate for sharing state.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


class SharePermission(str, Enum):
    VIEW = "view"
    EDIT = "edit"


@dataclass(frozen=True)
class ShareLink:
    """A shareable link to a trip."""

    share_id: str
    trip_id: str
    owner_id: str
    token: str
    permission: SharePermission
    created_at: str
    expires_at: str = ""
    is_active: bool = True
    view_count: int = 0
    last_viewed_at: str = ""


@dataclass
class TripShareStore:
    """Manages trip sharing."""

    _shares: dict[str, ShareLink] = field(default_factory=dict)  # share_id -> ShareLink
    _token_index: dict[str, str] = field(default_factory=dict)  # token -> share_id
    _counter: int = 0

    def create_share(
        self,
        trip_id: str,
        owner_id: str,
        permission: SharePermission = SharePermission.VIEW,
        expires_at: str = "",
    ) -> ShareLink:
        """Create a shareable link for a trip."""
        self._counter += 1
        share_id = f"share-{self._counter}"
        token = secrets.token_urlsafe(16)

        link = ShareLink(
            share_id=share_id,
            trip_id=trip_id,
            owner_id=owner_id,
            token=token,
            permission=permission,
            created_at=datetime.now(UTC).isoformat(),
            expires_at=expires_at,
            is_active=True,
        )
        self._shares[share_id] = link
        self._token_index[token] = share_id
        return link

    def get_by_token(self, token: str) -> ShareLink | None:
        """Look up a share by its token."""
        share_id = self._token_index.get(token)
        if share_id is None:
            return None
        share = self._shares.get(share_id)
        if share is None or not share.is_active:
            return None

        # Check expiration
        if share.expires_at:
            try:
                exp = datetime.fromisoformat(share.expires_at)
                if datetime.now(UTC) > exp:
                    return None
            except ValueError:
                pass

        return share

    def record_view(self, token: str) -> ShareLink | None:
        """Record a view of a shared trip. Returns updated link."""
        share = self.get_by_token(token)
        if share is None:
            return None

        updated = ShareLink(
            share_id=share.share_id,
            trip_id=share.trip_id,
            owner_id=share.owner_id,
            token=share.token,
            permission=share.permission,
            created_at=share.created_at,
            expires_at=share.expires_at,
            is_active=share.is_active,
            view_count=share.view_count + 1,
            last_viewed_at=datetime.now(UTC).isoformat(),
        )
        self._shares[share.share_id] = updated
        return updated

    def list_shares(self, owner_id: str) -> list[ShareLink]:
        """List all shares for a user."""
        return [s for s in self._shares.values() if s.owner_id == owner_id]

    def revoke_share(self, share_id: str, owner_id: str) -> ShareLink | None:
        """Revoke a share link."""
        share = self._shares.get(share_id)
        if share is None or share.owner_id != owner_id:
            return None

        revoked = ShareLink(
            share_id=share.share_id,
            trip_id=share.trip_id,
            owner_id=share.owner_id,
            token=share.token,
            permission=share.permission,
            created_at=share.created_at,
            expires_at=share.expires_at,
            is_active=False,
            view_count=share.view_count,
            last_viewed_at=share.last_viewed_at,
        )
        self._shares[share_id] = revoked
        if share.token in self._token_index:
            del self._token_index[share.token]
        return revoked

    def sharing_stats(self, owner_id: str) -> dict:
        """Get sharing statistics for a user."""
        user_shares = self.list_shares(owner_id)
        active = [s for s in user_shares if s.is_active]
        total_views = sum(s.view_count for s in user_shares)
        return {
            "total_shares": len(user_shares),
            "active_shares": len(active),
            "total_views": total_views,
            "most_viewed": max(user_shares, key=lambda s: s.view_count).share_id if user_shares else None,
        }


# Singleton
_TRIP_SHARE_STORE = TripShareStore()


def get_trip_share_store() -> TripShareStore:
    return _TRIP_SHARE_STORE


def reset_trip_share_store() -> None:
    global _TRIP_SHARE_STORE
    _TRIP_SHARE_STORE = TripShareStore()
