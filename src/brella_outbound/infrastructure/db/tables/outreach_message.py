"""Outreach message table definition."""

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    func,
)

from brella_outbound.domain.models.campaign import OutreachStatus
from brella_outbound.infrastructure.db.tables.metadata import metadata

outreach_message_table = Table(
    "outreach_messages",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column(
        "campaign_id",
        Integer,
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column(
        "attendee_id",
        Integer,
        ForeignKey("attendees.id"),
        nullable=False,
        index=True,
    ),
    Column("attendee_name", String(500), nullable=False),
    Column("message", Text, nullable=False),
    Column(
        "status",
        Enum(OutreachStatus, name="outreach_status"),
        nullable=False,
        default=OutreachStatus.PENDING,
    ),
    Column("error", Text),
    Column("sent_at", DateTime),
    Column("created_at", DateTime, nullable=False, server_default=func.now()),
)
