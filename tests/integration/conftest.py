"""Integration test conftest — in-memory SQLite for repository tests."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from redeemflow.infra.db_models import metadata


@pytest.fixture()
def db_engine():
    """Create an in-memory SQLite engine with all tables."""
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def session_factory(db_engine):
    """Session factory bound to the in-memory SQLite engine."""
    return sessionmaker(bind=db_engine, expire_on_commit=False)
