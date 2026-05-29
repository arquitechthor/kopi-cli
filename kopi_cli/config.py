"""Locate kopi-infra directory and expose service metadata."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ServiceInfo:
    name: str
    health_url: str
    compose_name: str  # matches the service key in docker-compose.yml


SERVICES: list[ServiceInfo] = [
    ServiceInfo("kopi-gateway", "http://localhost:8080/actuator/health", "kopi-gateway"),
    ServiceInfo("kopi-auth",    "http://localhost:8081/actuator/health", "kopi-auth"),
    ServiceInfo("kopi-links",   "http://localhost:8082/actuator/health", "kopi-links"),
]


def _has_compose(directory: Path) -> bool:
    """Return True if *directory* contains a docker-compose.yml at root or new location."""
    return (
        (directory / "docker" / "compose" / "docker-compose.yml").exists()
        or (directory / "docker-compose.yml").exists()
    )


def find_infra_dir() -> Path:
    """
    Resolve the kopi-infra directory using the following order:
      1. KOPI_INFRA_DIR environment variable
      2. Walk up from CWD looking for a directory named kopi-infra with a compose file
      3. Relative to the CLI package itself (../kopi-infra)

    Raises FileNotFoundError if none found.
    """
    # 1 — env var override
    if env_path := os.environ.get("KOPI_INFRA_DIR"):
        p = Path(env_path).expanduser().resolve()
        if _has_compose(p):
            return p
        raise FileNotFoundError(
            f"KOPI_INFRA_DIR='{env_path}' does not contain docker-compose.yml"
        )

    # 2 — walk up from CWD
    current = Path.cwd().resolve()
    for _ in range(6):
        candidate = current / "kopi-infra"
        if _has_compose(candidate):
            return candidate
        # maybe we're already inside kopi-infra
        if _has_compose(current) and current.name == "kopi-infra":
            return current
        current = current.parent

    # 3 — relative to this file: kopi-cli/kopi_cli/config.py → ../kopi-infra
    pkg_root = Path(__file__).resolve().parent.parent  # kopi-cli/
    candidate = pkg_root.parent / "kopi-infra"         # kopi-tools/kopi-infra
    if _has_compose(candidate):
        return candidate

    raise FileNotFoundError(
        "Could not locate kopi-infra. "
        "Set KOPI_INFRA_DIR env var or run from inside the kopi-tools workspace."
    )


def find_compose_file() -> Path:
    """
    Return the path to docker-compose.yml.

    Supports both the new structure (docker/compose/docker-compose.yml)
    and the legacy structure (docker-compose.yml at the infra root).
    """
    infra_dir = find_infra_dir()

    new_path = infra_dir / "docker" / "compose" / "docker-compose.yml"
    if new_path.exists():
        return new_path

    legacy_path = infra_dir / "docker-compose.yml"
    if legacy_path.exists():
        return legacy_path

    raise FileNotFoundError(
        f"docker-compose.yml not found in {infra_dir}. "
        "Expected at docker/compose/docker-compose.yml"
    )


@dataclass
class MavenProject:
    name: str       # logical service name, e.g. "kopi-auth"
    dir_name: str   # folder name inside the workspace, e.g. "kopi-auth-bk"


MAVEN_PROJECTS: list[MavenProject] = [
    MavenProject("kopi-auth",    "kopi-auth-bk"),
    MavenProject("kopi-links",   "kopi-links-bk"),
    MavenProject("kopi-tasks",   "kopi-tasks-bk"),
    MavenProject("kopi-gateway", "kopi-gateway"),
]


def find_workspace_dir() -> Path:
    """Return the kopi-tools workspace root (parent of kopi-infra)."""
    return find_infra_dir().parent
