"""Event table definition."""

from sqlalchemy import Column, DateTime, Integer, String, Table, func

from brella_outbound.infrastructure.db.tables.metadata import metadata

event_table = Table(
    "events",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("slug", String(255), nullable=False, unique=True),
    Column("name", String(500), nullable=False),
    Column("created_at", DateTime, nullable=False, server_default=func.now()),
)
