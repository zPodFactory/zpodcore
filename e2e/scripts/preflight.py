#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "zpodsdk~=0.9.2",
#     "pydantic-settings>=2.6",
#     "httpx>=0.27",
#     "rich>=13.9",
# ]
# ///
"""Standalone connectivity/auth check against the target zPodFactory server.

Runs the same checks the pytest suite's session-start fixture does, but as
a single file - `uv run scripts/preflight.py` works with zero `uv sync`,
useful for a quick sanity check before committing to a full test run.

Reads config the same way the suite does: from `.env` next to this script's
parent directory (see .env.sample).
"""

import sys
from pathlib import Path

E2E_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(E2E_ROOT / "src"))

import httpx  # noqa: E402
from rich.console import Console  # noqa: E402

from e2e.client_factory import build_client  # noqa: E402
from e2e.config import ConfigError, load_settings  # noqa: E402
from e2e.zssh import public_key_of  # noqa: E402

console = Console()


def _check_api_version(cfg) -> None:
    try:
        version = httpx.get(f"{cfg.api_base_url}/openapi.json", timeout=10).json()["info"]["version"]
        console.print(f"[green]OK[/green] zPod API {version}")
        if tuple(int(x) for x in version.split(".")[:2]) < (0, 9):
            console.print("[yellow]WARN[/yellow] networks/storage/NFS modules need a 0.9 server or later")
    except Exception as e:
        console.print(f"[yellow]WARN[/yellow] could not read the API version: {e}")


def _check_ssh_key(cfg, client) -> bool:
    key = cfg.zpod_ssh_key.expanduser()
    if not key.is_file():
        console.print(f"[yellow]WARN[/yellow] E2E_ZPOD_SSH_KEY {key} not found - on-host checks will be skipped")
        return True
    settings = client.settings_get_all.sync() or []
    server_key = next((s.value for s in settings if s.name == "zpodfactory_ssh_key"), "") or ""
    if public_key_of(key) in server_key:
        console.print(f"[green]OK[/green] {key} matches the zpodfactory_ssh_key setting")
        return True
    console.print(f"[red]FAIL[/red] {key} is not the key in the zpodfactory_ssh_key setting")
    return False


def main() -> int:
    console.print("[bold]e2e preflight[/bold]")

    try:
        cfg = load_settings()
    except ConfigError as e:
        console.print(f"[red]Config error:[/red] {e}")
        return 1
    console.print(f"  config loaded from {E2E_ROOT / '.env'}")

    client = build_client(cfg.api_base_url, cfg.superadmin_token)

    try:
        client.root_root.sync()
        console.print(f"[green]OK[/green] API reachable at {cfg.api_base_url}")
    except Exception as e:
        console.print(f"[red]FAIL[/red] API not reachable at {cfg.api_base_url}: {e}")
        return 1

    try:
        me = client.users_get_me.sync()
        if not me.superadmin:
            console.print(f"[red]FAIL[/red] token authenticates as '{me.username}' but is not a superadmin")
            return 1
        console.print(f"[green]OK[/green] token authenticates as superadmin '{me.username}'")
    except Exception as e:
        console.print(f"[red]FAIL[/red] token did not authenticate: {e}")
        return 1

    try:
        endpoints = client.endpoints_get_all.sync() or []
        match = next((e for e in endpoints if e.name == cfg.endpoint_name), None)
        if not match:
            console.print(f"[red]FAIL[/red] no endpoint named '{cfg.endpoint_name}' found")
            return 1
        console.print(f"[green]OK[/green] endpoint '{cfg.endpoint_name}' found (status={match.status})")
    except Exception as e:
        console.print(f"[red]FAIL[/red] could not list endpoints: {e}")
        return 1

    _check_api_version(cfg)
    if not _check_ssh_key(cfg, client):
        return 1

    console.print("[bold green]Preflight passed.[/bold green]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
