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
    ) -> tuple[list[Attendee], dict]:
        """List attendees for an event with pagination.

        Returns:
            A tuple of (attendees, pagination_meta) where pagination_meta
            contains keys like ``total_count``, ``total_pages``, and
            ``current_page``.
        """
        raise NotImplementedError

    @abstractmethod
    def list_all_attendees(self, event_slug: str) -> list[Attendee]:
        """Fetch every attendee for an event, handling pagination internally."""
        raise NotImplementedError

    @abstractmethod
    def get_interests(self, event_slug: str) -> dict:
        """Fetch the interest taxonomy for an event.

        Returns:
            Raw interest data from the API.
        """
        raise NotImplementedError

    @abstractmethod
    def filter_attendees(
        self,
        event_slug: str,
        *,
        persona_ids: list[int] | None = None,
        interest_ids: list[int] | None = None,
        industry_ids: list[int] | None = None,
        function_ids: list[int] | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Attendee], dict]:
        """List attendees filtered by persona, interest, industry, or function.

        Args:
            event_slug: The event identifier.
            persona_ids: Optional persona IDs to filter by.
            interest_ids: Optional interest IDs to filter by.
            industry_ids: Optional industry IDs to filter by.
            function_ids: Optional function IDs to filter by.
            page: Page number (1-indexed).
            page_size: Number of results per page.

        Returns:
            A tuple of (attendees, pagination_meta).
        """
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

    @abstractmethod
    def poke(self, meeting_id: int, message: str) -> dict:
        """Send a follow-up nudge for an existing meeting request.

        Args:
            meeting_id: The meeting/chat ID to poke.
            message: The nudge message.

        Returns:
            Response data from the API.
        """
        raise NotImplementedError
