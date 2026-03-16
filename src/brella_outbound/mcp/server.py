"""Brella Mass Outbound MCP Server — full-power interface for Claude."""

import sys

import structlog
from mcp.server.fastmcp import FastMCP

from brella_outbound.core.config import Settings, get_settings
from brella_outbound.infrastructure.brella.brella_api_client import BrellaApiClient
from brella_outbound.infrastructure.db.mappers import start_mappers
from brella_outbound.infrastructure.db.unit_of_work import (
    UnitOfWork,
    build_session_factory,
)
from brella_outbound.infrastructure.observability.console_logger import ConsoleLogger
from brella_outbound.mcp.tools.attendees import register_attendee_tools
from brella_outbound.mcp.tools.campaign import register_campaign_tools
from brella_outbound.mcp.tools.interests import register_interest_tools
from brella_outbound.mcp.tools.messages import register_message_tools

logger = structlog.get_logger("brella_mcp")

_mcp: FastMCP | None = None
_client: BrellaApiClient | None = None
_uow: UnitOfWork | None = None
_settings: Settings | None = None


def get_client() -> BrellaApiClient:
    """Get the shared Brella API client."""
    if _client is None:
        msg = "MCP server not initialized"
        raise RuntimeError(msg)
    return _client


def get_uow() -> UnitOfWork:
    """Get the shared UnitOfWork."""
    if _uow is None:
        msg = "MCP server not initialized"
        raise RuntimeError(msg)
    return _uow


def get_mcp_settings() -> Settings:
    """Get the shared settings."""
    if _settings is None:
        return get_settings()
    return _settings


def create_server(settings: Settings | None = None) -> FastMCP:
    """Create and configure the MCP server with all tools."""
    global _mcp, _client, _uow, _settings

    _settings = settings or get_settings()

    _mcp = FastMCP("brella-outbound")

    # Configure DB
    start_mappers()
    session_factory = build_session_factory(_settings.DATABASE_URL)
    _uow = UnitOfWork(session_factory)

    # Authenticate with Brella
    app_logger = ConsoleLogger("brella_mcp")
    _client = BrellaApiClient(settings=_settings, logger=app_logger)

    # Register all tool groups
    register_attendee_tools(_mcp, _client)
    register_interest_tools(_mcp, _client)
    register_message_tools(_mcp, _client, _settings)
    register_campaign_tools(_mcp, _client, _settings)

    logger.info("brella mcp server initialized")
    return _mcp


def main() -> None:
    """Entry point for CLI — runs the MCP server over stdio."""
    try:
        mcp = create_server()
        mcp.run(transport="stdio")
    except ValueError as e:
        print(f"Auth error: {e}", file=sys.stderr)
        print(
            "Set BRELLA_EMAIL+BRELLA_PASSWORD or BRELLA_AUTH_TOKEN in .env",
            file=sys.stderr,
        )
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
