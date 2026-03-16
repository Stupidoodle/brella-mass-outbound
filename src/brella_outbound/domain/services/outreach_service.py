"""Outreach domain service — filtering, dedup, personalization logic."""

from brella_outbound.domain.models.attendee import Attendee
from brella_outbound.domain.ports.logger_port import LoggerPort


class OutreachService:
    """Handles attendee filtering and targeting logic."""

    def __init__(self, logger: LoggerPort) -> None:
        self._logger = logger

    def filter_attendees(
        self,
        attendees: list[Attendee],
        *,
        exclude_ids: set[int] | None = None,
        personas: list[str] | None = None,
        industries: list[str] | None = None,
        interests: list[str] | None = None,
        min_common_interests: int = 0,
        my_interests: list[str] | None = None,
    ) -> list[Attendee]:
        """Filter attendees based on targeting criteria.

        Args:
            attendees: Full list of attendees.
            exclude_ids: Attendee IDs to skip (already contacted, self, etc.).
            personas: Only include these personas (e.g., "Startup (Founder)").
            industries: Only include these industries.
            interests: Only include attendees with at least one of these interests.
            min_common_interests: Minimum shared interests with sender.
            my_interests: The sender's interests (for computing overlap).

        Returns:
            Filtered list of attendees matching criteria.
        """
        filtered = attendees
        exclude = exclude_ids or set()

        if exclude:
            filtered = [a for a in filtered if a.id not in exclude]

        if personas:
            personas_lower = {p.lower() for p in personas}
            filtered = [
                a for a in filtered
                if a.persona_name and a.persona_name.lower() in personas_lower
            ]

        if industries:
            industries_lower = {i.lower() for i in industries}
            filtered = [
                a for a in filtered
                if a.industry_name
                and a.industry_name.lower() in industries_lower
            ]

        if interests:
            interests_lower = {i.lower() for i in interests}
            filtered = [
                a for a in filtered
                if any(
                    i.lower() in interests_lower for i in a.interest_names
                )
            ]

        if min_common_interests > 0 and my_interests:
            my_set = {i.lower() for i in my_interests}
            filtered = [
                a for a in filtered
                if len(my_set & {i.lower() for i in a.interest_names})
                >= min_common_interests
            ]

        self._logger.info(
            "filtered attendees",
            total=len(attendees),
            after_filter=len(filtered),
        )
        return filtered

    def compute_common_interests(
        self,
        sender: Attendee,
        recipient: Attendee,
    ) -> list[str]:
        """Compute shared interests between two attendees."""
        sender_set = {i.lower() for i in sender.interest_names}
        return [
            i for i in recipient.interest_names if i.lower() in sender_set
        ]
