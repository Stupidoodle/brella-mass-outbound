# brella-mass-outbound

Personalized mass outreach for [Brella](https://brella.io) event networking — because nobody deserves generic spam.

## Why this exists

I got a cold outreach message on Brella before START Summit 2026 that was so obviously mass-sent it hurt. Zero personalization, zero overlap with my interests, just pure copy-paste spam to all 2400+ attendees. The sender's networking interests literally had no overlap with mine.

So I built a tool that does mass outreach *properly* — by actually reading each person's profile, finding shared interests, and generating messages that reference their work. If you're going to reach out to 600 people, at least make it personal.

## What it does

- **Reverse-engineered Brella's JSON:API** — attendees, interests, chat, poke (follow-up nudge)
- **AI-powered message generation** — Claude Haiku 4.5, GPT-5-mini, or Jinja2 templates (no API key needed)
- **Server-side filtering** — persona, interest, industry, function IDs
- **Dedup** — tracks who you've already contacted per event in SQLite
- **14-tool MCP server** — use it conversationally from Claude Desktop/Code
- **CLI with Rich TUI** — progress bars, preview tables, y/n confirmation before sending

## Disclaimer

**Use at your own risk.** This tool reverse-engineers Brella's internal API which is not publicly documented. I have not tested this at scale (hundreds of messages). You could get rate-limited or banned. I take no responsibility for:

- Getting your Brella account restricted
- Annoying people with bad messages
- Any terms of service violations
- Messages sent that you didn't review properly

**Always use `campaign preview` first.** Review every message before sending. The `campaign run` command asks for explicit confirmation — don't skip it.

## Who this is for

- Event attendees who want to network at scale without being spammy
- Startup founders looking for investors/partners at Brella events
- Anyone who thinks cold outreach should be personalized, not copy-pasted

## Quick start

```bash
# Clone
git clone https://github.com/Stupidoodle/brella-mass-outbound.git
cd brella-mass-outbound

# Install (requires Python 3.14+ and uv)
uv sync

# Configure
cp .env.example .env
# Edit .env with your Brella credentials and optionally an LLM API key

# See your profile
uv run brella attendees me --event <event-slug>

# Preview messages (dry run)
uv run brella campaign preview --event <event-slug> --max-messages 5

# Send for real (with confirmation)
uv run brella campaign run --event <event-slug>
```

### Getting the event slug

The event slug is the part after `/events/` in the Brella URL:
```
https://next.brella.io/events/startsummitxhack2026/people
                              ^^^^^^^^^^^^^^^^^^^^
```

### Authentication

**Option A — Email + password** (easiest):
```env
BRELLA_EMAIL=your@email.com
BRELLA_PASSWORD=your-password
```

**Option B — Auth token** (from browser):
1. Open your event on Brella, open DevTools → Console
2. Run: `localStorage.getItem('authHeaders')`
3. Paste the JSON string into `.env`:
```env
BRELLA_AUTH_TOKEN={"access-token":"...","client":"...","uid":"..."}
```

### Message generation

Set `LLM_PROVIDER` in `.env`:

| Provider | Key needed | Quality | Speed |
|----------|-----------|---------|-------|
| `claude` | `ANTHROPIC_API_KEY` | Best — references their work, finds angles | ~2s/msg |
| `openai` | `OPENAI_API_KEY` | Good | ~1s/msg |
| `template` | None | Decent — Jinja2 with shared interests | Instant |

## CLI commands

```bash
# Discovery
uv run brella attendees me --event <slug>              # Your profile
uv run brella attendees list --event <slug> --size 20  # Browse attendees
uv run brella attendees show --event <slug> --id 123   # Full profile
uv run brella attendees search --event <slug> --query "AI"

# Campaigns
uv run brella campaign preview --event <slug>          # Dry run with message previews
uv run brella campaign preview --event <slug> \
  --persona "Startup (Founder)" --max-messages 10      # Filtered preview

uv run brella campaign run --event <slug>              # Full send (with confirmation)
uv run brella campaign run --event <slug> \
  --persona "Investor" --interest "AI" --max-messages 20 -y

# Sync to local DB
uv run brella sync attendees --event <slug>            # Cache attendees locally
uv run brella sync interests --event <slug>            # Cache interest catalog
```

## MCP server

Use Brella outreach conversationally from Claude Desktop or Claude Code.

**14 tools:** `get_my_profile`, `list_attendees`, `filter_attendees`, `get_attendee_profile`, `search_attendees`, `get_event_info`, `get_interest_catalog`, `find_common_interests`, `generate_message`, `send_chat`, `poke_nudge`, `build_outbound_list`, `mass_generate_messages`, `mass_send_messages`

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "brella": {
      "command": "uv",
      "args": ["run", "brella-mcp"],
      "cwd": "/path/to/brella-mass-outbound"
    }
  }
}
```

### Claude Code

```bash
claude mcp add brella -- uv run brella-mcp
```

Then just ask Claude things like:
- *"Show me all AI startup founders at startsummitxhack2026"*
- *"Generate personalized messages for the top 20 matches"*
- *"What interests do I share with attendee 10567312?"*

## Architecture

DDD hexagonal architecture — same patterns as production enterprise codebases.

```
src/brella_outbound/
├── core/config.py                    # Pydantic Settings + get_settings()
├── bootstrap.py                      # Composition root
├── domain/
│   ├── models/                       # Plain dataclasses (10 models)
│   ├── ports/                        # Abstract interfaces
│   └── services/                     # Filtering & targeting logic
├── application/services/             # Campaign pipeline orchestration
├── infrastructure/
│   ├── brella/                       # Reverse-engineered JSON:API client + parser
│   ├── db/tables/ (13 tables, 3NF)  # SQLite + imperative SQLAlchemy mapping
│   ├── db/mappers/                   # Imperative mapper config
│   ├── db/migrations/                # Alembic
│   ├── llm/                          # Claude / OpenAI / Jinja2 generators
│   └── observability/                # structlog
├── cli/                              # Typer + Rich TUI
└── mcp/                              # FastMCP server (14 tools)
```

## Development

```bash
uv sync                    # Install deps
uv run pytest tests/ -v    # Run tests (40 passing)
uv run ruff check src/     # Lint
uv run ruff format src/    # Format
```

## License

MIT — do whatever you want with it.
