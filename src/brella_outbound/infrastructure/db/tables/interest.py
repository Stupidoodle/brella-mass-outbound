"""Interest table definition."""

from sqlalchemy import Column, ForeignKey, Integer, String, Table

from brella_outbound.infrastructure.db.tables.metadata import metadata

interest_table = Table(
    "interests",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(255), nullable=False),
    Column(
        "category_id",
        Integer,
        ForeignKey("interest_categories.id"),
        nullable=False,
        index=True,
    ),
    Column("position", Integer, nullable=False, default=0),
)
