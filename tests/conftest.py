"""Shared test fixtures."""

import pytest

from brella_outbound.core.config import Settings
from brella_outbound.domain.models.attendee import Attendee, Persona, Function, Industry
from brella_outbound.infrastructure.db.mappers import start_mappers
from brella_outbound.infrastructure.db.unit_of_work import UnitOfWork, build_session_factory


@pytest.fixture(scope="session", autouse=True)
def _configure_mappers() -> None:
    """Configure imperative mappers once per test session."""
    start_mappers()


@pytest.fixture
def test_settings() -> Settings:
    """Settings for testing (in-memory SQLite, template generator)."""
    return Settings(
        DATABASE_URL="sqlite:///:memory:",
        LLM_PROVIDER="template",
        BRELLA_AUTH_TOKEN='{"access-token":"fake","client":"fake","uid":"test@test.com"}',
        BRELLA_API_BASE_URL="https://api.brella.io/api",
    )


@pytest.fixture
def uow(test_settings: Settings) -> UnitOfWork:
    """UoW with in-memory SQLite for tests."""
    session_factory = build_session_factory(test_settings.DATABASE_URL)
    return UnitOfWork(session_factory)


@pytest.fixture
def sender() -> Attendee:
    """Sample sender attendee."""
    return Attendee(
        id=1,
        user_id=100,
        event_slug="test-event",
        first_name="Bryan",
        last_name="Tran",
        company_title="Senior Data Engineer",
        company_name="cohaga AG",
        pitch="I love sidequests and ABGs",
        persona=Persona(id=1, name="Startup (Founder)"),
        function=Function(id=1, name="Engineer"),
        industry=Industry(id=1, name="Enterprise Software & SaaS"),
        interest_names=[
            "Backend Development",
            "Data Science/ ML",
            "IT Security",
            "Artificial Intelligence",
            "Entrepreneurship",
        ],
    )


@pytest.fixture
def recipient() -> Attendee:
    """Sample recipient attendee."""
    return Attendee(
        id=2,
        user_id=200,
        event_slug="test-event",
        first_name="Philip",
        last_name="Benson",
        company_title="Co-Founder & CEO",
        company_name="NAIRON",
        pitch="Building the next generation of Voice AI. ETH Zürich & TU Delft",
        persona=Persona(id=2, name="Startup (Founder)"),
        function=Function(id=2, name="Founder / Co-Founder"),
        industry=Industry(id=2, name="Enterprise Software & SaaS"),
        interest_names=[
            "Backend Development",
            "Data Science/ ML",
            "IT Security",
            "Artificial Intelligence",
            "Computer Science",
        ],
    )
