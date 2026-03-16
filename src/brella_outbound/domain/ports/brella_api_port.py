"""Brella API port interface."""

from abc import ABC, abstractmethod

from brella_outbound.domain.models.attendee import Attendee
from brella_outbound.domain.models.event import Event


class BrellaApiPort(ABC):
    """Abstract interface for Brella API operations."""

    @abstractmethod
    def get_event(self, event_slug: str) -> Event:
        """Fetch event details by slug."""
        raise NotImplementedError

    @abstractmethod
    def get_me_attendee(self, event_slug: str) -> Attendee:
        """Fetch the authenticated user's attendee profile."""
        raise NotImplementedError

    @abstractmethod
    def list_attendees(
        self,
        event_slug: str,
        page: int = 1,
        page_size: int = 50,
    ) -> list[Attendee]:
        """List attendees for an event with pagination."""
        raise NotImplementedError

    @abstractmethod
    def get_attendee(self, event_slug: str, attendee_id: int) -> Attendee:
        """Fetch a single attendee by ID."""
        raise NotImplementedError

    @abstractmethod
    def search_attendees(
        self,
        event_slug: str,
        query: str,
    ) -> list[Attendee]:
        """Search attendees by name, title, or company."""
        raise NotImplementedError

    @abstractmethod
    def start_chat(
        self,
        user_id: int,
        event_id: int,
        message: str,
    ) -> dict:
        """Send a chat message to start a conversation with an attendee.

        Args:
            user_id: The target user's ID.
            event_id: The event ID.
            message: The intro message (max 500 chars).

        Returns:
            Response data from the API.
        """
        raise NotImplementedError
