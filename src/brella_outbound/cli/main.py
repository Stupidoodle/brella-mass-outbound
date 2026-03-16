"""Brella Mass Outbound CLI — Typer-based entry point."""

import time
from datetime import datetime
from typing import Annotated

import typer
from rich import box
from rich.columns import Columns
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table as RichTable
from rich.text import Text

app = typer.Typer(
    name="brella",
    help="Personalized mass outreach for Brella event networking.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)
attendees_app = typer.Typer(help="Discover and explore event attendees.")
campaign_app = typer.Typer(help="Run outreach campaigns.")
sync_app = typer.Typer(help="Sync data from Brella API to local DB.")

app.add_typer(attendees_app, name="attendees")
app.add_typer(campaign_app, name="campaign")
app.add_typer(sync_app, name="sync")

console = Console()

PERSONA_COLORS = {
    "startup (founder)": "magenta",
    "investor": "green",
    "student": "cyan",
    "hacker": "yellow",
    "team": "blue",
    "attendee": "white",
    "media": "red",
    "corporate": "bright_black",
}


def _persona_styled(name: str | None) -> str:
    """Return Rich-styled persona string."""
    if not name:
        return "[dim]—[/dim]"
    color = PERSONA_COLORS.get(name.lower(), "white")
    return f"[{color}]{name}[/{color}]"


def _get_container():
    """Build container with interactive auth fallback."""
    from brella_outbound.core.config import get_settings

    settings = get_settings()

    if not settings.BRELLA_AUTH_TOKEN and not (
        settings.BRELLA_EMAIL and settings.BRELLA_PASSWORD
    ):
        console.print(
            "[yellow]No Brella credentials found in .env[/yellow]",
        )
        email = typer.prompt("Brella email")
        password = typer.prompt("Brella password", hide_input=True)
        # Rebuild settings with credentials
        import os

        os.environ["BRELLA_EMAIL"] = email
        os.environ["BRELLA_PASSWORD"] = password
        # Clear cached settings
        get_settings.cache_clear()

    from brella_outbound.bootstrap import Bootstrap

    with console.status("[bold]Authenticating with Brella..."):
        container = Bootstrap.build()
    return container


# ============================================================================
# Attendees
# ============================================================================


@attendees_app.command("list")
def attendees_list(
    event: Annotated[str, typer.Option(help="Brella event slug")],
    page: Annotated[int, typer.Option(help="Page number")] = 1,
    size: Annotated[int, typer.Option(help="Page size (max 120)")] = 20,
    persona: Annotated[str | None, typer.Option(help="Filter persona ID")] = None,
) -> None:
    """List attendees for an event."""
    container = _get_container()

    if persona:
        attendees, meta = container.brella_api.filter_attendees(
            event,
            persona_ids=[int(persona)],
            page=page,
            page_size=min(size, 120),
        )
    else:
        attendees, meta = container.brella_api.list_attendees(
            event,
            page=page,
            page_size=min(size, 120),
        )

    total = meta.get("total_count", "?")
    total_pages = meta.get("total_pages", "?")

    table = RichTable(
        title=f"[bold]Attendees[/bold] — {event}",
        caption=f"Page {page}/{total_pages} | {total} total",
        box=box.ROUNDED,
        show_lines=True,
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Name", style="bold", min_width=18)
    table.add_column("Role", min_width=15)
    table.add_column("Company", min_width=12)
    table.add_column("Persona", min_width=12)
    table.add_column("Interests", max_width=35)

    for i, a in enumerate(attendees, start=(page - 1) * size + 1):
        interests_str = ", ".join(a.interest_names[:4])
        if len(a.interest_names) > 4:
            interests_str += f" [dim]+{len(a.interest_names) - 4}[/dim]"
        table.add_row(
            str(i),
            a.full_name,
            a.company_title or "[dim]—[/dim]",
            a.company_name or "[dim]—[/dim]",
            _persona_styled(a.persona_name),
            interests_str or "[dim]—[/dim]",
        )

    console.print()
    console.print(table)


@attendees_app.command("show")
def attendees_show(
    event: Annotated[str, typer.Option(help="Brella event slug")],
    id: Annotated[int, typer.Option(help="Attendee ID")],
) -> None:
    """Show detailed attendee profile."""
    container = _get_container()
    a = container.brella_api.get_attendee(event, id)

    # Build profile panel
    lines = []
    lines.append(f"[bold]{a.full_name}[/bold]")
    if a.company_title:
        lines.append(f"[dim]Title:[/dim]    {a.company_title}")
    if a.company_name:
        lines.append(f"[dim]Company:[/dim]  {a.company_name}")
    lines.append(f"[dim]Persona:[/dim]  {_persona_styled(a.persona_name)}")
    if a.industry_name:
        lines.append(f"[dim]Industry:[/dim] {a.industry_name}")
    if a.function_name:
        lines.append(f"[dim]Function:[/dim] {a.function_name}")
    if a.pitch:
        lines.append("")
        lines.append(f"[italic]{a.pitch[:300]}[/italic]")
    if a.linkedin:
        lines.append(f"\n[dim]LinkedIn:[/dim] {a.linkedin}")
    if a.website:
        lines.append(f"[dim]Website:[/dim]  {a.website}")

    panel = Panel(
        "\n".join(lines),
        title=f"[bold]ID {a.id}[/bold]",
        border_style="bright_blue",
        padding=(1, 2),
    )
    console.print()
    console.print(panel)

    if a.interest_names:
        tags = [
            f"[on bright_black] {name} [/on bright_black]"
            for name in a.interest_names
        ]
        console.print()
        console.print(Columns(tags, padding=(0, 1)))
    console.print()


@attendees_app.command("search")
def attendees_search(
    event: Annotated[str, typer.Option(help="Brella event slug")],
    query: Annotated[str, typer.Option(help="Search query")],
) -> None:
    """Search attendees by name, title, or company."""
    container = _get_container()
    results = container.brella_api.search_attendees(event, query)

    if not results:
        console.print("[yellow]No results found.[/yellow]")
        return

    table = RichTable(
        title=f"[bold]Search:[/bold] \"{query}\"",
        box=box.SIMPLE,
    )
    table.add_column("ID", style="dim")
    table.add_column("Name", style="bold")
    table.add_column("Title")
    table.add_column("Company")
    table.add_column("Persona")

    for a in results:
        table.add_row(
            str(a.id),
            a.full_name,
            a.company_title or "",
            a.company_name or "",
            _persona_styled(a.persona_name),
        )

    console.print()
    console.print(table)


@attendees_app.command("me")
def attendees_me(
    event: Annotated[str, typer.Option(help="Brella event slug")],
) -> None:
    """Show your own profile."""
    container = _get_container()
    me = container.brella_api.get_me_attendee(event)

    console.print()
    console.print(
        Panel(
            f"[bold]{me.full_name}[/bold]\n"
            f"{me.company_title or ''} @ {me.company_name or ''}\n"
            f"Persona: {_persona_styled(me.persona_name)}\n"
            f"Interests: {', '.join(me.interest_names) or '—'}",
            title="[bold green]Your Profile[/bold green]",
            border_style="green",
            padding=(1, 2),
        ),
    )


# ============================================================================
# Campaign
# ============================================================================


@campaign_app.command("run")
def campaign_run(
    event: Annotated[str, typer.Option(help="Brella event slug")],
    persona: Annotated[
        list[str] | None, typer.Option(help="Filter by persona name")
    ] = None,
    industry: Annotated[
        list[str] | None, typer.Option(help="Filter by industry name")
    ] = None,
    interest: Annotated[
        list[str] | None, typer.Option(help="Filter by interest name")
    ] = None,
    min_common: Annotated[
        int, typer.Option(help="Min shared interests")
    ] = 0,
    max_messages: Annotated[
        int | None, typer.Option(help="Max messages to send")
    ] = None,
    context: Annotated[
        str | None, typer.Option(help="Extra context for message generation")
    ] = None,
    yes: Annotated[
        bool, typer.Option("--yes", "-y", help="Skip confirmation")
    ] = False,
) -> None:
    """Run a full outreach campaign with preview and confirmation."""
    container = _get_container()

    from brella_outbound.application.services.campaign_service import CampaignService
    from brella_outbound.domain.services.outreach_service import OutreachService

    # Step 1: Fetch profiles
    console.print()
    with console.status("[bold]Fetching your profile..."):
        me = container.brella_api.get_me_attendee(event)
        event_obj = container.brella_api.get_event(event)
    console.print(
        f"  [green]✓[/green] Sender: [bold]{me.full_name}[/bold] "
        f"({me.company_title} @ {me.company_name})",
    )

    # Step 2: Fetch all attendees with progress
    console.print()
    attendees = _fetch_all_with_progress(container, event)
    console.print(f"  [green]✓[/green] Fetched [bold]{len(attendees)}[/bold] attendees")

    # Step 3: Filter
    outreach_svc = OutreachService(logger=container.logger)
    svc = CampaignService(
        brella_api=container.brella_api,
        message_generator=container.message_generator,
        outreach_service=outreach_svc,
        uow=container.uow,
        logger=container.logger,
    )
    contacted_ids = svc._get_contacted_ids(event)
    exclude_ids = contacted_ids | {me.id}

    targets = outreach_svc.filter_attendees(
        attendees,
        exclude_ids=exclude_ids,
        personas=persona,
        industries=industry,
        interests=interest,
        min_common_interests=min_common,
        my_interests=me.interest_names,
    )
    if max_messages:
        targets = targets[:max_messages]

    if not targets:
        console.print("[yellow]No targets match your filters.[/yellow]")
        raise typer.Exit()

    console.print(
        f"  [green]✓[/green] [bold]{len(targets)}[/bold] targets "
        f"(excluded {len(exclude_ids)} — self + already contacted)",
    )

    # Step 4: Generate messages with progress
    console.print()
    messages = []
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
    )
    with progress:
        task = progress.add_task("Generating messages...", total=len(targets))
        for target in targets:
            try:
                msg = container.message_generator.generate(
                    sender=me,
                    recipient=target,
                    context=context,
                )
                messages.append((target, msg, None))
            except Exception as e:
                messages.append((target, "", str(e)))
            progress.advance(task)

    # Step 5: Preview table
    console.print()
    preview = RichTable(
        title="[bold]Campaign Preview[/bold]",
        box=box.ROUNDED,
        show_lines=True,
    )
    preview.add_column("#", style="dim", width=4)
    preview.add_column("Recipient", style="bold", min_width=18)
    preview.add_column("Company", min_width=12)
    preview.add_column("Persona", min_width=12)
    preview.add_column("Message", max_width=55)
    preview.add_column("", width=3)

    for i, (target, msg, err) in enumerate(messages, 1):
        if err:
            status = "[red]✗[/red]"
            msg_preview = f"[red]{err[:50]}[/red]"
        else:
            status = "[green]✓[/green]"
            msg_preview = msg[:55] + "..." if len(msg) > 55 else msg
        preview.add_row(
            str(i),
            target.full_name,
            target.company_name or "—",
            _persona_styled(target.persona_name),
            msg_preview,
            status,
        )

    console.print(preview)

    valid = [(t, m) for t, m, e in messages if not e]
    failed_gen = [(t, e) for t, m, e in messages if e]

    console.print(
        f"\n  [green]{len(valid)}[/green] messages ready | "
        f"[red]{len(failed_gen)}[/red] generation failures",
    )

    # Step 6: Confirm
    if not yes:
        console.print()
        confirm = typer.confirm(
            f"Send {len(valid)} messages on {event}?",
            default=False,
        )
        if not confirm:
            console.print("[yellow]Aborted.[/yellow]")
            raise typer.Exit()

    # Step 7: Send with progress
    console.print()
    sent = 0
    send_errors = 0
    results = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Sending messages...", total=len(valid))
        for target, msg in valid:
            try:
                container.brella_api.start_chat(
                    user_id=target.user_id,
                    event_id=event_obj.id,
                    message=msg,
                )
                sent += 1
                results.append((target.full_name, "sent", None))
            except Exception as e:
                send_errors += 1
                results.append((target.full_name, "failed", str(e)))
            progress.advance(task)

    # Step 8: Summary
    console.print()
    summary = Panel(
        f"[green bold]{sent}[/green bold] sent  |  "
        f"[red]{send_errors}[/red] failed  |  "
        f"[dim]{len(failed_gen)} gen errors[/dim]\n"
        f"[dim]Event: {event} | {datetime.now():%Y-%m-%d %H:%M}[/dim]",
        title="[bold]Campaign Complete[/bold]",
        border_style="green" if send_errors == 0 else "yellow",
        padding=(1, 2),
    )
    console.print(summary)

    # Persist campaign
    from brella_outbound.domain.models.campaign import (
        Campaign,
        OutreachMessage,
        OutreachStatus,
    )

    campaign = Campaign(event_slug=event)
    for name, status, error in results:
        t, m = next(
            ((t, m) for t, m in valid if t.full_name == name),
            (None, ""),
        )
        campaign.messages.append(OutreachMessage(
            attendee_id=t.id if t else 0,
            attendee_name=name,
            message=m,
            status=OutreachStatus.SENT if status == "sent" else OutreachStatus.FAILED,
            error=error,
            sent_at=datetime.now() if status == "sent" else None,
        ))
    try:
        with container.uow:
            container.uow.session.add(campaign)
    except Exception:
        pass


@campaign_app.command("preview")
def campaign_preview(
    event: Annotated[str, typer.Option(help="Brella event slug")],
    persona: Annotated[
        list[str] | None, typer.Option(help="Filter by persona name")
    ] = None,
    industry: Annotated[
        list[str] | None, typer.Option(help="Filter by industry name")
    ] = None,
    interest: Annotated[
        list[str] | None, typer.Option(help="Filter by interest name")
    ] = None,
    min_common: Annotated[
        int, typer.Option(help="Min shared interests")
    ] = 0,
    max_messages: Annotated[
        int | None, typer.Option(help="Max targets to preview")
    ] = 10,
    context: Annotated[
        str | None, typer.Option(help="Extra context for message generation")
    ] = None,
) -> None:
    """Preview generated messages without sending (dry run)."""
    container = _get_container()

    from brella_outbound.domain.services.outreach_service import OutreachService

    with console.status("[bold]Fetching profiles..."):
        me = container.brella_api.get_me_attendee(event)

    attendees = _fetch_all_with_progress(container, event)

    outreach_svc = OutreachService(logger=container.logger)
    targets = outreach_svc.filter_attendees(
        attendees,
        exclude_ids={me.id},
        personas=persona,
        industries=industry,
        interests=interest,
        min_common_interests=min_common,
        my_interests=me.interest_names,
    )
    if max_messages:
        targets = targets[:max_messages]

    if not targets:
        console.print("[yellow]No targets match your filters.[/yellow]")
        raise typer.Exit()

    console.print(
        f"\n  Previewing [bold]{len(targets)}[/bold] messages "
        f"(of {len(attendees)} attendees)\n",
    )

    for i, target in enumerate(targets, 1):
        try:
            msg = container.message_generator.generate(
                sender=me,
                recipient=target,
                context=context,
            )
        except Exception as e:
            msg = f"[generation error: {e}]"

        common = set(me.interest_names) & set(target.interest_names)
        common_str = (
            f"[green]{', '.join(list(common)[:3])}[/green]" if common else "[dim]none[/dim]"
        )

        panel = Panel(
            f"{msg}",
            title=(
                f"[bold]#{i}[/bold] → {target.full_name} "
                f"({target.company_title or '—'} @ {target.company_name or '—'})"
            ),
            subtitle=f"Common: {common_str} | {_persona_styled(target.persona_name)} | {len(msg)} chars",
            border_style="bright_blue",
            padding=(0, 2),
        )
        console.print(panel)
        console.print()


# ============================================================================
# Sync
# ============================================================================


@sync_app.command("attendees")
def sync_attendees(
    event: Annotated[str, typer.Option(help="Brella event slug")],
) -> None:
    """Sync all attendees from Brella to local DB."""
    container = _get_container()
    attendees = _fetch_all_with_progress(container, event)

    with console.status("[bold]Saving to database..."):
        with container.uow:
            for a in attendees:
                container.uow.session.merge(a)

    console.print(
        f"  [green]✓[/green] Synced [bold]{len(attendees)}[/bold] "
        f"attendees to local DB",
    )


@sync_app.command("interests")
def sync_interests(
    event: Annotated[str, typer.Option(help="Brella event slug")],
) -> None:
    """Sync interest catalog from Brella to local DB."""
    container = _get_container()

    from brella_outbound.infrastructure.brella.jsonapi_parser import JsonApiParser

    with console.status("[bold]Fetching interest catalog..."):
        raw = container.brella_api.get_interests(event)

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
        f"  [green]✓[/green] Synced [bold]{len(categories)}[/bold] categories, "
        f"[bold]{len(interests)}[/bold] interests, "
        f"[bold]{len(intent_pairs)}[/bold] intent pairs, "
        f"[bold]{len(intents)}[/bold] intents",
    )


# ============================================================================
# Helpers
# ============================================================================


def _fetch_all_with_progress(container, event_slug: str):
    """Fetch all attendees with a progress bar."""
    all_attendees = []
    page = 1

    # First call to get total
    batch, meta = container.brella_api.list_attendees(
        event_slug,
        page=1,
        page_size=120,
    )
    total = meta.get("total_count", 0)
    total_pages = meta.get("total_pages", 1)
    all_attendees.extend(batch)

    if total_pages <= 1:
        return all_attendees

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(
            f"Fetching {total} attendees...",
            total=total,
            completed=len(batch),
        )
        for page in range(2, total_pages + 1):
            batch, _ = container.brella_api.list_attendees(
                event_slug,
                page=page,
                page_size=120,
            )
            if not batch:
                break
            all_attendees.extend(batch)
            progress.update(task, completed=len(all_attendees))

    return all_attendees


if __name__ == "__main__":
    app()
