"""Tests for the campaign application service."""

from brella_outbound.application.services.campaign_service import CampaignService
from brella_outbound.core.config import Settings
from brella_outbound.domain.models.attendee import Attendee
from brella_outbound.domain.models.campaign import OutreachStatus
from brella_outbound.domain.services.outreach_service import OutreachService
from brella_outbound.infrastructure.db.unit_of_work import UnitOfWork, build_session_factory
from tests.fakes import FakeBrellaApi, FakeLogger, FakeMessageGenerator


def _test_settings() -> Settings:
    """Build settings for tests."""
    return Settings(
        BRELLA_AUTH_TOKEN="fake",
        LLM_PROVIDER="template",
        DATABASE_URL="sqlite:///:memory:",
        CAMPAIGN_FOOTER="",
        CAMPAIGN_FOOTER_ENABLED=False,
    )


def _make_attendees(count: int) -> list[Attendee]:
    """Create a list of test attendees."""
    return [
        Attendee(
            id=i,
            user_id=i * 10,
            event_slug="test-event",
            first_name=f"Person{i}",
            last_name="Test",
            company_name=f"Company{i}",
            interest_names=["AI", "ML"] if i % 2 == 0 else ["Robotics"],
        )
        for i in range(1, count + 1)
    ]


class TestCampaignServiceDryRun:
    """Tests for campaign dry-run mode."""

    def _build_service(
        self,
        attendees: list[Attendee] | None = None,
    ) -> tuple[CampaignService, FakeBrellaApi]:
        """Build a CampaignService with fakes."""
        logger = FakeLogger()
        api = FakeBrellaApi(
            attendees=attendees or _make_attendees(5),
            me=Attendee(
                id=999,
                user_id=9999,
                event_slug="test-event",
                first_name="Bryan",
                last_name="Tran",
                interest_names=["AI", "ML"],
            ),
        )
        generator = FakeMessageGenerator()
        outreach = OutreachService(logger=logger)
        sf = build_session_factory("sqlite:///:memory:")
        uow = UnitOfWork(sf)

        svc = CampaignService(
            brella_api=api,
            message_generator=generator,
            outreach_service=outreach,
            uow=uow,
            logger=logger,
        )
        return svc, api

    def test_dry_run_generates_messages(self) -> None:
        """Dry run generates messages without sending."""
        svc, api = self._build_service()
        campaign = svc.run("test-event", dry_run=True)

        assert len(campaign.messages) == 5
        assert campaign.sent_count == 0
        assert campaign.pending_count == 5
        assert len(api.sent_chats) == 0

    def test_dry_run_messages_contain_recipient_name(self) -> None:
        """Generated messages are personalized."""
        svc, _ = self._build_service()
        campaign = svc.run("test-event", dry_run=True)

        for msg in campaign.messages:
            assert msg.attendee_name in msg.message or "Person" in msg.message

    def test_live_run_sends_messages(self) -> None:
        """Live run actually calls start_chat."""
        svc, api = self._build_service()
        campaign = svc.run("test-event", dry_run=False)

        assert campaign.sent_count == 5
        assert len(api.sent_chats) == 5

    def test_max_messages_caps_output(self) -> None:
        """max_messages limits the number of targets."""
        svc, _ = self._build_service()
        campaign = svc.run("test-event", dry_run=True, max_messages=2)

        assert len(campaign.messages) == 2

    def test_excludes_self(self) -> None:
        """Sender is excluded from targets."""
        me = Attendee(
            id=3,
            user_id=30,
            event_slug="test-event",
            first_name="Bryan",
            last_name="Tran",
            interest_names=["AI"],
        )
        attendees = _make_attendees(5)
        logger = FakeLogger()
        api = FakeBrellaApi(attendees=attendees, me=me)
        generator = FakeMessageGenerator()
        outreach = OutreachService(logger=logger)
        sf = build_session_factory("sqlite:///:memory:")
        uow = UnitOfWork(sf)

        svc = CampaignService(
            brella_api=api,
            message_generator=generator,
            outreach_service=outreach,
            uow=uow,
            logger=logger,
        )
        campaign = svc.run("test-event", dry_run=True)

        # Attendee id=3 should be excluded (it's "me")
        ids = {m.attendee_id for m in campaign.messages}
        assert 3 not in ids
        assert len(campaign.messages) == 4

    def test_filter_by_persona(self) -> None:
        """Campaign respects persona filter."""
        from brella_outbound.domain.models.attendee import Persona

        attendees = [
            Attendee(
                id=1, user_id=10, event_slug="e", first_name="A", last_name="B",
                persona=Persona(id=1, name="Startup (Founder)"),
                interest_names=["AI"],
            ),
            Attendee(
                id=2, user_id=20, event_slug="e", first_name="C", last_name="D",
                persona=Persona(id=2, name="Student"),
                interest_names=["AI"],
            ),
        ]
        svc, _ = self._build_service(attendees=attendees)
        campaign = svc.run(
            "test-event",
            dry_run=True,
            personas=["Startup (Founder)"],
        )

        assert len(campaign.messages) == 1
        assert campaign.messages[0].attendee_name == "A B"


class TestCampaignServiceErrorHandling:
    """Tests for error handling in campaigns."""

    def test_failed_message_recorded(self) -> None:
        """If message generation fails, it's recorded as FAILED."""

        class FailingGenerator(FakeMessageGenerator):
            def generate(self, sender, recipient, context=None):
                raise RuntimeError("LLM is down")

        logger = FakeLogger()
        api = FakeBrellaApi(attendees=_make_attendees(2))
        outreach = OutreachService(logger=logger)
        sf = build_session_factory("sqlite:///:memory:")
        uow = UnitOfWork(sf)

        svc = CampaignService(
            brella_api=api,
            message_generator=FailingGenerator(),
            outreach_service=outreach,
            uow=uow,
            logger=logger,
        )
        campaign = svc.run("test-event", dry_run=True)

        assert campaign.failed_count == 2
        assert all(m.status == OutreachStatus.FAILED for m in campaign.messages)
        assert all("LLM is down" in (m.error or "") for m in campaign.messages)
