"""Log streaming command."""

from __future__ import annotations

import subprocess
from typing import Annotated, Optional

import typer
from rich.console import Console

from kopi_cli.config import find_compose_file

console = Console()
app = typer.Typer(help="View and stream logs from Kopi Tools services.")

_VALID_SERVICES = {"kopi-gateway", "kopi-auth", "kopi-links", "kopi-tasks", "postgres", "kopi-ui"}


@app.command()
def logs(
    service: Annotated[
        Optional[str],
        typer.Argument(
            help=f"Service to tail. One of: {', '.join(sorted(_VALID_SERVICES))}. Omit for all.",
        ),
    ] = None,
    follow: Annotated[bool, typer.Option("--follow", "-f", help="Follow log output.")] = True,
    tail: Annotated[int, typer.Option("--tail", "-n", help="Number of lines to show from the end.")] = 50,
):
    """Stream logs from one or all services."""
    try:
        compose_file = find_compose_file()
    except FileNotFoundError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)

    if service and service not in _VALID_SERVICES:
        console.print(
            f"[red]Unknown service '[bold]{service}[/bold]'.[/red] "
            f"Valid options: {', '.join(sorted(_VALID_SERVICES))}"
        )
        raise typer.Exit(1)

    cmd = ["docker", "compose", "-f", str(compose_file), "logs", f"--tail={tail}"]
    if follow:
        cmd.append("-f")
    if service:
        cmd.append(service)

    try:
        subprocess.run(cmd, cwd=compose_file.parent)
    except KeyboardInterrupt:
        pass  # clean Ctrl-C exit
