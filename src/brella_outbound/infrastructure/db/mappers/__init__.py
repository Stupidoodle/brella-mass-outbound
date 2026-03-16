"""Imperative SQLAlchemy mappings between domain models and tables.

This module configures the mapper registry so that plain dataclass domain
models can be persisted via SQLAlchemy's Unit-of-Work without inheriting
from any ORM base class.

Hydration-only fields on ``Attendee`` (``persona``, ``function``,
``industry``, ``group``, ``selected_interests``, ``interest_names``) are
excluded from the column mapping because they have no corresponding table
column — they are populated in-memory after loading from the API.
"""

from sqlalchemy.orm import registry, relationship

from brella_outbound.domain.models.attendee import (
    Attendee,
    AttendeeGroup,
    Function,
    Industry,
    Intent,
    IntentPair,
    Interest,
    InterestCategory,
    Persona,
    SelectedInterest,
)
from brella_outbound.domain.models.campaign import Campaign, OutreachMessage
from brella_outbound.domain.models.event import Event
from brella_outbound.infrastructure.db.tables.attendee import attendee_table
from brella_outbound.infrastructure.db.tables.attendee_group import (
    attendee_group_table,
)
from brella_outbound.infrastructure.db.tables.campaign import campaign_table
from brella_outbound.infrastructure.db.tables.event import event_table
from brella_outbound.infrastructure.db.tables.function import function_table
from brella_outbound.infrastructure.db.tables.industry import industry_table
from brella_outbound.infrastructure.db.tables.intent import intent_table
from brella_outbound.infrastructure.db.tables.intent_pair import intent_pair_table
from brella_outbound.infrastructure.db.tables.interest import interest_table
from brella_outbound.infrastructure.db.tables.interest_category import (
    interest_category_table,
)
from brella_outbound.infrastructure.db.tables.outreach_message import (
    outreach_message_table,
)
from brella_outbound.infrastructure.db.tables.persona import persona_table
from brella_outbound.infrastructure.db.tables.selected_interest import (
    selected_interest_table,
)

mapper_registry = registry()


def start_mappers() -> None:
    """Register all imperative mappings.

    Must be called once at application startup before any ORM operations.
    Subsequent calls are silently ignored (idempotent).
    """
    if mapper_registry.mappers:
        return

    # -- Reference data models (simple 1:1 column mapping) ----------------

    mapper_registry.map_imperatively(InterestCategory, interest_category_table)
    mapper_registry.map_imperatively(Interest, interest_table)
    mapper_registry.map_imperatively(IntentPair, intent_pair_table)
    mapper_registry.map_imperatively(Intent, intent_table)
    mapper_registry.map_imperatively(Persona, persona_table)
    mapper_registry.map_imperatively(Function, function_table)
    mapper_registry.map_imperatively(Industry, industry_table)
    mapper_registry.map_imperatively(AttendeeGroup, attendee_group_table)
    mapper_registry.map_imperatively(SelectedInterest, selected_interest_table)
    mapper_registry.map_imperatively(Event, event_table)

    # -- Attendee ----------------------------------------------------------
    # Hydration-only fields must be excluded from the column mapping.  We
    # list only the columns that exist in the table and tell SQLAlchemy to
    # leave the remaining dataclass fields alone via ``exclude_properties``.

    mapper_registry.map_imperatively(
        Attendee,
        attendee_table,
        properties={
            "persona": relationship(Persona, lazy="joined", viewonly=True),
            "function": relationship(Function, lazy="joined", viewonly=True),
            "industry": relationship(Industry, lazy="joined", viewonly=True),
            "group": relationship(
                AttendeeGroup,
                lazy="joined",
                viewonly=True,
            ),
            "selected_interests": relationship(
                SelectedInterest,
                lazy="joined",
                viewonly=True,
                foreign_keys=[selected_interest_table.c.attendee_id],
            ),
        },
        exclude_properties={"interest_names"},
    )

    # -- Campaign & OutreachMessage ----------------------------------------

    mapper_registry.map_imperatively(
        OutreachMessage,
        outreach_message_table,
        properties={
            "id": outreach_message_table.c.id,
            "campaign_id": outreach_message_table.c.campaign_id,
        },
    )

    mapper_registry.map_imperatively(
        Campaign,
        campaign_table,
        properties={
            "id": campaign_table.c.id,
            "messages": relationship(OutreachMessage, lazy="joined"),
        },
    )
