"""Stack lifecycle commands: up, down, restart."""

from __future__ import annotations

import subprocess
import sys
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from kopi_cli.config import find_compose_file

console = Console()
app = typer.Typer(help="Manage the Kopi Tools stack lifecycle.")


def _compose(compose_file, *args: str) -> int:
    """Run ``docker compose -f <compose_file> <args>``. Returns exit code."""
    cmd = ["docker", "compose", "-f", str(compose_file), *args]
    console.print(f"[dim]$ {' '.join(cmd)}[/dim]")
    result = subprocess.run(cmd, cwd=compose_file.parent)
    return result.returncode


@app.command()
def up(
    build: Annotated[bool, typer.Option("--build", help="Rebuild images before starting.")] = False,
    detach: Annotated[bool, typer.Option("--detach/--no-detach", "-d", help="Run in background (default: True).")] = True,
):
    """Start the full Kopi Tools stack (PostgreSQL + auth + links + gateway)."""
    try:
        compose_file = find_compose_file()
    except FileNotFoundError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)

    console.print(Panel(
        Text.from_markup(
            f"[bold]Starting Kopi Tools[/bold]\n"
            f"[dim]Compose file:[/dim] {compose_file}"
        ),
        title="[bold green]kopi up[/bold green]",
        border_style="green",
    ))

    args = ["up"]
    if build:
        args.append("--build")
    if detach:
        args.append("-d")

    code = _compose(compose_file, *args)

    if code == 0 and detach:
        console.print()
        console.print("[bold green]Stack is running.[/bold green]")
        console.print()
        console.print("  [cyan]Frontend[/cyan]    http://localhost:4200")
        console.print("  [cyan]Gateway[/cyan]     http://localhost:8080")
        console.print("  [cyan]Auth[/cyan]        http://localhost:8081")
        console.print("  [cyan]Links[/cyan]       http://localhost:8082")
        console.print("  [cyan]Tasks[/cyan]       http://localhost:8083")
        console.print()
        console.print("Run [bold]kopi status[/bold] to check service health.")
        console.print("Run [bold]kopi logs[/bold] to tail all logs.")
    elif code != 0:
        console.print(f"[bold red]docker compose up exited with code {code}.[/bold red]")
        raise typer.Exit(code)


@app.command()
def down(
    volumes: Annotated[bool, typer.Option("--volumes", "-v", help="Also remove volumes (deletes DB data).")] = False,
):
    """Stop and remove all Kopi Tools containers."""
    try:
        compose_file = find_compose_file()
    except FileNotFoundError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)

    if volumes:
        console.print("[bold yellow]Warning:[/bold yellow] --volumes will delete all database data.")
        confirm = typer.confirm("Continue?")
        if not confirm:
            raise typer.Abort()

    args = ["down"]
    if volumes:
        args.append("--volumes")

    console.print(Panel("[bold]Stopping Kopi Tools...[/bold]", border_style="yellow"))
    code = _compose(compose_file, *args)
    if code != 0:
        raise typer.Exit(code)
    console.print("[bold green]Stack stopped.[/bold green]")


@app.command()
def restart(
    service: Annotated[Optional[str], typer.Argument(help="Service to restart (default: all).")] = None,
):
    """Restart one or all services without rebuilding."""
    try:
        compose_file = find_compose_file()
    except FileNotFoundError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)

    label = f"[bold]{service}[/bold]" if service else "all services"
    console.print(f"Restarting {label}...")

    args = ["restart"] + ([service] if service else [])
    code = _compose(compose_file, *args)
    if code != 0:
        raise typer.Exit(code)
    console.print(f"[bold green]Done.[/bold green]")
