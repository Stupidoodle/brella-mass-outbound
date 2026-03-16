"""JSON:API response parser for Brella API responses.

Brella uses the JSON:API spec with sideloaded `included` data.
This parser resolves relationships and hydrates domain models.
"""

from typing import Any

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
from brella_outbound.domain.models.event import Event


class JsonApiParser:
    """Parses JSON:API responses into domain models."""

    def __init__(self) -> None:
        self._included_index: dict[str, dict[str, dict]] = {}

    def index_included(
        self,
        included: list[dict],
        *,
        merge: bool = True,
    ) -> None:
        """Build/merge a lookup index from the `included` array.

        Args:
            included: The JSON:API `included` sideload array.
            merge: If True, merge into existing index. If False, replace.
        """
        if not merge:
            self._included_index = {}
        for item in included:
            item_type = item["type"]
            item_id = str(item["id"])
            self._included_index.setdefault(item_type, {})[item_id] = item

    def resolve(self, ref_type: str, ref_id: str) -> dict | None:
        """Resolve a relationship reference to its included data."""
        return self._included_index.get(ref_type, {}).get(str(ref_id))

    def parse_event(self, data: dict) -> Event:
        """Parse event from JSON:API data."""
        attrs = data.get("attributes", {})
        return Event(
            id=int(data["id"]),
            slug=attrs.get("slug", ""),
            name=attrs.get("name", ""),
        )

    def parse_attendee(
        self,
        data: dict,
        event_slug: str,
    ) -> Attendee:
        """Parse attendee from JSON:API data with resolved relationships.

        Args:
            data: A single JSON:API resource object (type=attendee).
            event_slug: The event slug for context.

        Returns:
            Fully hydrated Attendee domain model.
        """
        attrs = data.get("attributes", {})
        rels = data.get("relationships", {})

        # Resolve user sideload for image/social
        user_ref = _rel_ref(rels, "user")
        user_data = self.resolve("user", user_ref["id"]) if user_ref else None
        user_attrs = (user_data or {}).get("attributes", {})

        # Resolve reference data
        persona_ref = _rel_ref(rels, "persona")
        function_ref = _rel_ref(rels, "function")
        industry_ref = _rel_ref(rels, "industry")
        group_ref = _rel_ref(rels, "group")

        persona = self._resolve_persona(persona_ref)
        function = self._resolve_function(function_ref)
        industry = self._resolve_industry(industry_ref)
        group = self._resolve_group(group_ref)

        # Resolve selected interests
        si_refs = _rel_refs(rels, "selected-interests")
        selected_interests = []
        interest_names = []
        for si_ref in si_refs:
            si = self._resolve_selected_interest(si_ref, int(data["id"]))
            if si:
                selected_interests.append(si)
                # Resolve the interest name
                interest_data = self.resolve("interest", str(si.interest_id))
                if interest_data:
                    name = interest_data.get("attributes", {}).get("name", "")
                    if name and name not in interest_names:
                        interest_names.append(name)

        return Attendee(
            id=int(data["id"]),
            user_id=int(attrs.get("user-id", 0)),
            event_slug=event_slug,
            first_name=attrs.get("first-name", ""),
            last_name=attrs.get("last-name", ""),
            company_title=attrs.get("company-title"),
            company_name=attrs.get("company-name"),
            pitch=attrs.get("pitch"),
            status=attrs.get("status", "joined"),
            persona_id=int(persona_ref["id"]) if persona_ref else None,
            function_id=int(function_ref["id"]) if function_ref else None,
            industry_id=int(industry_ref["id"]) if industry_ref else None,
            group_id=int(group_ref["id"]) if group_ref else None,
            image_url=user_attrs.get("image-url"),
            cover_photo_url=user_attrs.get("cover-photo-url"),
            linkedin=user_attrs.get("linkedin"),
            website=user_attrs.get("website"),
            persona=persona,
            function=function,
            industry=industry,
            group=group,
            selected_interests=selected_interests,
            interest_names=interest_names,
        )

    def parse_interest_categories(
        self,
        data: list[dict],
        included: list[dict],
    ) -> tuple[list[InterestCategory], list[Interest], list[IntentPair], list[Intent]]:
        """Parse full interest catalog from the /events/:slug/interests endpoint.

        Returns:
            Tuple of (categories, interests, intent_pairs, intents).
        """
        self.index_included(included)

        categories = []
        interests = []
        intent_pairs = []
        intents = []

        seen_pairs: set[int] = set()
        seen_intents: set[int] = set()

        for cat_data in data:
            cat_attrs = cat_data.get("attributes", {})
            cat = InterestCategory(
                id=int(cat_data["id"]),
                name=cat_attrs.get("name", ""),
                event_id=int(cat_attrs.get("event-id", 0)),
                position=int(cat_attrs.get("position", 0)),
            )
            categories.append(cat)

            # Parse child interests
            children_refs = _rel_refs(
                cat_data.get("relationships", {}),
                "children",
            )
            for child_ref in children_refs:
                child_data = self.resolve("interest", child_ref["id"])
                if child_data:
                    child_attrs = child_data.get("attributes", {})
                    interests.append(Interest(
                        id=int(child_data["id"]),
                        name=child_attrs.get("name", ""),
                        category_id=cat.id,
                        position=int(child_attrs.get("position", 0)),
                    ))

        # Parse intent pairs and intents from included
        for item in included:
            if item["type"] == "intent-pair":
                pair_id = int(item["id"])
                if pair_id not in seen_pairs:
                    pair_attrs = item.get("attributes", {})
                    intent_pairs.append(IntentPair(
                        id=pair_id,
                        title=pair_attrs.get("title", ""),
                        slug=pair_attrs.get("slug", ""),
                        position=int(pair_attrs.get("position", 0)),
                    ))
                    seen_pairs.add(pair_id)

            elif item["type"] == "intent":
                intent_id = int(item["id"])
                if intent_id not in seen_intents:
                    intent_attrs = item.get("attributes", {})
                    intents.append(Intent(
                        id=intent_id,
                        selection_label=intent_attrs.get("selection-label", ""),
                        match_label=intent_attrs.get("match-label", ""),
                        profile_label=intent_attrs.get("profile-label", ""),
                        position=int(intent_attrs.get("position", 0)),
                    ))
                    seen_intents.add(intent_id)

        return categories, interests, intent_pairs, intents

    def _resolve_persona(self, ref: dict[str, Any] | None) -> Persona | None:
        """Resolve persona from included data."""
        if not ref:
            return None
        data = self.resolve("persona", ref["id"])
        if not data:
            return None
        attrs = data.get("attributes", {})
        return Persona(
            id=int(data["id"]),
            name=attrs.get("name", ""),
            position=int(attrs.get("position", 0)),
        )

    def _resolve_function(self, ref: dict[str, Any] | None) -> Function | None:
        """Resolve function from included data."""
        if not ref:
            return None
        data = self.resolve("function", ref["id"])
        if not data:
            return None
        attrs = data.get("attributes", {})
        return Function(
            id=int(data["id"]),
            name=attrs.get("name", ""),
            position=int(attrs.get("position", 0)),
        )

    def _resolve_industry(self, ref: dict[str, Any] | None) -> Industry | None:
        """Resolve industry from included data."""
        if not ref:
            return None
        data = self.resolve("industry", ref["id"])
        if not data:
            return None
        attrs = data.get("attributes", {})
        return Industry(
            id=int(data["id"]),
            name=attrs.get("name", ""),
            position=int(attrs.get("position", 0)),
        )

    def _resolve_group(self, ref: dict[str, Any] | None) -> AttendeeGroup | None:
        """Resolve attendee group from included data."""
        if not ref:
            return None
        data = self.resolve("attendee-group", ref["id"])
        if not data:
            return None
        attrs = data.get("attributes", {})
        return AttendeeGroup(
            id=int(data["id"]),
            name=attrs.get("name", ""),
            attendance_type=attrs.get("attendance-type", "in_person"),
            allows_networking=attrs.get("allows-networking", True),
            attendees_count=int(attrs.get("attendees-count", 0)),
        )

    def _resolve_selected_interest(
        self,
        ref: dict[str, Any],
        attendee_id: int,
    ) -> SelectedInterest | None:
        """Resolve selected-interest junction from included data."""
        data = self.resolve("selected-interest", ref["id"])
        if not data:
            return None
        si_rels = data.get("relationships", {})
        interest_ref = _rel_ref(si_rels, "interest")
        intent_ref = _rel_ref(si_rels, "intent")
        if not interest_ref or not intent_ref:
            return None
        return SelectedInterest(
            id=int(data["id"]),
            attendee_id=attendee_id,
            interest_id=int(interest_ref["id"]),
            intent_id=int(intent_ref["id"]),
        )


def _rel_ref(rels: dict, key: str) -> dict | None:
    """Extract a single relationship reference {id, type}."""
    rel = rels.get(key, {})
    data = rel.get("data")
    if isinstance(data, dict) and "id" in data:
        return data
    return None


def _rel_refs(rels: dict, key: str) -> list[dict]:
    """Extract a list of relationship references [{id, type}, ...]."""
    rel = rels.get(key, {})
    data = rel.get("data")
    if isinstance(data, list):
        return [d for d in data if isinstance(d, dict) and "id" in d]
    return []
