"""Alembic env.py — reads DB URL from Settings, not alembic.ini."""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from brella_outbound.core.config import get_settings
from brella_outbound.infrastructure.db.mappers import start_mappers
from brella_outbound.infrastructure.db.tables.metadata import metadata

# Import all table modules so metadata picks them up
from brella_outbound.infrastructure.db.tables import (  # noqa: F401
    attendee,
    attendee_group,
    campaign,
    event,
    function,
    industry,
    intent,
    intent_pair,
    interest,
    interest_category,
    outreach_message,
    persona,
    selected_interest,
)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Configure mappers so relationships are known
start_mappers()

# Override sqlalchemy.url from Settings
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
