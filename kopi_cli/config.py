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


def find_infra_dir() -> Path:
    """
    Resolve the kopi-infra directory using the following order:
      1. KOPI_INFRA_DIR environment variable
      2. Walk up from CWD, looking for a sibling/parent ``kopi-infra/docker-compose.yml``
      3. Relative to the CLI package itself (``../kopi-infra``)

    Raises FileNotFoundError if none found.
    """
    # 1 — env var override
    if env_path := os.environ.get("KOPI_INFRA_DIR"):
        p = Path(env_path).expanduser().resolve()
        if (p / "docker-compose.yml").exists():
            return p
        raise FileNotFoundError(
            f"KOPI_INFRA_DIR='{env_path}' does not contain docker-compose.yml"
        )

    # 2 — walk up from CWD
    current = Path.cwd().resolve()
    for _ in range(6):
        candidate = current / "kopi-infra"
        if (candidate / "docker-compose.yml").exists():
            return candidate
        # maybe we're already inside kopi-infra
        if (current / "docker-compose.yml").exists() and current.name == "kopi-infra":
            return current
        current = current.parent

    # 3 — relative to this file: kopi-cli/kopi_cli/config.py → ../kopi-infra
    pkg_root = Path(__file__).resolve().parent.parent  # kopi-cli/
    candidate = pkg_root.parent / "kopi-infra"         # kopi-tools/kopi-infra
    if (candidate / "docker-compose.yml").exists():
        return candidate

    raise FileNotFoundError(
        "Could not locate kopi-infra/docker-compose.yml. "
        "Set KOPI_INFRA_DIR env var or run from inside the kopi-tools workspace."
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
