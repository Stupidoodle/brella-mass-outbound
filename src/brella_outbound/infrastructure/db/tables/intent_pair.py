"""Intent pair table definition."""

from sqlalchemy import Column, Integer, String, Table

from brella_outbound.infrastructure.db.tables.metadata import metadata

intent_pair_table = Table(
    "intent_pairs",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("title", String(255), nullable=False),
    Column("slug", String(255), nullable=False),
    Column("position", Integer, nullable=False, default=0),
)
