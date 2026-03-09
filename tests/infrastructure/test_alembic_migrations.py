"""Alembic migration roundtrip — upgrade, verify, downgrade, verify, upgrade again.

Uses SQLite in-memory to validate that the migration script creates and
removes all 9 expected tables without relying on a running Postgres instance.
"""

from __future__ import annotations

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from alembic import command

EXPECTED_TABLES = frozenset(
    {
        "subscriptions",
        "donations",
        "community_pools",
        "pledges",
        "forum_posts",
        "forum_replies",
        "founder_profiles",
        "auto_donate_rules",
        "charity_alignments",
    }
)


def _make_alembic_config(url: str) -> Config:
    """Build an Alembic Config pointing at the repo's migration scripts."""
    cfg = Config()
    cfg.set_main_option("script_location", "alembic")
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


def _get_table_names(engine) -> set[str]:
    """Return the set of user table names in the database (excludes alembic_version)."""
    insp = inspect(engine)
    return {t for t in insp.get_table_names() if t != "alembic_version"}


@pytest.mark.infrastructure
class TestAlembicMigrationRoundtrip:
    def test_upgrade_creates_all_tables(self):
        engine = create_engine("sqlite://", echo=False)
        cfg = _make_alembic_config("sqlite://")

        # Alembic needs a real connection for SQLite in-memory
        with engine.connect() as connection:
            cfg.attributes["connection"] = connection
            command.upgrade(cfg, "head")
            tables = _get_table_names(engine)

        assert tables >= EXPECTED_TABLES, f"Missing tables: {EXPECTED_TABLES - tables}"
        engine.dispose()

    def test_downgrade_removes_all_tables(self):
        engine = create_engine("sqlite://", echo=False)
        cfg = _make_alembic_config("sqlite://")

        with engine.connect() as connection:
            cfg.attributes["connection"] = connection
            command.upgrade(cfg, "head")
            command.downgrade(cfg, "base")
            tables = _get_table_names(engine)

        assert len(tables) == 0, f"Tables remain after downgrade: {tables}"
        engine.dispose()

    def test_upgrade_downgrade_upgrade_idempotent(self):
        engine = create_engine("sqlite://", echo=False)
        cfg = _make_alembic_config("sqlite://")

        with engine.connect() as connection:
            cfg.attributes["connection"] = connection
            command.upgrade(cfg, "head")
            command.downgrade(cfg, "base")
            command.upgrade(cfg, "head")
            tables = _get_table_names(engine)

        assert tables >= EXPECTED_TABLES, f"Missing tables after re-upgrade: {EXPECTED_TABLES - tables}"
        engine.dispose()
