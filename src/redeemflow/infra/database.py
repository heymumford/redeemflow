"""Database connection management — opt-in via DATABASE_URL.

If DATABASE_URL is not set, no engine is created and the app runs in-memory.
"""

from __future__ import annotations

import os

from sqlalchemy import Engine
from sqlalchemy import create_engine as sa_create_engine
from sqlalchemy.orm import Session, sessionmaker


def normalize_database_url(url: str) -> str:
    """Normalize DB URL for SQLAlchemy 2.x + psycopg v3 driver."""
    # Fly Postgres sets postgres:// but SQLAlchemy 2.x requires postgresql://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    # Force psycopg v3 driver (not psycopg2)
    if url.startswith("postgresql://") and "+psycopg" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def get_database_url() -> str | None:
    url = os.environ.get("DATABASE_URL")
    if not url:
        return None
    return normalize_database_url(url)


def create_engine(url: str) -> Engine:
    return sa_create_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=10)


def get_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)
