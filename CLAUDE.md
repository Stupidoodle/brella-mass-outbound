# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Brella Mass Outbound is a CLI tool for personalized mass outreach on the Brella event networking platform. It reverse-engineers Brella's internal API to fetch attendee profiles and send personalized chat messages at scale — replacing generic spam with context-aware, AI-generated introductions.

## Commands

**Important**: Always use `uv run` (never bare `python` or `python3`). **NEVER** manually create or edit `pyproject.toml` — always use uv commands (`uv init`, `uv add <package>`, `uv add --group dev <package>`).

### Setup & Dependencies
```bash
uv sync                           # Install all dependencies
uv run pre-commit install         # Install git hooks
make setup                        # Full setup: deps + hooks
uv add <package>                  # Add a new dependency
```

### Running the CLI
```bash
uv run brella --help                                    # Show all commands
uv run brella attendees list --event <slug>             # List attendees
uv run brella attendees show --event <slug> --id <id>   # Show attendee profile
uv run brella campaign run --event <slug> --dry-run     # Dry-run campaign
uv run brella campaign run --event <slug>               # Execute campaign
```

### Running Tests
```bash
make test                          # Run all tests
uv run pytest tests/path/to/test_file.py::TestClass::test_name  # Single test
```

### Linting & Formatting
```bash
make lint                          # Ruff linter
make lint-fix                      # Ruff linter with auto-fix
make format                        # Ruff format + lint fix
make typecheck                     # Mypy type checking
make pre-commit                    # Run all pre-commit hooks on all files
```

## Architecture

### Layered DDD (Hexagonal / Ports & Adapters)

The codebase follows Domain-Driven Design with clear layer separation under `src/brella_outbound/`:

- **`domain/`** — Pure business logic, no framework dependencies
  - `models/` — Domain dataclasses (Attendee, Event, Campaign, OutreachMessage)
  - `ports/` — Abstract interfaces (BrellaApiPort, MessageGeneratorPort, LoggerPort)
  - `services/` — Domain services (OutreachService — filtering, dedup, personalization logic)

- **`application/`** — Use cases and orchestration
  - `services/` — Application services (CampaignService — runs the full outreach pipeline)

- **`infrastructure/`** — Concrete implementations of ports
  - `brella/` — Brella API client (httpx-based, reverse-engineered endpoints)
  - `llm/` — Message generators (Claude API, OpenAI API, template-based fallback)
  - `observability/` — Structured logging (structlog)

- **`core/`** — Cross-cutting concerns
  - `config.py` — Pydantic Settings with .env support

- **`cli/`** — Typer CLI entry point

### Key Patterns

**Composition Root (`bootstrap.py`)**: All dependency wiring happens here. The CLI calls `Bootstrap.build()` to get a fully-wired `Container` with all services.

**Ports & Adapters**: Every external dependency (Brella API, LLM APIs) is an abstract interface in `domain/ports/`. Infrastructure provides concrete implementations. This makes testing easy (swap with fakes).

**Message Generation Strategy**: Three interchangeable generators:
1. `ClaudeGenerator` — Uses Claude API for highly personalized messages
2. `OpenAIGenerator` — Uses OpenAI API as alternative
3. `TemplateGenerator` — Uses Jinja2 templates with variable substitution (no API key needed)

### Brella API (Reverse-Engineered)

Base URL: `https://api.brella.io/api`

| Action | Method | Endpoint |
|---|---|---|
| Sign in | POST | `/auth/sign_in` |
| List attendees | GET | `/events/:eventSlug/attendees` |
| Get attendee | GET | `/events/:eventSlug/attendees/:attendeeId` |
| My profile | GET | `/me/events/:eventSlug/me_attendee` |
| Start chat | POST | `me/meetings/start_chat` |
| Suggest meeting | POST | `me/meetings/suggest` |
| Search | GET | `/me/events/:eventSlug/search` |
| Chat messages | GET | `/me/chat_conversations/:id/chat_messages` |

Auth is session-based (cookie). The tool extracts auth tokens from browser session or login credentials.

### Testing

- **Unit tests** (`tests/unit/`): Use fake implementations. No external dependencies needed.
- **Integration tests** (`tests/integration/`): Hit real Brella API. Marked with `@pytest.mark.integration`.

### Configuration

Settings loaded via Pydantic Settings (`core/config.py`) with priority: env vars > .env file. Set `LLM_PROVIDER=claude|openai|template` to choose message generation strategy.

## Code Style

- Python 3.14, line length 88
- Ruff for linting (rules: E, F, C, D, B, I, Q, COM812) and formatting
- Double quotes, trailing commas enforced
- Imports: third-party first, then first-party (`brella_outbound.*`), separated by blank line
- Docstrings required (Google style, per ruff D rules)

## Python 3.14 — CRITICAL RULES

### UUID (stdlib `uuid`)
All UUID versions are in the standard library — **NEVER** use third-party UUID packages:
- `uuid.uuid7()` — Unix timestamp + random, time-ordered ← preferred

### Type Hints
**ALWAYS** use inbuilt types. **NEVER** import from `typing` for these:
- `list[X]` not `List[X]`
- `dict[K, V]` not `Dict[K, V]`
- `X | Y` not `Union[X, Y]`
- `X | None` not `Optional[X]`

Still valid from typing: `Any`, `Literal`, `TypeVar`, `Protocol`, `TypedDict`, etc.

### Annotations & Forward References (PEP 649)
- **No** `from __future__ import annotations`
- **NEVER** use string-quoted type annotations — forward references just work natively
