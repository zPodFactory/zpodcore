#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "zpodsdk>=0.7.2",
#     "pydantic-settings>=2.6",
#     "httpx>=0.27",
#     "rich>=13.9",
# ]
# ///
"""Standalone cleanup sweep - removes any zpod/user/profile/permission_group
whose name starts with E2E_RESOURCE_PREFIX. Safe to run any time; mainly
useful after a pytest run was interrupted (Ctrl-C) and its own teardown
fixtures didn't get a chance to run.

`uv run scripts/cleanup.py` works standalone, no `uv sync` needed.
Pass --dry-run to see what would be removed without removing it.
"""

import argparse
import sys
from pathlib import Path

E2E_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(E2E_ROOT / "src"))

from rich.console import Console  # noqa: E402

from e2e.cleanup import print_sweep_result, sweep_e2e_resources  # noqa: E402
from e2e.client_factory import build_client  # noqa: E402
from e2e.config import ConfigError, load_settings  # noqa: E402

console = Console()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="List what would be removed, without removing it")
    parser.add_argument(
        "--include-failed", action="store_true",
        help="Also delete zpods stuck in DEPLOY_FAILED/DESTROY_FAILED (kept for inspection by default, "
        "same as E2E_KEEP_FAILED_RESOURCES=1 during a normal run)",
    )
    args = parser.parse_args()

    try:
        cfg = load_settings()
    except ConfigError as e:
        console.print(f"[red]Config error:[/red] {e}")
        return 1

    client = build_client(cfg.api_base_url, cfg.superadmin_token)
    keep_failed = cfg.keep_failed_resources and not args.include_failed

    console.print(f"Sweeping resources matching prefix '{cfg.resource_prefix}'" + (" (dry run)" if args.dry_run else ""))
    removed = sweep_e2e_resources(client, cfg.resource_prefix, dry_run=args.dry_run, keep_failed=keep_failed)
    print_sweep_result(removed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
