"""Campaign and outreach message domain models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class OutreachStatus(Enum):
    """Status of an individual outreach message."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class OutreachMessage:
    """A single outreach message to an attendee."""

    attendee_id: int
    attendee_name: str
    message: str
    id: int | None = None
    campaign_id: int | None = None
    status: OutreachStatus = OutreachStatus.PENDING
    error: str | None = None
    sent_at: datetime | None = None
    created_at: datetime | None = None


@dataclass
class Campaign:
    """An outreach campaign targeting event attendees."""

    event_slug: str
    id: int | None = None
    messages: list[OutreachMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def sent_count(self) -> int:
        """Return count of successfully sent messages."""
        return sum(1 for m in self.messages if m.status == OutreachStatus.SENT)

    @property
    def failed_count(self) -> int:
        """Return count of failed messages."""
        return sum(1 for m in self.messages if m.status == OutreachStatus.FAILED)

    @property
    def pending_count(self) -> int:
        """Return count of pending messages."""
        return sum(1 for m in self.messages if m.status == OutreachStatus.PENDING)
