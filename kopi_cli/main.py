"""
kopi-cli – Command-line interface for the Kopi Tools platform.

Usage:
    kopi build [--skip-tests] [--project P]  Build all Maven microservices
    kopi up [--build] [-d]                   Start the full stack
    kopi down [--volumes]                    Stop and remove containers
    kopi restart [service]                   Restart one or all services
    kopi status                              Check service health
    kopi ps                                  List running containers
    kopi logs [service] [-f]                 Stream logs
    kopi version                             Print CLI version
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel

from kopi_cli import __version__
from kopi_cli.commands import build as build_cmd
from kopi_cli.commands import logs as logs_cmd
from kopi_cli.commands import stack as stack_cmd
from kopi_cli.commands import status as status_cmd

console = Console()

app = typer.Typer(
    name="kopi",
    help="Manage the Kopi Tools platform.",
    add_completion=True,
    rich_markup_mode="rich",
    no_args_is_help=True,
)

# ── Sub-commands ──────────────────────────────────────────────────────────────
# Build
app.command("build",   help="Build all Maven microservices.")(build_cmd.build)

# Stack lifecycle
app.command("up",      help="Start the full stack.")(stack_cmd.up)
app.command("down",    help="Stop and remove containers.")(stack_cmd.down)
app.command("restart", help="Restart one or all services.")(stack_cmd.restart)

# Observability
app.command("status",  help="Check service health.")(status_cmd.status)
app.command("ps",      help="List running containers.")(status_cmd.ps)
app.command("logs",    help="Stream logs from a service.")(logs_cmd.logs)


# ── Utility commands ──────────────────────────────────────────────────────────
@app.command()
def version():
    """Print the kopi-cli version."""
    console.print(Panel(
        f"[bold green]kopi-cli[/bold green] [cyan]{__version__}[/cyan]",
        expand=False,
    ))


@app.callback(invoke_without_command=True)
def _default(ctx: typer.Context):
    """Kopi Tools CLI."""
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())


if __name__ == "__main__":
    app()
