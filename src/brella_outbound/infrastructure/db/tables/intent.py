"""Intent table definition."""

from sqlalchemy import Column, ForeignKey, Integer, String, Table

from brella_outbound.infrastructure.db.tables.metadata import metadata

intent_table = Table(
    "intents",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("selection_label", String(255), nullable=False),
    Column("match_label", String(255), nullable=False),
    Column("profile_label", String(255), nullable=False),
    Column(
        "pair_id",
        Integer,
        ForeignKey("intent_pairs.id"),
        nullable=True,
        index=True,
    ),
    Column("position", Integer, nullable=False, default=0),
)
