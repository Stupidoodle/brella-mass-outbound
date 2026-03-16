"""Message generator port interface."""

from abc import ABC, abstractmethod

from brella_outbound.domain.models.attendee import Attendee


class MessageGeneratorPort(ABC):
    """Abstract interface for generating personalized outreach messages."""

    @abstractmethod
    def generate(
        self,
        sender: Attendee,
        recipient: Attendee,
        context: str | None = None,
    ) -> str:
        """Generate a personalized message for an attendee.

        Args:
            sender: The sender's attendee profile.
            recipient: The target attendee profile.
            context: Optional additional context (e.g., event name, goals).

        Returns:
            A personalized message string (max 500 chars for Brella).
        """
        raise NotImplementedError
