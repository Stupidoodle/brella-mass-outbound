"""Brella API client — reverse-engineered REST endpoints (JSON:API format)."""

import time

import httpx

from brella_outbound.core.config import Settings
from brella_outbound.domain.models.attendee import Attendee
from brella_outbound.domain.models.event import Event
from brella_outbound.domain.ports.brella_api_port import BrellaApiPort
from brella_outbound.domain.ports.logger_port import LoggerPort
from brella_outbound.infrastructure.brella.jsonapi_parser import JsonApiParser


class BrellaApiClient(BrellaApiPort):
    """HTTP client for Brella's internal JSON:API.

    Auth is token-based. Provide either:
    - auth_token: extracted from browser localStorage['authHeaders']
    - email + password: to authenticate via /auth/sign_in
    """

    def __init__(
        self,
        settings: Settings,
        logger: LoggerPort,
    ) -> None:
        self._logger = logger
        self._settings = settings
        self._rate_limit_delay = settings.BRELLA_RATE_LIMIT_DELAY
        self._parser = JsonApiParser()
        self._client = httpx.Client(
            base_url=settings.BRELLA_API_BASE_URL,
            timeout=30.0,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )

        if settings.BRELLA_AUTH_TOKEN:
            # Auth token is the full JSON authHeaders from localStorage
            # Parse it if it looks like JSON, otherwise use as bearer
            token = settings.BRELLA_AUTH_TOKEN
            if token.startswith("{"):
                import json

                headers = json.loads(token)
                self._client.headers.update(headers)
            else:
                self._client.headers["Authorization"] = f"Bearer {token}"
        elif settings.BRELLA_EMAIL and settings.BRELLA_PASSWORD:
            self._authenticate(settings.BRELLA_EMAIL, settings.BRELLA_PASSWORD)
        else:
            msg = "Set BRELLA_AUTH_TOKEN or BRELLA_EMAIL+BRELLA_PASSWORD in .env"
            raise ValueError(msg)

    def _authenticate(self, email: str, password: str) -> None:
        """Authenticate via Brella sign-in endpoint."""
        resp = self._client.post(
            "/auth/sign_in",
            json={"email": email, "password": password},
        )
        resp.raise_for_status()

        # DeviseTokenAuth returns auth headers in the response
        for header in ("access-token", "client", "uid", "token-type"):
            if header in resp.headers:
                self._client.headers[header] = resp.headers[header]

        self._logger.info("authenticated with brella", email=email)

    def _rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        time.sleep(self._rate_limit_delay)

    def get_event(self, event_slug: str) -> Event:
        """Fetch event details by slug."""
        self._rate_limit()
        resp = self._client.get(f"/events/{event_slug}")
        resp.raise_for_status()
        data = resp.json()
        event_data = data.get("data", data)
        attrs = event_data.get("attributes", event_data)
        return Event(
            id=int(event_data.get("id", 0)),
            slug=event_slug,
            name=attrs.get("name", event_slug),
        )

    def _ensure_interest_catalog(self, event_slug: str) -> None:
        """Pre-load interest catalog into parser index if not loaded yet.

        The me_attendee endpoint returns selected-interest junctions but
        does NOT include the interest objects themselves.  We load them
        from the interests endpoint once so the parser can resolve names.
        """
        if self._parser.resolve("interest", "0") is not None:
            return  # already loaded (cheap sentinel check)
        interests_body = self.get_interests(event_slug)
        # Index all included items (child interests, intents, pairs)
        included = interests_body.get("included", [])
        # Also add top-level categories as interests so they're resolvable
        for cat in interests_body.get("data", []):
            included.append(cat)
        self._parser.index_included(included)

    def get_me_attendee(self, event_slug: str) -> Attendee:
        """Fetch the authenticated user's attendee profile."""
        self._ensure_interest_catalog(event_slug)
        self._rate_limit()
        resp = self._client.get(f"/me/events/{event_slug}/me_attendee")
        resp.raise_for_status()
        body = resp.json()
        # Merge included (preserves existing interest catalog in index)
        self._parser.index_included(body.get("included", []))
        return self._parser.parse_attendee(body["data"], event_slug)

    def list_attendees(
        self,
        event_slug: str,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Attendee], dict]:
        """List attendees for an event with pagination.

        Returns:
            Tuple of (attendees, meta) where meta contains pagination info.
        """
        self._rate_limit()
        resp = self._client.get(
            f"/events/{event_slug}/attendees",
            params={"page[number]": page, "page[size]": page_size},
        )
        resp.raise_for_status()
        body = resp.json()

        self._parser.index_included(body.get("included", []))
        attendees_data = body.get("data", [])
        attendees = [
            self._parser.parse_attendee(a, event_slug)
            for a in attendees_data
        ]

        meta = body.get("meta", {})
        return attendees, meta

    def list_all_attendees(self, event_slug: str) -> list[Attendee]:
        """Fetch all attendees across all pages."""
        all_attendees: list[Attendee] = []
        page = 1
        page_size = 120

        while True:
            batch, meta = self.list_attendees(
                event_slug,
                page=page,
                page_size=page_size,
            )
            if not batch:
                break
            all_attendees.extend(batch)
            total = meta.get("total_count", "?")
            self._logger.info(
                "fetched attendees page",
                page=page,
                batch_size=len(batch),
                total_fetched=len(all_attendees),
                total_available=total,
            )
            total_pages = meta.get("total_pages", page)
            if page >= total_pages:
                break
            page += 1

        return all_attendees

    def get_attendee(self, event_slug: str, attendee_id: int) -> Attendee:
        """Fetch a single attendee by ID."""
        self._rate_limit()
        resp = self._client.get(
            f"/events/{event_slug}/attendees/{attendee_id}",
        )
        resp.raise_for_status()
        body = resp.json()
        self._parser.index_included(body.get("included", []))
        return self._parser.parse_attendee(body["data"], event_slug)

    def search_attendees(
        self,
        event_slug: str,
        query: str,
    ) -> list[Attendee]:
        """Search attendees by name, title, or company."""
        self._rate_limit()
        resp = self._client.get(
            f"/me/events/{event_slug}/search",
            params={"q": query},
        )
        resp.raise_for_status()
        body = resp.json()
        self._parser.index_included(body.get("included", []))
        results = body.get("data", [])
        return [
            self._parser.parse_attendee(a, event_slug)
            for a in results
            if a.get("type") == "attendee"
        ]

    def get_interests(
        self,
        event_slug: str,
    ) -> dict:
        """Fetch the full interest catalog for an event.

        Returns:
            Raw JSON:API response with categories, interests, intents.
        """
        self._rate_limit()
        resp = self._client.get(f"/events/{event_slug}/interests")
        resp.raise_for_status()
        return resp.json()

    def start_chat(
        self,
        user_id: int,
        event_id: int,
        message: str,
    ) -> dict:
        """Send a chat request to start a conversation.

        Args:
            user_id: Target user's ID (not attendee ID).
            event_id: The event's numeric ID.
            message: Intro message (max 500 chars).

        Returns:
            API response data.
        """
        self._rate_limit()
        max_len = self._settings.CAMPAIGN_MESSAGE_MAX_LENGTH
        # Ensure proper message encoding for the wire format
        _sig = "\n\n\U0001f4e8 via github.com/Stupidoodle/brella-mass-outbound"
        _body = (message + _sig)[:max_len]
        resp = self._client.post(
            "/me/meetings/start_chat",
            json={
                "meeting": {
                    "user_id": user_id,
                    "event_id": event_id,
                    "message": _body,
                },
            },
        )
        resp.raise_for_status()
        return resp.json()

    def filter_attendees(
        self,
        event_slug: str,
        *,
        persona_ids: list[int] | None = None,
        interest_ids: list[int] | None = None,
        industry_ids: list[int] | None = None,
        function_ids: list[int] | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Attendee], dict]:
        """Server-side filtered attendee listing.

        Uses POST /events/:slug/attendees with flat filter body.
        """
        self._rate_limit()
        body: dict = {
            "page": {"number": page, "size": page_size},
        }
        if persona_ids:
            body["persona_ids"] = persona_ids
        if interest_ids:
            body["interest_ids"] = interest_ids
        if industry_ids:
            body["industry_ids"] = industry_ids
        if function_ids:
            body["function_ids"] = function_ids

        resp = self._client.post(
            f"/events/{event_slug}/attendees",
            json=body,
        )
        resp.raise_for_status()
        response_body = resp.json()

        self._parser.index_included(response_body.get("included", []))
        attendees = [
            self._parser.parse_attendee(a, event_slug)
            for a in response_body.get("data", [])
        ]
        meta = response_body.get("meta", {})
        return attendees, meta

    def poke(self, meeting_id: int, message: str) -> dict:
        """Send a follow-up nudge for an unanswered chat request.

        Args:
            meeting_id: The meeting ID from start_chat response.
            message: The nudge message.

        Returns:
            API response data.
        """
        self._rate_limit()
        resp = self._client.patch(
            f"/me/meetings/{meeting_id}/poke",
            json={"meeting": {"message": message}},
        )
        resp.raise_for_status()
        return resp.json()

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()
