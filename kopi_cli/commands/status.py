"""Status and health-check commands."""

from __future__ import annotations

import subprocess
from typing import Optional

import httpx
import typer
from rich.console import Console
from rich.table import Table

from kopi_cli.config import SERVICES, find_infra_dir

console = Console()
app = typer.Typer(help="Check health and running state of Kopi Tools services.")

# HTTP timeout for individual health checks
_TIMEOUT = 4.0


def _check_health(url: str) -> tuple[str, str]:
    """Return (status_emoji, detail_text) for a single health endpoint."""
    try:
        r = httpx.get(url, timeout=_TIMEOUT)
        if r.status_code == 200:
            body = r.json()
            status = body.get("status", "UNKNOWN")
            if status == "UP":
                return "[green]UP[/green]", ""
            return "[yellow]DEGRADED[/yellow]", status
        return "[red]DOWN[/red]", f"HTTP {r.status_code}"
    except httpx.ConnectError:
        return "[red]DOWN[/red]", "connection refused"
    except httpx.TimeoutException:
        return "[red]TIMEOUT[/red]", f">{_TIMEOUT}s"
    except Exception as exc:
        return "[red]ERROR[/red]", str(exc)


@app.command()
def status():
    """Show health status of all running services."""
    table = Table(title="Kopi Tools – Service Health", show_lines=True)
    table.add_column("Service", style="bold")
    table.add_column("Health URL")
    table.add_column("Status", justify="center")
    table.add_column("Detail")

    all_up = True
    for svc in SERVICES:
        emoji, detail = _check_health(svc.health_url)
        if "UP" not in emoji:
            all_up = False
        table.add_row(svc.name, svc.health_url, emoji, detail)

    console.print(table)

    if not all_up:
        console.print()
        console.print("[yellow]Some services are not healthy. Run [bold]kopi logs[/bold] to investigate.[/yellow]")
        console.print("If the stack is not running, use [bold]kopi up[/bold] to start it.")


@app.command("ps")
def ps():
    """List running containers (docker compose ps)."""
    try:
        infra_dir = find_infra_dir()
    except FileNotFoundError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)

    subprocess.run(["docker", "compose", "ps"], cwd=infra_dir)
