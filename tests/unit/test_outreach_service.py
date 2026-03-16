"""Tests for the outreach domain service."""

from brella_outbound.domain.models.attendee import Attendee, Persona, Industry
from brella_outbound.domain.services.outreach_service import OutreachService
from tests.fakes import FakeLogger


def _make_attendee(
    id: int,
    name: str = "Test",
    persona: str | None = None,
    industry: str | None = None,
    interests: list[str] | None = None,
) -> Attendee:
    """Create a minimal attendee for testing."""
    return Attendee(
        id=id,
        user_id=id * 10,
        event_slug="test-event",
        first_name=name,
        last_name="User",
        persona=Persona(id=id, name=persona) if persona else None,
        industry=Industry(id=id, name=industry) if industry else None,
        interest_names=interests or [],
    )


class TestFilterAttendees:
    """Tests for OutreachService.filter_attendees."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.service = OutreachService(logger=FakeLogger())
        self.attendees = [
            _make_attendee(1, "Alice", "Startup (Founder)", "FinTech", ["AI", "ML"]),
            _make_attendee(2, "Bob", "Investor", "FinTech", ["AI", "Robotics"]),
            _make_attendee(3, "Charlie", "Student", "EdTech", ["ML", "Data"]),
            _make_attendee(4, "Diana", "Startup (Founder)", "HealthTech", ["AI"]),
            _make_attendee(5, "Eve", "Investor", "FinTech", ["Blockchain"]),
        ]

    def test_no_filters_returns_all(self) -> None:
        """With no filters, all attendees are returned."""
        result = self.service.filter_attendees(self.attendees)
        assert len(result) == 5

    def test_exclude_ids(self) -> None:
        """Excluded IDs are removed."""
        result = self.service.filter_attendees(
            self.attendees,
            exclude_ids={1, 3},
        )
        assert len(result) == 3
        assert all(a.id not in {1, 3} for a in result)

    def test_filter_by_persona(self) -> None:
        """Filter by persona name."""
        result = self.service.filter_attendees(
            self.attendees,
            personas=["Startup (Founder)"],
        )
        assert len(result) == 2
        assert {a.first_name for a in result} == {"Alice", "Diana"}

    def test_filter_by_persona_case_insensitive(self) -> None:
        """Persona filter is case-insensitive."""
        result = self.service.filter_attendees(
            self.attendees,
            personas=["startup (founder)"],
        )
        assert len(result) == 2

    def test_filter_by_industry(self) -> None:
        """Filter by industry."""
        result = self.service.filter_attendees(
            self.attendees,
            industries=["FinTech"],
        )
        assert len(result) == 3
        assert {a.first_name for a in result} == {"Alice", "Bob", "Eve"}

    def test_filter_by_interests(self) -> None:
        """Filter by at least one matching interest."""
        result = self.service.filter_attendees(
            self.attendees,
            interests=["Robotics"],
        )
        assert len(result) == 1
        assert result[0].first_name == "Bob"

    def test_filter_by_min_common_interests(self) -> None:
        """Filter by minimum shared interests with sender."""
        result = self.service.filter_attendees(
            self.attendees,
            min_common_interests=2,
            my_interests=["AI", "ML"],
        )
        # Alice has AI + ML (2), Bob has AI (1), Charlie has ML (1), Diana has AI (1)
        assert len(result) == 1
        assert result[0].first_name == "Alice"

    def test_combined_filters(self) -> None:
        """Multiple filters combine (AND logic)."""
        result = self.service.filter_attendees(
            self.attendees,
            personas=["Investor"],
            industries=["FinTech"],
        )
        assert len(result) == 2
        assert {a.first_name for a in result} == {"Bob", "Eve"}

    def test_combined_filters_with_interests(self) -> None:
        """Persona + interest filter narrows results."""
        result = self.service.filter_attendees(
            self.attendees,
            personas=["Investor"],
            interests=["AI"],
        )
        assert len(result) == 1
        assert result[0].first_name == "Bob"


class TestComputeCommonInterests:
    """Tests for OutreachService.compute_common_interests."""

    def test_common_interests(self) -> None:
        """Finds shared interests between sender and recipient."""
        service = OutreachService(logger=FakeLogger())
        sender = _make_attendee(1, interests=["AI", "ML", "Data"])
        recipient = _make_attendee(2, interests=["AI", "Robotics", "Data"])

        common = service.compute_common_interests(sender, recipient)
        assert set(common) == {"AI", "Data"}

    def test_no_common_interests(self) -> None:
        """Returns empty when no overlap."""
        service = OutreachService(logger=FakeLogger())
        sender = _make_attendee(1, interests=["AI"])
        recipient = _make_attendee(2, interests=["Blockchain"])

        common = service.compute_common_interests(sender, recipient)
        assert common == []

    def test_case_insensitive_matching(self) -> None:
        """Interest matching is case-insensitive."""
        service = OutreachService(logger=FakeLogger())
        sender = _make_attendee(1, interests=["artificial intelligence"])
        recipient = _make_attendee(2, interests=["Artificial Intelligence"])

        common = service.compute_common_interests(sender, recipient)
        assert len(common) == 1
