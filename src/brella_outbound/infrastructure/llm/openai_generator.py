"""OpenAI API message generator."""

from openai import OpenAI

from brella_outbound.core.config import Settings
from brella_outbound.domain.models.attendee import Attendee
from brella_outbound.domain.ports.logger_port import LoggerPort
from brella_outbound.domain.ports.message_generator_port import MessageGeneratorPort


class OpenAIGenerator(MessageGeneratorPort):
    """Generates personalized outreach messages using OpenAI API."""

    def __init__(self, settings: Settings, logger: LoggerPort) -> None:
        self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self._model = settings.OPENAI_MODEL
        self._max_length = settings.CAMPAIGN_MESSAGE_MAX_LENGTH
        self._logger = logger

    def generate(
        self,
        sender: Attendee,
        recipient: Attendee,
        context: str | None = None,
    ) -> str:
        """Generate a personalized message using OpenAI.

        Args:
            sender: The sender's attendee profile.
            recipient: The target attendee profile.
            context: Optional additional context (e.g., event name, goals).

        Returns:
            A personalized message string truncated to max length.
        """
        prompt = self._build_prompt(sender, recipient, context)
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
        )
        message = (response.choices[0].message.content or "").strip()
        # Truncate to Brella's max
        if len(message) > self._max_length:
            message = message[: self._max_length - 3] + "..."
        self._logger.debug(
            "generated openai message",
            recipient=recipient.full_name,
        )
        return message

    def _build_prompt(
        self,
        sender: Attendee,
        recipient: Attendee,
        context: str | None,
    ) -> str:
        """Build the prompt from sender/recipient profiles.

        Args:
            sender: The sender's attendee profile.
            recipient: The target attendee profile.
            context: Optional additional context.

        Returns:
            A formatted prompt string.
        """
        common_interests = set(sender.interest_names) & set(
            recipient.interest_names,
        )
        prompt = (
            f"Write a short, personalized networking message "
            f"(max {self._max_length} chars) from {sender.full_name} "
            f"to {recipient.first_name} for an event networking platform."
            f"\n\n"
            f"Sender: {sender.full_name}, "
            f"{sender.company_title or ''} at "
            f"{sender.company_name or ''}\n"
            f"Sender's interests: "
            f"{', '.join(sender.interest_names[:10])}\n"
            f"{f'Sender bio: {sender.pitch[:200]}' if sender.pitch else ''}"
            f"\n\n"
            f"Recipient: {recipient.full_name}, "
            f"{recipient.company_title or ''} at "
            f"{recipient.company_name or ''}\n"
            f"Recipient's interests: "
            f"{', '.join(recipient.interest_names[:10])}\n"
            f"{f'Recipient bio: {recipient.pitch[:200]}' if recipient.pitch else ''}\n"
            f"{f'Recipient persona: {recipient.persona_name}' if recipient.persona_name else ''}\n"
            f"{f'Recipient industry: {recipient.industry_name}' if recipient.industry_name else ''}"
            f"\n\n"
            f"Common interests: "
            f"{', '.join(common_interests) if common_interests else 'None identified'}"
            f"\n\n"
            f"{f'Additional context: {context}' if context else ''}"
            f"\n\n"
            f"Rules:\n"
            f"- Be genuine and specific, reference shared interests or "
            f"their work\n"
            f"- Don't be salesy or generic. "
            f'No "I\'d love to connect" filler.\n'
            f"- Keep it conversational and brief\n"
            f'- Start with "Hi {recipient.first_name}" or similar\n'
            f"- Must be under {self._max_length} characters"
        )
        return prompt
