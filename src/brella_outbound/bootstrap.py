"""Composition root — all dependency wiring happens here."""

from brella_outbound.core.config import LLMProvider, Settings, get_settings
from brella_outbound.domain.ports.brella_api_port import BrellaApiPort
from brella_outbound.domain.ports.logger_port import LoggerPort
from brella_outbound.domain.ports.message_generator_port import MessageGeneratorPort
from brella_outbound.infrastructure.brella.brella_api_client import BrellaApiClient
from brella_outbound.infrastructure.db.mappers import start_mappers
from brella_outbound.infrastructure.db.unit_of_work import (
    UnitOfWork,
    build_session_factory,
)
from brella_outbound.infrastructure.observability.console_logger import ConsoleLogger


class Container:
    """Holds all wired dependencies for the application."""

    def __init__(
        self,
        settings: Settings,
        logger: LoggerPort,
        brella_api: BrellaApiPort,
        message_generator: MessageGeneratorPort,
        uow: UnitOfWork,
    ) -> None:
        self.settings = settings
        self.logger = logger
        self.brella_api = brella_api
        self.message_generator = message_generator
        self.uow = uow


class Bootstrap:
    """Builds the dependency container."""

    @staticmethod
    def build(settings: Settings | None = None) -> Container:
        """Build a fully wired Container.

        Args:
            settings: Optional settings override (uses singleton if None).

        Returns:
            Wired Container with all services.
        """
        settings = settings or get_settings()
        logger = ConsoleLogger("brella_outbound")

        # Configure imperative mappers
        start_mappers()

        # Database
        session_factory = build_session_factory(settings.DATABASE_URL)
        uow = UnitOfWork(session_factory)

        # Brella API client
        brella_api = BrellaApiClient(settings=settings, logger=logger)

        # Message generator (based on LLM_PROVIDER setting)
        message_generator = _build_generator(settings, logger)

        return Container(
            settings=settings,
            logger=logger,
            brella_api=brella_api,
            message_generator=message_generator,
            uow=uow,
        )


def _build_generator(
    settings: Settings,
    logger: LoggerPort,
) -> MessageGeneratorPort:
    """Build the message generator based on LLM_PROVIDER setting."""
    if settings.LLM_PROVIDER == LLMProvider.CLAUDE:
        from brella_outbound.infrastructure.llm.claude_generator import (
            ClaudeGenerator,
        )

        return ClaudeGenerator(settings=settings, logger=logger)

    if settings.LLM_PROVIDER == LLMProvider.OPENAI:
        from brella_outbound.infrastructure.llm.openai_generator import (
            OpenAIGenerator,
        )

        return OpenAIGenerator(settings=settings, logger=logger)

    from brella_outbound.infrastructure.llm.template_generator import (
        TemplateGenerator,
    )

    return TemplateGenerator(settings=settings, logger=logger)
