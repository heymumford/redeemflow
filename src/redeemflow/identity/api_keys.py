"""API key management — create, list, and revoke keys for programmatic access.

Beck: API keys are facts — created, active, or revoked.
Fowler: Value Object for the key, Aggregate for the user's key collection.
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class APIKey:
    """An API key for programmatic access."""

    key_id: str
    name: str
    prefix: str  # First 8 chars for display (e.g., "rf_abc123...")
    key_hash: str  # SHA-256 hash of the full key
    user_id: str
    created_at: str
    expires_at: str = ""
    is_active: bool = True
    last_used_at: str = ""
    scopes: list[str] = field(default_factory=list)


@dataclass
class APIKeyStore:
    """Manages API keys for all users."""

    _keys: dict[str, APIKey] = field(default_factory=dict)  # key_id -> APIKey
    _hash_index: dict[str, str] = field(default_factory=dict)  # key_hash -> key_id
    _counter: int = 0

    def create_key(
        self,
        user_id: str,
        name: str,
        scopes: list[str] | None = None,
        expires_at: str = "",
    ) -> tuple[str, APIKey]:
        """Create a new API key. Returns (raw_key, APIKey).

        The raw key is only returned once — it cannot be recovered later.
        """
        self._counter += 1
        key_id = f"key-{self._counter}"

        # Generate a secure random key with identifiable prefix
        raw_key = f"rf_{secrets.token_urlsafe(32)}"
        prefix = raw_key[:11]  # "rf_" + first 8 chars
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        api_key = APIKey(
            key_id=key_id,
            name=name,
            prefix=prefix,
            key_hash=key_hash,
            user_id=user_id,
            created_at=datetime.now(UTC).isoformat(),
            expires_at=expires_at,
            is_active=True,
            scopes=scopes or ["read"],
        )

        self._keys[key_id] = api_key
        self._hash_index[key_hash] = key_id
        return raw_key, api_key

    def list_keys(self, user_id: str) -> list[APIKey]:
        """List all keys for a user (active and revoked)."""
        return [k for k in self._keys.values() if k.user_id == user_id]

    def get_key(self, key_id: str) -> APIKey | None:
        """Get a key by its ID."""
        return self._keys.get(key_id)

    def revoke_key(self, key_id: str, user_id: str) -> APIKey | None:
        """Revoke a key. Returns None if key not found or doesn't belong to user."""
        key = self._keys.get(key_id)
        if key is None or key.user_id != user_id:
            return None

        revoked = APIKey(
            key_id=key.key_id,
            name=key.name,
            prefix=key.prefix,
            key_hash=key.key_hash,
            user_id=key.user_id,
            created_at=key.created_at,
            expires_at=key.expires_at,
            is_active=False,
            last_used_at=key.last_used_at,
            scopes=key.scopes,
        )
        self._keys[key_id] = revoked
        if key.key_hash in self._hash_index:
            del self._hash_index[key.key_hash]
        return revoked

    def validate_key(self, raw_key: str) -> APIKey | None:
        """Validate a raw API key. Returns the APIKey if valid and active."""
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_id = self._hash_index.get(key_hash)
        if key_id is None:
            return None

        key = self._keys.get(key_id)
        if key is None or not key.is_active:
            return None

        # Check expiration
        if key.expires_at:
            try:
                exp = datetime.fromisoformat(key.expires_at)
                if datetime.now(UTC) > exp:
                    return None
            except ValueError:
                pass

        # Update last_used_at
        updated = APIKey(
            key_id=key.key_id,
            name=key.name,
            prefix=key.prefix,
            key_hash=key.key_hash,
            user_id=key.user_id,
            created_at=key.created_at,
            expires_at=key.expires_at,
            is_active=key.is_active,
            last_used_at=datetime.now(UTC).isoformat(),
            scopes=key.scopes,
        )
        self._keys[key_id] = updated
        return updated

    def active_count(self, user_id: str) -> int:
        """Count active keys for a user."""
        return sum(1 for k in self._keys.values() if k.user_id == user_id and k.is_active)


# Singleton
_API_KEY_STORE = APIKeyStore()


def get_api_key_store() -> APIKeyStore:
    return _API_KEY_STORE


def reset_api_key_store() -> None:
    """Reset the store — for testing only."""
    global _API_KEY_STORE
    _API_KEY_STORE = APIKeyStore()
