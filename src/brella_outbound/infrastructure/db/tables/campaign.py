"""Campaign table definition."""

from sqlalchemy import Column, DateTime, Integer, String, Table, func

from brella_outbound.infrastructure.db.tables.metadata import metadata

campaign_table = Table(
    "campaigns",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("event_slug", String(255), nullable=False, index=True),
    Column("created_at", DateTime, nullable=False, server_default=func.now()),
)
