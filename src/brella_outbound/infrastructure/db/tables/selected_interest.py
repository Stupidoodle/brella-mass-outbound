"""Selected interest junction table definition (3NF).

Links an attendee to a specific interest with a specific intent.
This is the core matchmaking data — how Brella knows what each attendee
is interested in and what they want to do about it.
"""

from sqlalchemy import Column, ForeignKey, Integer, Table

from brella_outbound.infrastructure.db.tables.metadata import metadata

selected_interest_table = Table(
    "selected_interests",
    metadata,
    Column("id", Integer, primary_key=True),
    Column(
        "attendee_id",
        Integer,
        ForeignKey("attendees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column(
        "interest_id",
        Integer,
        ForeignKey("interests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column(
        "intent_id",
        Integer,
        ForeignKey("intents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
)
