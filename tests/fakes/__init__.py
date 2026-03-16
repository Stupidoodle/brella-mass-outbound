"""Fake implementations for testing."""

from typing import Any

from brella_outbound.domain.models.attendee import Attendee
from brella_outbound.domain.models.event import Event
from brella_outbound.domain.ports.brella_api_port import BrellaApiPort
from brella_outbound.domain.ports.logger_port import LoggerPort
from brella_outbound.domain.ports.message_generator_port import MessageGeneratorPort


class FakeLogger(LoggerPort):
    """In-memory logger that captures messages."""

    def __init__(self) -> None:
        self.messages: list[tuple[str, str, dict]] = []

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info."""
        self.messages.append(("info", message, kwargs))

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning."""
        self.messages.append(("warning", message, kwargs))

    def error(
        self,
        message: str,
        exc_info: Exception | None = None,
        **kwargs: Any,
    ) -> None:
        """Log error."""
        self.messages.append(("error", message, kwargs))

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug."""
        self.messages.append(("debug", message, kwargs))


class FakeMessageGenerator(MessageGeneratorPort):
    """Returns a predictable message for testing."""

    def __init__(self, prefix: str = "Hey") -> None:
        self._prefix = prefix

    def generate(
        self,
        sender: Attendee,
        recipient: Attendee,
        context: str | None = None,
    ) -> str:
        """Generate a fake message."""
        return f"{self._prefix} {recipient.first_name}, this is {sender.first_name}."


class FakeBrellaApi(BrellaApiPort):
    """In-memory Brella API for testing."""

    def __init__(
        self,
        attendees: list[Attendee] | None = None,
        event: Event | None = None,
        me: Attendee | None = None,
    ) -> None:
        self._attendees = attendees or []
        self._event = event or Event(id=1, slug="test-event", name="Test Event")
        self._me = me
        self.sent_chats: list[dict] = []

    def get_event(self, event_slug: str) -> Event:
        """Return fake event."""
        return self._event

    def get_me_attendee(self, event_slug: str) -> Attendee:
        """Return fake me attendee."""
        if self._me:
            return self._me
        return Attendee(
            id=999,
            user_id=9999,
            event_slug=event_slug,
            first_name="Test",
            last_name="Sender",
            interest_names=["AI"],
        )

    def list_attendees(
        self,
        event_slug: str,
        page: int = 1,
        page_size: int = 50,
    ) -> list[Attendee]:
        """Return paginated fake attendees."""
        start = (page - 1) * page_size
        return self._attendees[start : start + page_size]

    def list_all_attendees(self, event_slug: str) -> list[Attendee]:
        """Return all fake attendees."""
        return self._attendees

    def get_attendee(self, event_slug: str, attendee_id: int) -> Attendee:
        """Return fake attendee by ID."""
        for a in self._attendees:
            if a.id == attendee_id:
                return a
        msg = f"Attendee {attendee_id} not found"
        raise ValueError(msg)

    def search_attendees(self, event_slug: str, query: str) -> list[Attendee]:
        """Search fake attendees."""
        q = query.lower()
        return [
            a
            for a in self._attendees
            if q in a.first_name.lower()
            or q in a.last_name.lower()
            or q in (a.company_name or "").lower()
        ]

    def start_chat(self, user_id: int, event_id: int, message: str) -> dict:
        """Record a fake chat send."""
        self.sent_chats.append({
            "user_id": user_id,
            "event_id": event_id,
            "message": message,
        })
        return {"data": {"id": len(self.sent_chats)}}
