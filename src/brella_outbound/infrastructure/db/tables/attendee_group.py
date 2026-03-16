"""Attendee group table definition."""

from sqlalchemy import Boolean, Column, Integer, String, Table

from brella_outbound.infrastructure.db.tables.metadata import metadata

attendee_group_table = Table(
    "attendee_groups",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(255), nullable=False),
    Column("attendance_type", String(50), nullable=False, default="in_person"),
    Column("allows_networking", Boolean, nullable=False, default=True),
    Column("attendees_count", Integer, nullable=False, default=0),
)
