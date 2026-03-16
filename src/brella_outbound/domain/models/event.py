"""Event domain model."""

from dataclasses import dataclass


@dataclass
class Event:
    """Represents a Brella event."""

    id: int
    slug: str
    name: str
