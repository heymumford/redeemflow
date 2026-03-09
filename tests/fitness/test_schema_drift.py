"""Schema drift detection — db_models.py metadata vs Alembic migration.

Compares the canonical schema (defined in db_models.py MetaData) against
what the Alembic migration actually creates in SQLite. Any table or column
present in one but not the other is a drift failure.
"""

from __future__ import annotations

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from alembic import command
from redeemflow.infra.db_models import metadata as model_metadata


def _make_alembic_config(url: str) -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", "alembic")
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


def _get_migration_schema(engine) -> dict[str, set[str]]:
    """Run migration and return {table_name: {column_names}} from the live DB."""
    cfg = _make_alembic_config("sqlite://")
    with engine.connect() as connection:
        cfg.attributes["connection"] = connection
        command.upgrade(cfg, "head")

    insp = inspect(engine)
    schema: dict[str, set[str]] = {}
    for table_name in insp.get_table_names():
        if table_name == "alembic_version":
            continue
        columns = {col["name"] for col in insp.get_columns(table_name)}
        schema[table_name] = columns
    return schema


def _get_model_schema() -> dict[str, set[str]]:
    """Extract {table_name: {column_names}} from db_models.py MetaData."""
    schema: dict[str, set[str]] = {}
    for table in model_metadata.sorted_tables:
        schema[table.name] = {col.name for col in table.columns}
    return schema


@pytest.mark.fitness
class TestSchemaDrift:
    def test_no_tables_missing_from_migration(self):
        """Every table in db_models.py must exist after migration."""
        engine = create_engine("sqlite://", echo=False)
        migration_schema = _get_migration_schema(engine)
        model_schema = _get_model_schema()
        engine.dispose()

        missing = set(model_schema.keys()) - set(migration_schema.keys())
        assert not missing, f"Tables in db_models.py but not in migration: {missing}"

    def test_no_extra_tables_in_migration(self):
        """Migration must not create tables absent from db_models.py."""
        engine = create_engine("sqlite://", echo=False)
        migration_schema = _get_migration_schema(engine)
        model_schema = _get_model_schema()
        engine.dispose()

        extra = set(migration_schema.keys()) - set(model_schema.keys())
        assert not extra, f"Tables in migration but not in db_models.py: {extra}"

    def test_no_columns_missing_from_migration(self):
        """Every column in db_models.py must exist in the migrated table."""
        engine = create_engine("sqlite://", echo=False)
        migration_schema = _get_migration_schema(engine)
        model_schema = _get_model_schema()
        engine.dispose()

        drift: list[str] = []
        for table_name, model_cols in model_schema.items():
            migration_cols = migration_schema.get(table_name, set())
            missing_cols = model_cols - migration_cols
            if missing_cols:
                drift.append(f"{table_name}: missing columns {missing_cols}")

        assert not drift, "Column drift detected:\n" + "\n".join(drift)

    def test_no_extra_columns_in_migration(self):
        """Migration must not add columns absent from db_models.py."""
        engine = create_engine("sqlite://", echo=False)
        migration_schema = _get_migration_schema(engine)
        model_schema = _get_model_schema()
        engine.dispose()

        drift: list[str] = []
        for table_name, migration_cols in migration_schema.items():
            model_cols = model_schema.get(table_name, set())
            extra_cols = migration_cols - model_cols
            if extra_cols:
                drift.append(f"{table_name}: extra columns {extra_cols}")

        assert not drift, "Extra column drift detected:\n" + "\n".join(drift)
