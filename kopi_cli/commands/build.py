"""Build command: compile and package all Maven microservices."""

from __future__ import annotations

import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.panel import Panel

from kopi_cli.config import MAVEN_PROJECTS, MavenProject, find_workspace_dir

console = Console()


@dataclass
class BuildResult:
    name: str
    success: bool
    duration: float
    output: str = field(default="", repr=False)


def _run_maven(project_dir: Path, extra_args: list[str]) -> BuildResult:
    if sys.platform == "win32":
        wrapper = str(project_dir / "mvnw.cmd")
    else:
        wrapper = "./mvnw"
    cmd = [wrapper, "package", *extra_args]
    console.print(f"[dim]  $ mvnw {'  '.join(extra_args) if extra_args else 'package'}[/dim]")

    start = time.monotonic()
    result = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True,
                            shell=(sys.platform == "win32"))
    duration = time.monotonic() - start

    return BuildResult(
        name=project_dir.name,
        success=result.returncode == 0,
        duration=duration,
        output=result.stdout + result.stderr,
    )


def build(
    skip_tests: Annotated[bool, typer.Option("--skip-tests", "-s", help="Skip unit tests.")] = False,
    project: Annotated[Optional[str], typer.Option("--project", "-p", help="Build only this service (e.g. kopi-auth).")] = None,
):
    """Build all Maven microservices (or a single one with --project)."""
    try:
        workspace = find_workspace_dir()
    except FileNotFoundError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)

    targets = MAVEN_PROJECTS
    if project:
        targets = [p for p in MAVEN_PROJECTS if p.name == project or p.dir_name == project]
        if not targets:
            names = ", ".join(p.name for p in MAVEN_PROJECTS)
            console.print(f"[bold red]Error:[/bold red] Unknown project '{project}'. Available: {names}")
            raise typer.Exit(1)

    mvn_args = ["-DskipTests"] if skip_tests else []
    label = targets[0].name if len(targets) == 1 else "all services"

    console.print(Panel(
        Text.from_markup(
            f"[bold]Building {label}[/bold]\n"
            f"[dim]Workspace:[/dim] {workspace}\n"
            f"[dim]Skip tests:[/dim] {'yes' if skip_tests else 'no'}"
        ),
        title="[bold cyan]kopi build[/bold cyan]",
        border_style="cyan",
    ))

    results: list[BuildResult] = []
    for maven_project in targets:
        project_dir = workspace / maven_project.dir_name
        if not project_dir.exists():
            console.print(f"[bold yellow]Warning:[/bold yellow] {project_dir} not found, skipping.")
            results.append(BuildResult(name=maven_project.name, success=False, duration=0.0,
                                       output=f"Directory not found: {project_dir}"))
            continue

        console.print(f"\n[bold cyan]Building {maven_project.name}...[/bold cyan]")
        res = _run_maven(project_dir, mvn_args)
        res.name = maven_project.name
        results.append(res)

        if res.success:
            console.print(f"[green]OK[/green] {maven_project.name} built in {res.duration:.1f}s")
        else:
            console.print(f"[red]FAILED[/red] {maven_project.name} ({res.duration:.1f}s)")
            # Print the last 30 lines of output to surface the error
            tail = "\n".join(res.output.splitlines()[-30:])
            console.print(f"[dim]{tail}[/dim]")

    _print_summary(results)

    failed = [r for r in results if not r.success]
    if failed:
        raise typer.Exit(1)


def _print_summary(results: list[BuildResult]) -> None:
    console.print()
    table = Table(title="Build Summary", show_header=True, header_style="bold")
    table.add_column("Service", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Time", justify="right")

    for r in results:
        status = "[green]OK[/green]" if r.success else "[red]FAILED[/red]"
        table.add_row(r.name, Text.from_markup(status), f"{r.duration:.1f}s")

    console.print(table)
    total = sum(r.duration for r in results)
    passed = sum(1 for r in results if r.success)
    console.print(f"\n[dim]Total: {len(results)} projects | {passed} passed | {len(results)-passed} failed | {total:.1f}s[/dim]")
