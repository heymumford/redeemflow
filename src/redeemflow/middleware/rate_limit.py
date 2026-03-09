"""Rate limiting — SlowAPI with in-memory backend.

Public endpoints: 60 req/min. Authenticated endpoints: 300 req/min.
Returns 429 with Retry-After header when exceeded.
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

# In-memory rate limiter — sufficient for single-instance Fly.io deployment.
# Swap to redis backend for multi-instance: Limiter(key_func=..., storage_uri="redis://...")
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

# Higher limit for authenticated endpoints — applied per-route via @limiter.limit()
AUTHENTICATED_LIMIT = "300/minute"
