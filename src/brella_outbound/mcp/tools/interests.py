"""Interest catalog MCP tools — for ICP research and targeting."""

from typing import Any

from mcp.server.fastmcp import FastMCP

from brella_outbound.infrastructure.brella.brella_api_client import BrellaApiClient
from brella_outbound.infrastructure.brella.jsonapi_parser import JsonApiParser


def register_interest_tools(mcp: FastMCP, client: BrellaApiClient) -> None:
    """Register interest catalog tools with the MCP server."""

    @mcp.tool()
    def get_interest_catalog(event_slug: str) -> dict[str, Any]:
        """Get the full interest taxonomy for an event.

        Returns categories (Role, Field of Study, Industry Sector, etc.)
        with their child interests and IDs. Use these IDs for filtering.

        Args:
            event_slug: The Brella event slug.

        Returns:
            Categories with child interests, intent pairs, and intents.
        """
        try:
            raw = client.get_interests(event_slug)
            parser = JsonApiParser()
            categories, interests, intent_pairs, intents = (
                parser.parse_interest_categories(
                    raw.get("data", []),
                    raw.get("included", []),
                )
            )

            # Group interests by category
            by_category: dict[int, list[dict]] = {}
            for i in interests:
                by_category.setdefault(i.category_id, []).append({
                    "id": i.id,
                    "name": i.name,
                })

            return {
                "categories": [
                    {
                        "id": c.id,
                        "name": c.name,
                        "interests": by_category.get(c.id, []),
                    }
                    for c in categories
                ],
                "intent_pairs": [
                    {"id": p.id, "title": p.title, "slug": p.slug}
                    for p in intent_pairs
                ],
                "intents": [
                    {
                        "id": i.id,
                        "label": i.selection_label,
                        "match_label": i.match_label,
                    }
                    for i in intents
                ],
                "total_interests": len(interests),
            }
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    def find_common_interests(
        event_slug: str,
        attendee_id: int,
    ) -> dict[str, Any]:
        """Find interests you share with a specific attendee.

        Args:
            event_slug: The Brella event slug.
            attendee_id: The attendee's numeric ID.

        Returns:
            Common interests, your interests, their interests.
        """
        try:
            me = client.get_me_attendee(event_slug)
            them = client.get_attendee(event_slug, attendee_id)

            my_set = {i.lower() for i in me.interest_names}
            common = [i for i in them.interest_names if i.lower() in my_set]

            return {
                "attendee": them.full_name,
                "common_interests": common,
                "common_count": len(common),
                "your_interests": me.interest_names,
                "their_interests": them.interest_names,
            }
        except Exception as e:
            return {"error": str(e)}
