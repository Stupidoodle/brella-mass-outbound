"""Function (role) table definition."""

from sqlalchemy import Column, Integer, String, Table

from brella_outbound.infrastructure.db.tables.metadata import metadata

function_table = Table(
    "functions",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(255), nullable=False),
    Column("position", Integer, nullable=False, default=0),
)
