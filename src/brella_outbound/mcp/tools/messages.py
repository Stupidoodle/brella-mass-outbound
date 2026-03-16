"""Messaging MCP tools — send chats and poke nudges."""

from typing import Any

from mcp.server.fastmcp import FastMCP

from brella_outbound.core.config import Settings
from brella_outbound.infrastructure.brella.brella_api_client import BrellaApiClient


def register_message_tools(
    mcp: FastMCP,
    client: BrellaApiClient,
    settings: Settings,
) -> None:
    """Register messaging tools with the MCP server."""

    @mcp.tool(annotations={"destructive": True})
    def send_chat(
        event_slug: str,
        attendee_id: int,
        message: str,
    ) -> dict[str, Any]:
        """Send a cold outreach chat message to an attendee.

        This creates a new chat/meeting request. Can only be sent once
        per attendee — subsequent attempts will fail.

        Args:
            event_slug: The Brella event slug.
            attendee_id: The target attendee's ID.
            message: The intro message (max 500 chars).

        Returns:
            Meeting ID and chat conversation ID on success.
        """
        try:
            event = client.get_event(event_slug)
            attendee = client.get_attendee(event_slug, attendee_id)

            result = client.start_chat(
                user_id=attendee.user_id,
                event_id=event.id,
                message=message,
            )

            meeting_data = result.get("data", {})
            attrs = meeting_data.get("attributes", {})
            rels = meeting_data.get("relationships", {})
            chat_conv = rels.get("chat-conversation", {}).get("data", {})

            return {
                "success": True,
                "meeting_id": int(meeting_data.get("id", 0)),
                "chat_conversation_id": int(chat_conv.get("id", 0)),
                "attendee": attendee.full_name,
                "poke_messages_left": attrs.get("poke-chat-messages-left", 0),
            }
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool(annotations={"destructive": True})
    def poke_nudge(
        meeting_id: int,
        message: str,
    ) -> dict[str, Any]:
        """Send a follow-up nudge for an unanswered chat request.

        You get exactly 1 poke per conversation. Use it wisely.

        Args:
            meeting_id: The meeting ID from a previous send_chat.
            message: The nudge message.

        Returns:
            Success status.
        """
        try:
            result = client.poke(meeting_id, message)
            return {"success": True, "meeting_id": meeting_id, "data": result}
        except Exception as e:
            return {"error": str(e), "meeting_id": meeting_id}

    @mcp.tool()
    def generate_message(
        event_slug: str,
        attendee_id: int,
        context: str | None = None,
    ) -> dict[str, Any]:
        """Generate a personalized outreach message for an attendee.

        Uses the configured LLM provider (claude/openai/template) to
        generate a message based on both profiles and shared interests.

        Args:
            event_slug: The Brella event slug.
            attendee_id: The target attendee's ID.
            context: Optional extra context (e.g. 'interested in their AI work').

        Returns:
            Generated message text and profile context.
        """
        try:
            from brella_outbound.bootstrap import _build_generator
            from brella_outbound.infrastructure.observability.console_logger import (
                ConsoleLogger,
            )

            me = client.get_me_attendee(event_slug)
            them = client.get_attendee(event_slug, attendee_id)

            generator = _build_generator(settings, ConsoleLogger("mcp_gen"))
            message = generator.generate(sender=me, recipient=them, context=context)

            my_set = {i.lower() for i in me.interest_names}
            common = [i for i in them.interest_names if i.lower() in my_set]

            return {
                "message": message,
                "length": len(message),
                "max_length": settings.CAMPAIGN_MESSAGE_MAX_LENGTH,
                "recipient": them.full_name,
                "common_interests": common,
            }
        except Exception as e:
            return {"error": str(e)}
