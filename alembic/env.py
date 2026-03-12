"""Alembic environment — reads DATABASE_URL from env, runs migrations."""

from __future__ import annotations

import os
from logging.config import fileConfig

from sqlalchemy import create_engine, pool

from alembic import context
from redeemflow.infra.db_models import metadata

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = metadata


def get_url() -> str:
    from redeemflow.infra.database import normalize_database_url

    url = os.environ.get("DATABASE_URL", config.get_main_option("sqlalchemy.url", ""))
    return normalize_database_url(url) if url else ""


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # Support injected connection for in-memory SQLite testing
    connectable = config.attributes.get("connection")
    if connectable is not None:
        context.configure(connection=connectable, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
        return

    url = get_url()
    connectable = create_engine(url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
