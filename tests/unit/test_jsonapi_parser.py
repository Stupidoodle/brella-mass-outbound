"""Tests for the JSON:API parser."""

from brella_outbound.infrastructure.brella.jsonapi_parser import JsonApiParser


def _make_attendee_response() -> dict:
    """Build a realistic JSON:API attendee response (based on reverse engineering)."""
    return {
        "data": [
            {
                "id": "10567312",
                "type": "attendee",
                "attributes": {
                    "pitch": "Building the next generation of Voice AI.",
                    "joined-at": "2026-02-10T14:31:40.380Z",
                    "skip-networking": False,
                    "first-name": "Philip",
                    "last-name": "Benson",
                    "company-title": "Co-Founder & CEO",
                    "company-name": "NAIRON",
                    "status": "joined",
                    "user-id": "1620754",
                    "bookmarked": False,
                },
                "relationships": {
                    "persona": {"data": {"id": "18585", "type": "persona"}},
                    "function": {"data": {"id": "22831", "type": "function"}},
                    "industry": {"data": {"id": "30321", "type": "industry"}},
                    "user": {"data": {"id": "1620754", "type": "user"}},
                    "event": {"data": {"id": "9474", "type": "event"}},
                    "group": {"data": {"id": "32872", "type": "attendee-group"}},
                    "selected-interests": {
                        "data": [
                            {"id": "100", "type": "selected-interest"},
                            {"id": "101", "type": "selected-interest"},
                        ],
                    },
                    "latest-meeting": {"data": None},
                },
            },
        ],
        "included": [
            {
                "id": "1620754",
                "type": "user",
                "attributes": {
                    "first-name": "Philip",
                    "last-name": "Benson",
                    "company-title": "Co-Founder & CEO",
                    "company-name": "NAIRON",
                    "image-url": "https://example.com/philip.jpg",
                    "cover-photo-url": "https://example.com/philip-cover.jpg",
                    "linkedin": "https://linkedin.com/in/philip-benson",
                    "website": "https://nairon.ai/",
                },
            },
            {
                "id": "18585",
                "type": "persona",
                "attributes": {"name": "Startup (Founder)", "position": 1},
            },
            {
                "id": "22831",
                "type": "function",
                "attributes": {"name": "Founder / Co-Founder", "position": 1},
            },
            {
                "id": "30321",
                "type": "industry",
                "attributes": {"name": "Enterprise Software & SaaS", "position": 15},
            },
            {
                "id": "32872",
                "type": "attendee-group",
                "attributes": {
                    "name": "Startups",
                    "attendance-type": "in_person",
                    "allows-networking": True,
                    "attendees-count": 181,
                },
            },
            {
                "id": "861811",
                "type": "interest",
                "attributes": {"name": "Artificial Intelligence", "position": 3},
            },
            {
                "id": "861806",
                "type": "interest",
                "attributes": {"name": "Backend Development", "position": 1},
            },
            {
                "id": "1",
                "type": "intent",
                "attributes": {
                    "selection-label": "Network about this",
                    "match-label": "Networker",
                    "profile-label": "Networking about",
                    "position": 1,
                },
            },
            {
                "id": "100",
                "type": "selected-interest",
                "relationships": {
                    "selector": {"data": {"id": "10567312", "type": "registrant"}},
                    "interest": {"data": {"id": "861811", "type": "interest"}},
                    "intent": {"data": {"id": "1", "type": "intent"}},
                },
            },
            {
                "id": "101",
                "type": "selected-interest",
                "relationships": {
                    "selector": {"data": {"id": "10567312", "type": "registrant"}},
                    "interest": {"data": {"id": "861806", "type": "interest"}},
                    "intent": {"data": {"id": "1", "type": "intent"}},
                },
            },
        ],
        "meta": {
            "total_count": 2420,
            "total_pages": 1210,
            "current_page": 1,
        },
    }


class TestJsonApiParser:
    """Tests for JsonApiParser."""

    def test_parse_attendee_basic_attributes(self) -> None:
        """Test that basic attendee attributes are parsed correctly."""
        response = _make_attendee_response()
        parser = JsonApiParser()
        parser.index_included(response["included"])
        attendee = parser.parse_attendee(response["data"][0], "test-event")

        assert attendee.id == 10567312
        assert attendee.user_id == 1620754
        assert attendee.first_name == "Philip"
        assert attendee.last_name == "Benson"
        assert attendee.company_title == "Co-Founder & CEO"
        assert attendee.company_name == "NAIRON"
        assert attendee.pitch == "Building the next generation of Voice AI."
        assert attendee.status == "joined"
        assert attendee.event_slug == "test-event"

    def test_parse_attendee_resolved_persona(self) -> None:
        """Test persona is resolved from included data."""
        response = _make_attendee_response()
        parser = JsonApiParser()
        parser.index_included(response["included"])
        attendee = parser.parse_attendee(response["data"][0], "test-event")

        assert attendee.persona is not None
        assert attendee.persona.name == "Startup (Founder)"
        assert attendee.persona.id == 18585
        assert attendee.persona_name == "Startup (Founder)"

    def test_parse_attendee_resolved_function(self) -> None:
        """Test function is resolved from included data."""
        response = _make_attendee_response()
        parser = JsonApiParser()
        parser.index_included(response["included"])
        attendee = parser.parse_attendee(response["data"][0], "test-event")

        assert attendee.function is not None
        assert attendee.function.name == "Founder / Co-Founder"
        assert attendee.function_name == "Founder / Co-Founder"

    def test_parse_attendee_resolved_industry(self) -> None:
        """Test industry is resolved from included data."""
        response = _make_attendee_response()
        parser = JsonApiParser()
        parser.index_included(response["included"])
        attendee = parser.parse_attendee(response["data"][0], "test-event")

        assert attendee.industry is not None
        assert attendee.industry.name == "Enterprise Software & SaaS"

    def test_parse_attendee_resolved_group(self) -> None:
        """Test attendee group is resolved from included data."""
        response = _make_attendee_response()
        parser = JsonApiParser()
        parser.index_included(response["included"])
        attendee = parser.parse_attendee(response["data"][0], "test-event")

        assert attendee.group is not None
        assert attendee.group.name == "Startups"
        assert attendee.group.attendance_type == "in_person"
        assert attendee.group.attendees_count == 181

    def test_parse_attendee_user_social_data(self) -> None:
        """Test user sideload provides social/image data."""
        response = _make_attendee_response()
        parser = JsonApiParser()
        parser.index_included(response["included"])
        attendee = parser.parse_attendee(response["data"][0], "test-event")

        assert attendee.linkedin == "https://linkedin.com/in/philip-benson"
        assert attendee.website == "https://nairon.ai/"
        assert attendee.image_url == "https://example.com/philip.jpg"
        assert attendee.cover_photo_url == "https://example.com/philip-cover.jpg"

    def test_parse_attendee_selected_interests(self) -> None:
        """Test selected interests are resolved with interest names."""
        response = _make_attendee_response()
        parser = JsonApiParser()
        parser.index_included(response["included"])
        attendee = parser.parse_attendee(response["data"][0], "test-event")

        assert len(attendee.selected_interests) == 2
        assert attendee.selected_interests[0].interest_id == 861811
        assert attendee.selected_interests[0].intent_id == 1
        assert "Artificial Intelligence" in attendee.interest_names
        assert "Backend Development" in attendee.interest_names

    def test_parse_attendee_full_name(self) -> None:
        """Test full_name property."""
        response = _make_attendee_response()
        parser = JsonApiParser()
        parser.index_included(response["included"])
        attendee = parser.parse_attendee(response["data"][0], "test-event")

        assert attendee.full_name == "Philip Benson"

    def test_parse_attendee_display_info(self) -> None:
        """Test display_info property."""
        response = _make_attendee_response()
        parser = JsonApiParser()
        parser.index_included(response["included"])
        attendee = parser.parse_attendee(response["data"][0], "test-event")

        assert "Philip Benson" in attendee.display_info
        assert "Co-Founder & CEO" in attendee.display_info
        assert "NAIRON" in attendee.display_info

    def test_parse_attendee_missing_relationships(self) -> None:
        """Test parsing works when relationships are missing from included."""
        response = _make_attendee_response()
        response["included"] = []  # No sideloaded data
        parser = JsonApiParser()
        parser.index_included(response["included"])
        attendee = parser.parse_attendee(response["data"][0], "test-event")

        assert attendee.id == 10567312
        assert attendee.first_name == "Philip"
        assert attendee.persona is None
        assert attendee.function is None
        assert attendee.industry is None
        assert attendee.group is None
        assert attendee.interest_names == []


class TestParseInterestCategories:
    """Tests for interest catalog parsing."""

    def _make_interest_response(self) -> tuple[list[dict], list[dict]]:
        """Build a realistic interest catalog response."""
        data = [
            {
                "id": "861959",
                "type": "interest",
                "attributes": {"name": "Role", "position": 1, "event-id": 9474},
                "relationships": {
                    "children": {
                        "data": [
                            {"id": "861960", "type": "interest"},
                            {"id": "861961", "type": "interest"},
                        ],
                    },
                    "intent-pairs": {"data": []},
                },
            },
            {
                "id": "861795",
                "type": "interest",
                "attributes": {
                    "name": "Field of Study",
                    "position": 2,
                    "event-id": 9474,
                },
                "relationships": {
                    "children": {
                        "data": [
                            {"id": "861811", "type": "interest"},
                        ],
                    },
                    "intent-pairs": {
                        "data": [{"id": "1", "type": "intent-pair"}],
                    },
                },
            },
        ]
        included = [
            {
                "id": "861960",
                "type": "interest",
                "attributes": {"name": "Startup", "position": 1},
            },
            {
                "id": "861961",
                "type": "interest",
                "attributes": {"name": "Investor", "position": 2},
            },
            {
                "id": "861811",
                "type": "interest",
                "attributes": {
                    "name": "Artificial Intelligence",
                    "position": 3,
                },
            },
            {
                "id": "1",
                "type": "intent-pair",
                "attributes": {
                    "title": "Networking",
                    "position": 1,
                    "slug": "networking",
                },
                "relationships": {
                    "intents": {"data": [{"id": "1", "type": "intent"}]},
                },
            },
            {
                "id": "1",
                "type": "intent",
                "attributes": {
                    "selection-label": "Network about this",
                    "match-label": "Networker",
                    "profile-label": "Networking about",
                    "position": 1,
                },
            },
        ]
        return data, included

    def test_parse_categories(self) -> None:
        """Test category parsing from interest catalog."""
        data, included = self._make_interest_response()
        parser = JsonApiParser()
        categories, interests, pairs, intents = parser.parse_interest_categories(
            data,
            included,
        )

        assert len(categories) == 2
        assert categories[0].name == "Role"
        assert categories[0].event_id == 9474
        assert categories[1].name == "Field of Study"

    def test_parse_child_interests(self) -> None:
        """Test child interests are resolved from categories."""
        data, included = self._make_interest_response()
        parser = JsonApiParser()
        _, interests, _, _ = parser.parse_interest_categories(data, included)

        names = {i.name for i in interests}
        assert "Startup" in names
        assert "Investor" in names
        assert "Artificial Intelligence" in names
        assert len(interests) == 3

    def test_parse_intent_pairs(self) -> None:
        """Test intent pairs are parsed from included."""
        data, included = self._make_interest_response()
        parser = JsonApiParser()
        _, _, pairs, _ = parser.parse_interest_categories(data, included)

        assert len(pairs) == 1
        assert pairs[0].title == "Networking"
        assert pairs[0].slug == "networking"

    def test_parse_intents(self) -> None:
        """Test intents are parsed from included."""
        data, included = self._make_interest_response()
        parser = JsonApiParser()
        _, _, _, intents = parser.parse_interest_categories(data, included)

        assert len(intents) == 1
        assert intents[0].selection_label == "Network about this"
        assert intents[0].match_label == "Networker"
