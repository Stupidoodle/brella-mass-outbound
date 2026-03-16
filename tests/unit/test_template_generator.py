"""Tests for the template-based message generator."""

from brella_outbound.core.config import Settings
from brella_outbound.domain.models.attendee import Attendee
from brella_outbound.infrastructure.llm.template_generator import TemplateGenerator
from tests.fakes import FakeLogger


def _make_attendee(
    first_name: str,
    interests: list[str] | None = None,
    pitch: str | None = None,
    company: str | None = None,
) -> Attendee:
    """Create a minimal attendee."""
    return Attendee(
        id=1,
        user_id=10,
        event_slug="test",
        first_name=first_name,
        last_name="User",
        company_name=company,
        pitch=pitch,
        interest_names=interests or [],
    )


class TestTemplateGenerator:
    """Tests for TemplateGenerator."""

    def _build(self, template: str | None = None) -> TemplateGenerator:
        """Build a generator with test settings."""
        settings = Settings(
            BRELLA_AUTH_TOKEN="fake",
            LLM_PROVIDER="template",
            CAMPAIGN_MESSAGE_MAX_LENGTH=500,
        )
        return TemplateGenerator(
            settings=settings,
            logger=FakeLogger(),
            template=template,
        )

    def test_default_template_includes_recipient_name(self) -> None:
        """Default template addresses recipient by first name."""
        gen = self._build()
        sender = _make_attendee("Bryan", interests=["AI"])
        recipient = _make_attendee("Philip", interests=["AI"], company="NAIRON")

        msg = gen.generate(sender, recipient)
        assert "Philip" in msg

    def test_default_template_includes_sender_name(self) -> None:
        """Default template signs off with sender name."""
        gen = self._build()
        sender = _make_attendee("Bryan")
        recipient = _make_attendee("Philip", company="NAIRON")

        msg = gen.generate(sender, recipient)
        assert "Bryan" in msg

    def test_default_template_includes_common_interests(self) -> None:
        """Default template mentions common interests when they exist."""
        gen = self._build()
        sender = _make_attendee("Bryan", interests=["AI", "ML"])
        recipient = _make_attendee("Philip", interests=["AI", "Robotics"])

        msg = gen.generate(sender, recipient)
        assert "AI" in msg

    def test_default_template_with_context(self) -> None:
        """Context is included when provided."""
        gen = self._build()
        sender = _make_attendee("Bryan")
        recipient = _make_attendee("Philip", company="NAIRON")

        msg = gen.generate(sender, recipient, context="Voice AI collaboration")
        assert "Voice AI collaboration" in msg

    def test_custom_template(self) -> None:
        """Custom Jinja2 template is used when provided."""
        custom = "Yo {{ recipient.first_name }}, {{ sender.first_name }} here."
        gen = self._build(template=custom)
        sender = _make_attendee("Bryan")
        recipient = _make_attendee("Philip")

        msg = gen.generate(sender, recipient)
        assert msg == "Yo Philip, Bryan here."

    def test_message_truncated_to_max_length(self) -> None:
        """Messages exceeding max length are truncated."""
        long_template = "{{ 'A' * 600 }}"
        gen = self._build(template=long_template)
        sender = _make_attendee("Bryan")
        recipient = _make_attendee("Philip")

        msg = gen.generate(sender, recipient)
        assert len(msg) <= 500

    def test_empty_interests_no_crash(self) -> None:
        """Works when both parties have no interests."""
        gen = self._build()
        sender = _make_attendee("Bryan", interests=[])
        recipient = _make_attendee("Philip", interests=[], company="NAIRON")

        msg = gen.generate(sender, recipient)
        assert "Philip" in msg
