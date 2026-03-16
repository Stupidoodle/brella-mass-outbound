"""Interest category table definition."""

from sqlalchemy import Column, ForeignKey, Integer, String, Table

from brella_outbound.infrastructure.db.tables.metadata import metadata

interest_category_table = Table(
    "interest_categories",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(255), nullable=False),
    Column("event_id", Integer, ForeignKey("events.id"), nullable=False, index=True),
    Column("position", Integer, nullable=False, default=0),
)
