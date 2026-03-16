"""Attendee discovery and filtering MCP tools."""

from typing import Any

from mcp.server.fastmcp import FastMCP

from brella_outbound.infrastructure.brella.brella_api_client import BrellaApiClient


def register_attendee_tools(mcp: FastMCP, client: BrellaApiClient) -> None:
    """Register attendee-related tools with the MCP server."""

    @mcp.tool()
    def get_my_profile(event_slug: str) -> dict[str, Any]:
        """Get your own attendee profile for an event.

        Args:
            event_slug: The Brella event slug (e.g. 'startsummitxhack2026').

        Returns:
            Your profile with name, title, company, interests, persona.
        """
        try:
            me = client.get_me_attendee(event_slug)
            return {
                "id": me.id,
                "user_id": me.user_id,
                "name": me.full_name,
                "title": me.company_title,
                "company": me.company_name,
                "persona": me.persona_name,
                "industry": me.industry_name,
                "function": me.function_name,
                "bio": me.pitch,
                "interests": me.interest_names,
                "linkedin": me.linkedin,
                "website": me.website,
            }
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    def list_attendees(
        event_slug: str,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """List attendees for an event with pagination.

        Args:
            event_slug: The Brella event slug.
            page: Page number (1-indexed).
            page_size: Results per page (max 120).

        Returns:
            Attendees list with pagination metadata.
        """
        try:
            attendees, meta = client.list_attendees(
                event_slug,
                page=page,
                page_size=min(page_size, 120),
            )
            return {
                "attendees": [
                    {
                        "id": a.id,
                        "user_id": a.user_id,
                        "name": a.full_name,
                        "title": a.company_title,
                        "company": a.company_name,
                        "persona": a.persona_name,
                        "industry": a.industry_name,
                        "interests": a.interest_names[:8],
                        "bio": (a.pitch or "")[:150],
                    }
                    for a in attendees
                ],
                "total_count": meta.get("total_count"),
                "total_pages": meta.get("total_pages"),
                "current_page": meta.get("current_page"),
            }
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    def filter_attendees(
        event_slug: str,
        persona_ids: list[int] | None = None,
        interest_ids: list[int] | None = None,
        industry_ids: list[int] | None = None,
        function_ids: list[int] | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """Filter attendees server-side by persona, interest, industry, or function.

        Use get_interest_catalog and get_event_info to find valid IDs.

        Args:
            event_slug: The Brella event slug.
            persona_ids: Filter by persona IDs (e.g. [18585] for Startup Founder).
            interest_ids: Filter by interest IDs (e.g. [861811] for AI).
            industry_ids: Filter by industry IDs.
            function_ids: Filter by function IDs.
            page: Page number (1-indexed).
            page_size: Results per page (max 120).

        Returns:
            Filtered attendees with pagination metadata.
        """
        try:
            attendees, meta = client.filter_attendees(
                event_slug,
                persona_ids=persona_ids,
                interest_ids=interest_ids,
                industry_ids=industry_ids,
                function_ids=function_ids,
                page=page,
                page_size=min(page_size, 120),
            )
            return {
                "attendees": [
                    {
                        "id": a.id,
                        "user_id": a.user_id,
                        "name": a.full_name,
                        "title": a.company_title,
                        "company": a.company_name,
                        "persona": a.persona_name,
                        "industry": a.industry_name,
                        "interests": a.interest_names[:8],
                        "bio": (a.pitch or "")[:150],
                    }
                    for a in attendees
                ],
                "total_count": meta.get("total_count"),
                "total_pages": meta.get("total_pages"),
                "current_page": meta.get("current_page"),
            }
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    def get_attendee_profile(
        event_slug: str,
        attendee_id: int,
    ) -> dict[str, Any]:
        """Get full profile for a specific attendee.

        Args:
            event_slug: The Brella event slug.
            attendee_id: The attendee's numeric ID.

        Returns:
            Full attendee profile with all details.
        """
        try:
            a = client.get_attendee(event_slug, attendee_id)
            return {
                "id": a.id,
                "user_id": a.user_id,
                "name": a.full_name,
                "title": a.company_title,
                "company": a.company_name,
                "persona": a.persona_name,
                "industry": a.industry_name,
                "function": a.function_name,
                "bio": a.pitch,
                "interests": a.interest_names,
                "linkedin": a.linkedin,
                "website": a.website,
                "image_url": a.image_url,
            }
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    def search_attendees(
        event_slug: str,
        query: str,
    ) -> dict[str, Any]:
        """Search attendees by name, title, or company.

        Args:
            event_slug: The Brella event slug.
            query: Search query string.

        Returns:
            Matching attendees.
        """
        try:
            results = client.search_attendees(event_slug, query)
            return {
                "results": [
                    {
                        "id": a.id,
                        "user_id": a.user_id,
                        "name": a.full_name,
                        "title": a.company_title,
                        "company": a.company_name,
                        "persona": a.persona_name,
                    }
                    for a in results
                ],
                "count": len(results),
            }
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    def get_event_info(event_slug: str) -> dict[str, Any]:
        """Get event details.

        Args:
            event_slug: The Brella event slug.

        Returns:
            Event ID, name, and slug.
        """
        try:
            event = client.get_event(event_slug)
            return {
                "id": event.id,
                "slug": event.slug,
                "name": event.name,
            }
        except Exception as e:
            return {"error": str(e)}
