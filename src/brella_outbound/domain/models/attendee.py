"""Attendee and reference data domain models."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class InterestCategory:
    """Top-level interest category (e.g. Role, Field of Study, Technology)."""

    id: int
    name: str
    event_id: int
    position: int = 0


@dataclass
class Interest:
    """A selectable interest within a category."""

    id: int
    name: str
    category_id: int
    position: int = 0


@dataclass
class IntentPair:
    """Networking intent pair (e.g. Networking, Recruitment, Investment)."""

    id: int
    title: str
    slug: str
    position: int = 0


@dataclass
class Intent:
    """Individual intent within a pair."""

    id: int
    selection_label: str
    match_label: str
    profile_label: str
    pair_id: int | None = None
    position: int = 0


@dataclass
class Persona:
    """Attendee persona (e.g. Startup (Founder), Investor, Student)."""

    id: int
    name: str
    position: int = 0


@dataclass
class Function:
    """Attendee function/role (e.g. Founder / Co-Founder, CTO)."""

    id: int
    name: str
    position: int = 0


@dataclass
class Industry:
    """Attendee industry (e.g. Enterprise Software & SaaS)."""

    id: int
    name: str
    position: int = 0


@dataclass
class AttendeeGroup:
    """Event attendee group (e.g. Startups, Hackers, Team)."""

    id: int
    name: str
    attendance_type: str = "in_person"
    allows_networking: bool = True
    attendees_count: int = 0


@dataclass
class SelectedInterest:
    """Junction: links an attendee to an interest with an intent."""

    id: int
    attendee_id: int
    interest_id: int
    intent_id: int


@dataclass
class Attendee:
    """Represents a Brella event attendee."""

    id: int
    user_id: int
    event_slug: str
    first_name: str
    last_name: str
    company_title: str | None = None
    company_name: str | None = None
    pitch: str | None = None
    status: str = "joined"
    persona_id: int | None = None
    function_id: int | None = None
    industry_id: int | None = None
    group_id: int | None = None
    image_url: str | None = None
    cover_photo_url: str | None = None
    linkedin: str | None = None
    website: str | None = None
    joined_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    # Hydrated from included data (not persisted directly)
    persona: Persona | None = field(default=None, repr=False)
    function: Function | None = field(default=None, repr=False)
    industry: Industry | None = field(default=None, repr=False)
    group: AttendeeGroup | None = field(default=None, repr=False)
    selected_interests: list[SelectedInterest] = field(
        default_factory=list,
        repr=False,
    )

    # Resolved interest names (convenience, populated during hydration)
    interest_names: list[str] = field(default_factory=list, repr=False)

    @property
    def full_name(self) -> str:
        """Return the attendee's full name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def display_info(self) -> str:
        """Return a concise display string."""
        parts = [self.full_name]
        if self.company_title and self.company_name:
            parts.append(f"{self.company_title} @ {self.company_name}")
        elif self.company_name:
            parts.append(self.company_name)
        return " — ".join(parts)

    @property
    def persona_name(self) -> str | None:
        """Return resolved persona name."""
        return self.persona.name if self.persona else None

    @property
    def industry_name(self) -> str | None:
        """Return resolved industry name."""
        return self.industry.name if self.industry else None

    @property
    def function_name(self) -> str | None:
        """Return resolved function name."""
        return self.function.name if self.function else None
