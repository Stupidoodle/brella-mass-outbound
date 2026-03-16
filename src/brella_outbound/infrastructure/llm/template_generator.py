"""Jinja2 template-based message generator (no API key needed)."""

from jinja2 import Environment

from brella_outbound.core.config import Settings
from brella_outbound.domain.models.attendee import Attendee
from brella_outbound.domain.ports.logger_port import LoggerPort
from brella_outbound.domain.ports.message_generator_port import MessageGeneratorPort

DEFAULT_TEMPLATE = """\
Hi {{ recipient.first_name }},

{% if common_interests %}\
I noticed we share an interest in {{ common_interests[:3] | join(', ') }}. \
{% endif %}\
{% if recipient.company_name %}\
What you're building at {{ recipient.company_name }} looks interesting\
{% else %}\
Your profile caught my eye\
{% endif %}\
{% if context %} — would love to chat about {{ context }}{% endif %}. \
Let's connect!

{{ sender.first_name }}\
"""


class TemplateGenerator(MessageGeneratorPort):
    """Generates outreach messages by rendering a Jinja2 template."""

    def __init__(
        self,
        settings: Settings,
        logger: LoggerPort,
        template: str | None = None,
    ) -> None:
        self._env = Environment(autoescape=False)
        self._template = self._env.from_string(template or DEFAULT_TEMPLATE)
        self._max_length = settings.CAMPAIGN_MESSAGE_MAX_LENGTH
        self._logger = logger

    def generate(
        self,
        sender: Attendee,
        recipient: Attendee,
        context: str | None = None,
    ) -> str:
        """Generate a message by rendering the Jinja2 template.

        Args:
            sender: The sender's attendee profile.
            recipient: The target attendee profile.
            context: Optional additional context (e.g., event name, goals).

        Returns:
            A rendered message string truncated to max length.
        """
        common_interests = list(
            set(sender.interest_names) & set(recipient.interest_names),
        )
        message = self._template.render(
            sender=sender,
            recipient=recipient,
            common_interests=common_interests,
            context=context,
        ).strip()
        # Truncate to Brella's max
        if len(message) > self._max_length:
            message = message[: self._max_length - 3] + "..."
        self._logger.debug(
            "generated template message",
            recipient=recipient.full_name,
        )
        return message
