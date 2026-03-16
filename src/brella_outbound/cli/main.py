"""Brella Mass Outbound CLI — Typer-based entry point."""

from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table as RichTable

from brella_outbound.bootstrap import Bootstrap
from brella_outbound.domain.services.outreach_service import OutreachService

app = typer.Typer(
    name="brella",
    help="Personalized mass outreach for Brella event networking.",
    no_args_is_help=True,
)
attendees_app = typer.Typer(help="Manage event attendees.")
campaign_app = typer.Typer(help="Run outreach campaigns.")
sync_app = typer.Typer(help="Sync data from Brella API to local DB.")

app.add_typer(attendees_app, name="attendees")
app.add_typer(campaign_app, name="campaign")
app.add_typer(sync_app, name="sync")

console = Console()


@attendees_app.command("list")
def attendees_list(
    event: Annotated[str, typer.Option(help="Brella event slug")],
    page: Annotated[int, typer.Option(help="Page number")] = 1,
    size: Annotated[int, typer.Option(help="Page size")] = 20,
) -> None:
    """List attendees for an event."""
    container = Bootstrap.build()
    attendees, meta = container.brella_api.list_attendees(event, page=page, page_size=size)

    table = RichTable(title=f"Attendees — {event} (page {page})")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="bold")
    table.add_column("Title")
    table.add_column("Company")
    table.add_column("Persona")
    table.add_column("Interests", max_width=40)

    for a in attendees:
        table.add_row(
            str(a.id),
            a.full_name,
            a.company_title or "",
            a.company_name or "",
            a.persona_name or "",
            ", ".join(a.interest_names[:5]),
        )

    console.print(table)
    total = meta.get("total_count", "?")
    console.print(f"\n[dim]Showing {len(attendees)} of {total} attendees[/dim]")


@attendees_app.command("show")
def attendees_show(
    event: Annotated[str, typer.Option(help="Brella event slug")],
    id: Annotated[int, typer.Option(help="Attendee ID")],
) -> None:
    """Show detailed attendee profile."""
    container = Bootstrap.build()
    a = container.brella_api.get_attendee(event, id)

    console.print(f"\n[bold]{a.full_name}[/bold]")
    console.print(f"  Title:    {a.company_title or '—'}")
    console.print(f"  Company:  {a.company_name or '—'}")
    console.print(f"  Persona:  {a.persona_name or '—'}")
    console.print(f"  Industry: {a.industry_name or '—'}")
    console.print(f"  Function: {a.function_name or '—'}")
    if a.pitch:
        console.print(f"  Bio:      {a.pitch[:200]}")
    if a.linkedin:
        console.print(f"  LinkedIn: {a.linkedin}")
    if a.website:
        console.print(f"  Website:  {a.website}")
    if a.interest_names:
        console.print(f"  Interests: {', '.join(a.interest_names)}")
    console.print()


@attendees_app.command("search")
def attendees_search(
    event: Annotated[str, typer.Option(help="Brella event slug")],
    query: Annotated[str, typer.Option(help="Search query")],
) -> None:
    """Search attendees by name, title, or company."""
    container = Bootstrap.build()
    results = container.brella_api.search_attendees(event, query)

    if not results:
        console.print("[yellow]No results found.[/yellow]")
        return

    for a in results:
        console.print(f"  [bold]{a.full_name}[/bold] — {a.display_info}")
    console.print(f"\n[dim]{len(results)} results[/dim]")


@campaign_app.command("run")
def campaign_run(
    event: Annotated[str, typer.Option(help="Brella event slug")],
    dry_run: Annotated[bool, typer.Option(help="Preview without sending")] = True,
    persona: Annotated[list[str] | None, typer.Option(help="Filter by persona")] = None,
    industry: Annotated[list[str] | None, typer.Option(help="Filter by industry")] = None,
    interest: Annotated[list[str] | None, typer.Option(help="Filter by interest")] = None,
    min_common: Annotated[int, typer.Option(help="Min shared interests")] = 0,
    max_messages: Annotated[int | None, typer.Option(help="Max messages to send")] = None,
    context: Annotated[str | None, typer.Option(help="Extra context for LLM")] = None,
) -> None:
    """Run an outreach campaign."""
    container = Bootstrap.build()
    outreach_svc = OutreachService(logger=container.logger)

    from brella_outbound.application.services.campaign_service import CampaignService

    svc = CampaignService(
        brella_api=container.brella_api,
        message_generator=container.message_generator,
        outreach_service=outreach_svc,
        uow=container.uow,
        logger=container.logger,
    )

    campaign = svc.run(
        event_slug=event,
        dry_run=dry_run,
        personas=persona,
        industries=industry,
        interests=interest,
        min_common_interests=min_common,
        max_messages=max_messages,
        context=context,
    )

    # Print summary
    console.print(f"\n[bold]Campaign Results[/bold]")
    table = RichTable()
    table.add_column("Attendee", style="bold")
    table.add_column("Status")
    table.add_column("Message", max_width=60)

    for msg in campaign.messages:
        status_style = {
            "sent": "green",
            "pending": "yellow",
            "failed": "red",
            "skipped": "dim",
        }.get(msg.status.value, "white")
        table.add_row(
            msg.attendee_name,
            f"[{status_style}]{msg.status.value}[/{status_style}]",
            msg.message[:60] + "..." if len(msg.message) > 60 else msg.message,
        )

    console.print(table)
    console.print(
        f"\n[dim]Sent: {campaign.sent_count} | "
        f"Pending: {campaign.pending_count} | "
        f"Failed: {campaign.failed_count}[/dim]",
    )


@sync_app.command("attendees")
def sync_attendees(
    event: Annotated[str, typer.Option(help="Brella event slug")],
) -> None:
    """Sync all attendees from Brella to local DB."""
    container = Bootstrap.build()
    attendees = container.brella_api.list_all_attendees(event)

    with container.uow:
        for a in attendees:
            container.uow.session.merge(a)

    console.print(f"[green]Synced {len(attendees)} attendees to local DB[/green]")


@sync_app.command("interests")
def sync_interests(
    event: Annotated[str, typer.Option(help="Brella event slug")],
) -> None:
    """Sync interest catalog from Brella to local DB."""
    container = Bootstrap.build()
    raw = container.brella_api.get_interests(event)

    from brella_outbound.infrastructure.brella.jsonapi_parser import JsonApiParser

    parser = JsonApiParser()
    categories, interests, intent_pairs, intents = parser.parse_interest_categories(
        raw.get("data", []),
        raw.get("included", []),
    )

    with container.uow:
        for cat in categories:
            container.uow.session.merge(cat)
        for interest in interests:
            container.uow.session.merge(interest)
        for pair in intent_pairs:
            container.uow.session.merge(pair)
        for intent in intents:
            container.uow.session.merge(intent)

    console.print(
        f"[green]Synced {len(categories)} categories, "
        f"{len(interests)} interests, "
        f"{len(intent_pairs)} intent pairs, "
        f"{len(intents)} intents[/green]",
    )


if __name__ == "__main__":
    app()
