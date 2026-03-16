"""Campaign MCP tools — mass outreach orchestration."""

from typing import Any

from mcp.server.fastmcp import FastMCP

from brella_outbound.core.config import Settings
from brella_outbound.infrastructure.brella.brella_api_client import BrellaApiClient


def register_campaign_tools(
    mcp: FastMCP,
    client: BrellaApiClient,
    settings: Settings,
) -> None:
    """Register campaign orchestration tools with the MCP server."""

    @mcp.tool()
    def build_outbound_list(
        event_slug: str,
        persona_ids: list[int] | None = None,
        interest_ids: list[int] | None = None,
        industry_ids: list[int] | None = None,
        max_results: int = 50,
    ) -> dict[str, Any]:
        """Build a targeted outbound list using server-side filters.

        Fetches attendees matching your ICP criteria. Use
        get_interest_catalog to find valid IDs for filtering.

        Args:
            event_slug: The Brella event slug.
            persona_ids: Filter by persona IDs.
            interest_ids: Filter by interest IDs.
            industry_ids: Filter by industry IDs.
            max_results: Maximum attendees to return (fetches multiple pages).

        Returns:
            Targeted list of attendees ready for outreach.
        """
        try:
            all_targets: list[dict] = []
            page = 1

            while len(all_targets) < max_results:
                remaining = max_results - len(all_targets)
                page_size = min(remaining, 120)

                attendees, meta = client.filter_attendees(
                    event_slug,
                    persona_ids=persona_ids,
                    interest_ids=interest_ids,
                    industry_ids=industry_ids,
                    page=page,
                    page_size=page_size,
                )

                if not attendees:
                    break

                for a in attendees:
                    if len(all_targets) >= max_results:
                        break
                    all_targets.append({
                        "id": a.id,
                        "user_id": a.user_id,
                        "name": a.full_name,
                        "title": a.company_title,
                        "company": a.company_name,
                        "persona": a.persona_name,
                        "industry": a.industry_name,
                        "interests": a.interest_names[:6],
                        "bio": (a.pitch or "")[:100],
                    })

                total_pages = meta.get("total_pages", page)
                if page >= total_pages:
                    break
                page += 1

            return {
                "targets": all_targets,
                "count": len(all_targets),
                "total_matching": meta.get("total_count", len(all_targets)),
            }
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    def mass_generate_messages(
        event_slug: str,
        attendee_ids: list[int],
        context: str | None = None,
    ) -> dict[str, Any]:
        """Generate personalized messages for multiple attendees.

        Generates messages for each attendee using the configured LLM
        provider. Rate-limited to respect Brella's API limits.

        Args:
            event_slug: The Brella event slug.
            attendee_ids: List of attendee IDs to generate messages for.
            context: Optional extra context for message generation.

        Returns:
            List of generated messages ready for review and sending.
        """
        try:
            from brella_outbound.bootstrap import _build_generator
            from brella_outbound.infrastructure.observability.console_logger import (
                ConsoleLogger,
            )

            me = client.get_me_attendee(event_slug)
            generator = _build_generator(settings, ConsoleLogger("mcp_gen"))

            messages: list[dict] = []
            errors: list[dict] = []

            for aid in attendee_ids:
                try:
                    them = client.get_attendee(event_slug, aid)
                    msg = generator.generate(
                        sender=me,
                        recipient=them,
                        context=context,
                    )
                    messages.append({
                        "attendee_id": them.id,
                        "user_id": them.user_id,
                        "name": them.full_name,
                        "message": msg,
                        "length": len(msg),
                    })
                except Exception as e:
                    errors.append({"attendee_id": aid, "error": str(e)})

            return {
                "messages": messages,
                "generated": len(messages),
                "errors": errors,
                "error_count": len(errors),
            }
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool(annotations={"destructive": True})
    def mass_send_messages(
        event_slug: str,
        messages: list[dict],
    ) -> dict[str, Any]:
        """Send pre-generated messages to multiple attendees.

        Takes the output from mass_generate_messages and sends each
        message. Rate-limited to avoid bans.

        IMPORTANT: Review messages before calling this. This sends real
        chat requests that cannot be undone.

        Args:
            event_slug: The Brella event slug.
            messages: List of dicts with 'user_id' and 'message' keys
                      (output from mass_generate_messages).

        Returns:
            Results for each send attempt with meeting IDs.
        """
        try:
            event = client.get_event(event_slug)
            results: list[dict] = []
            errors: list[dict] = []

            for msg_data in messages:
                user_id = msg_data.get("user_id")
                message = msg_data.get("message", "")
                name = msg_data.get("name", f"user_{user_id}")

                try:
                    result = client.start_chat(
                        user_id=user_id,
                        event_id=event.id,
                        message=message,
                    )
                    meeting_data = result.get("data", {})
                    results.append({
                        "name": name,
                        "user_id": user_id,
                        "meeting_id": int(meeting_data.get("id", 0)),
                        "status": "sent",
                    })
                except Exception as e:
                    errors.append({
                        "name": name,
                        "user_id": user_id,
                        "error": str(e),
                        "status": "failed",
                    })

            return {
                "sent": results,
                "sent_count": len(results),
                "errors": errors,
                "error_count": len(errors),
            }
        except Exception as e:
            return {"error": str(e)}
