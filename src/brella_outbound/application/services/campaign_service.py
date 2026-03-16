"""Campaign application service — orchestrates the full outreach pipeline."""

from datetime import datetime

from brella_outbound.domain.models.campaign import (
    Campaign,
    OutreachMessage,
    OutreachStatus,
)
from brella_outbound.domain.ports.brella_api_port import BrellaApiPort
from brella_outbound.domain.ports.logger_port import LoggerPort
from brella_outbound.domain.ports.message_generator_port import MessageGeneratorPort
from brella_outbound.domain.services.outreach_service import OutreachService
from brella_outbound.infrastructure.db.unit_of_work import UnitOfWork


class CampaignService:
    """Runs the full outreach campaign pipeline.

    1. Fetch attendees from Brella
    2. Filter based on targeting criteria
    3. Generate personalized messages
    4. Send (or dry-run preview)
    5. Persist campaign results to DB
    """

    def __init__(
        self,
        brella_api: BrellaApiPort,
        message_generator: MessageGeneratorPort,
        outreach_service: OutreachService,
        uow: UnitOfWork,
        logger: LoggerPort,
    ) -> None:
        self._brella_api = brella_api
        self._generator = message_generator
        self._outreach = outreach_service
        self._uow = uow
        self._logger = logger


    def run(
        self,
        event_slug: str,
        *,
        dry_run: bool = True,
        personas: list[str] | None = None,
        industries: list[str] | None = None,
        interests: list[str] | None = None,
        min_common_interests: int = 0,
        max_messages: int | None = None,
        context: str | None = None,
    ) -> Campaign:
        """Execute an outreach campaign.

        Args:
            event_slug: Brella event slug.
            dry_run: If True, generate messages but don't send.
            personas: Filter by persona names.
            industries: Filter by industry names.
            interests: Filter by interest names.
            min_common_interests: Minimum shared interests with sender.
            max_messages: Cap on number of messages to send.
            context: Additional context for message generation.

        Returns:
            Campaign with all generated/sent messages.
        """
        self._logger.info("starting campaign", event_slug=event_slug, dry_run=dry_run)

        # 1. Fetch event and my profile
        event = self._brella_api.get_event(event_slug)
        me = self._brella_api.get_me_attendee(event_slug)
        self._logger.info("fetched sender profile", name=me.full_name)

        # 2. Fetch all attendees
        attendees = self._brella_api.list_all_attendees(event_slug)
        self._logger.info("fetched attendees", count=len(attendees))

        # 3. Get already-contacted attendee IDs from DB
        contacted_ids = self._get_contacted_ids(event_slug)

        # 4. Filter attendees
        exclude_ids = contacted_ids | {me.id}
        targets = self._outreach.filter_attendees(
            attendees,
            exclude_ids=exclude_ids,
            personas=personas,
            industries=industries,
            interests=interests,
            min_common_interests=min_common_interests,
            my_interests=me.interest_names,
        )

        if max_messages:
            targets = targets[:max_messages]

        self._logger.info("targets after filtering", count=len(targets))

        # 5. Generate messages and optionally send
        campaign = Campaign(event_slug=event_slug)

        for target in targets:
            try:
                message_text = self._generator.generate(
                    sender=me,
                    recipient=target,
                    context=context,
                )

                outreach_msg = OutreachMessage(
                    attendee_id=target.id,
                    attendee_name=target.full_name,
                    message=message_text,
                )

                if not dry_run:
                    self._brella_api.start_chat(
                        user_id=target.user_id,
                        event_id=event.id,
                        message=message_text,
                    )
                    outreach_msg.status = OutreachStatus.SENT
                    outreach_msg.sent_at = datetime.now()
                    self._logger.info(
                        "sent message",
                        to=target.full_name,
                    )
                else:
                    outreach_msg.status = OutreachStatus.PENDING
                    self._logger.info(
                        "dry-run message",
                        to=target.full_name,
                        preview=message_text[:80],
                    )

                campaign.messages.append(outreach_msg)

            except Exception as exc:
                self._logger.error(
                    "failed to process target",
                    target=target.full_name,
                    exc_info=exc,
                )
                campaign.messages.append(OutreachMessage(
                    attendee_id=target.id,
                    attendee_name=target.full_name,
                    message="",
                    status=OutreachStatus.FAILED,
                    error=str(exc),
                ))

        # 6. Persist campaign to DB
        self._persist_campaign(campaign)

        self._logger.info(
            "campaign complete",
            sent=campaign.sent_count,
            failed=campaign.failed_count,
            pending=campaign.pending_count,
        )
        return campaign

    def _get_contacted_ids(self, event_slug: str) -> set[int]:
        """Get attendee IDs already contacted in previous campaigns."""
        try:
            with self._uow:
                from sqlalchemy import select

                from brella_outbound.infrastructure.db.tables.campaign import (
                    campaign_table,
                )
                from brella_outbound.infrastructure.db.tables.outreach_message import (
                    outreach_message_table,
                )

                stmt = (
                    select(outreach_message_table.c.attendee_id)
                    .join(
                        campaign_table,
                        outreach_message_table.c.campaign_id == campaign_table.c.id,
                    )
                    .where(campaign_table.c.event_slug == event_slug)
                    .where(
                        outreach_message_table.c.status == OutreachStatus.SENT,
                    )
                )
                result = self._uow.session.execute(stmt)
                return {row[0] for row in result}
        except Exception:
            return set()

    def _persist_campaign(self, campaign: Campaign) -> None:
        """Save campaign and messages to the database."""
        try:
            with self._uow:
                self._uow.session.add(campaign)
        except Exception as exc:
            self._logger.error("failed to persist campaign", exc_info=exc)
