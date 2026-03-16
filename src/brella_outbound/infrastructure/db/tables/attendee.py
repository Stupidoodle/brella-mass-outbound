"""Attendee table definition."""

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    func,
)

from brella_outbound.infrastructure.db.tables.metadata import metadata

attendee_table = Table(
    "attendees",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, nullable=False, index=True),
    Column("event_slug", String(255), nullable=False, index=True),
    Column("first_name", String(255), nullable=False),
    Column("last_name", String(255), nullable=False),
    Column("company_title", String(500)),
    Column("company_name", String(500)),
    Column("pitch", Text),
    Column("status", String(50), nullable=False, default="joined"),
    Column("persona_id", Integer, ForeignKey("personas.id")),
    Column("function_id", Integer, ForeignKey("functions.id")),
    Column("industry_id", Integer, ForeignKey("industries.id")),
    Column("group_id", Integer, ForeignKey("attendee_groups.id")),
    Column("image_url", String(1000)),
    Column("cover_photo_url", String(1000)),
    Column("linkedin", String(1000)),
    Column("website", String(1000)),
    Column("joined_at", DateTime),
    Column("created_at", DateTime, nullable=False, server_default=func.now()),
    Column("updated_at", DateTime, onupdate=func.now()),
)
