"""Resource sweep - removes anything the suite created and matching
E2E_RESOURCE_PREFIX. Used both as a session start/end pytest fixture and by
the standalone `scripts/cleanup.py` (for cleaning up after a crashed run).

Sweeps server-side resources (zpods, users, profiles, permission groups)
via the SDK. Ephemeral local `zcli` factory entries created for role
switching are tracked and removed explicitly by the fixtures that create
them (see conftest.py) rather than swept here - they're harmless local
config leftovers if a run crashes, unlike a stranded zpod consuming real
vCenter resources.

zPod deletion is status-gated: `zcli zpod create` (without --wait) and
`zpods_create.sync()` both return as soon as the zpod record is created,
well before deployment finishes - deleting a zpod that's still
PENDING/BUILDING/CONFIG_SCRIPTS races the in-progress deploy flow against
a destroy flow on the same zpod. Only ACTIVE/DEPLOY_FAILED/DESTROY_FAILED
(`e2e.status.ZPOD_TERMINAL`) are safe to delete.

Profile deletion is reference-gated: a Profile is only deleted once no zPod
uses it any more (`delete_unused_profiles`). The server doesn't enforce this
- `DELETE /profiles/{id}` has no in-use check - so deleting a throwaway
Profile while its zPods are still deploying succeeds, and leaves those zPods
pointing at a profile that no longer exists (zpodweb's build-progress hover,
for one, needs it).
"""

import time

from e2e import status
from e2e.client_factory import ZpodClient
from e2e.console import console

# A previous session's crashed run might have left a zpod mid-deploy; give
# it a short grace period to land on a terminal state rather than either
# blocking the sweep for a full deploy timeout or deleting it mid-build.
SWEEP_ZPOD_GRACE_SECONDS = 60
SWEEP_ZPOD_POLL_INTERVAL_SECONDS = 10
# How long the sweep waits for the zPod destroys it just started to finish
# before deciding a profile is still in use. A destroy takes about a minute.
SWEEP_PROFILE_WAIT_SECONDS = 600


def zpods_using_profiles(client: ZpodClient, profile_names) -> dict[str, list]:
    """The zPods still referencing each profile. `GET /zpods` already hides
    DELETED zPods, so anything it returns - deploying, ACTIVE, being
    destroyed, or kept back as DEPLOY_FAILED/DESTROY_FAILED - holds its profile."""
    using: dict[str, list] = {name: [] for name in profile_names}
    for zpod in client.zpods_get_all.sync() or []:
        if zpod.profile in using:
            using[zpod.profile].append(zpod)
    return using


def delete_unused_profiles(
    client: ZpodClient,
    profile_names,
    *,
    wait_seconds: float = 0,
    poll_interval: float = SWEEP_ZPOD_POLL_INTERVAL_SECONDS,
    dry_run: bool = False,
) -> tuple[list[str], dict[str, list[str]]]:
    """Delete each profile once no zPod references it.

    While some referencing zPod is still moving (deploying or being
    destroyed), wait up to `wait_seconds` for it to settle. A profile whose
    zPods all sit in a terminal state (ACTIVE, or DEPLOY_FAILED/DESTROY_FAILED
    kept for inspection) is left in place at once, without waiting.

    Returns (deleted, kept) where kept maps each profile left in place to
    the "name (STATUS)" of the zPods still using it.
    """
    pending = list(dict.fromkeys(profile_names))
    deleted: list[str] = []
    using: dict[str, list] = {}
    start = time.monotonic()
    while pending:
        using = zpods_using_profiles(client, pending)
        for name in [n for n in pending if not using[n]]:
            pending.remove(name)
            if dry_run:
                deleted.append(name)
                continue
            try:
                client.profiles_delete.sync(id=f"name={name}")
                deleted.append(name)
            except Exception:
                pass  # already gone, e.g. deleted by the test itself
        moving = any(z.status not in status.ZPOD_TERMINAL for n in pending for z in using[n])
        if not pending or dry_run or not moving or time.monotonic() - start >= wait_seconds:
            break
        time.sleep(poll_interval)
    kept = {name: [f"{z.name} ({z.status})" for z in using[name]] for name in pending}
    return deleted, kept


def _wait_for_zpod_terminal(client: ZpodClient, zpod):
    """Give a non-terminal zpod a short grace period to land on ACTIVE/DEPLOY_FAILED/
    DESTROY_FAILED, rather than either blocking for a full deploy timeout or
    treating it as safe to delete while it might still be mid-build."""
    current = zpod
    start = time.monotonic()
    while current.status not in status.ZPOD_TERMINAL and time.monotonic() - start < SWEEP_ZPOD_GRACE_SECONDS:
        time.sleep(SWEEP_ZPOD_POLL_INTERVAL_SECONDS)
        current = client.zpods_get.sync(id=f"name={zpod.name}")
    return current.status in status.ZPOD_TERMINAL


def _sweep_zpods(client: ZpodClient, zpods, removed: dict[str, list[str]], *, dry_run: bool, keep_failed: bool) -> None:
    terminal = [z for z in zpods if _wait_for_zpod_terminal(client, z)]
    terminal_names = {z.name for z in terminal}
    still_deploying = [z.name for z in zpods if z.name not in terminal_names]

    if keep_failed:
        # Re-fetch: _wait_for_zpod_terminal's grace-period loop only polls
        # occasionally, so `z` may be stale by the time it returns "terminal" -
        # need the real current status to sort ACTIVE from DEPLOY_FAILED/DESTROY_FAILED.
        current = [client.zpods_get.sync(id=f"name={z.name}") for z in terminal]
        deletable = [z.name for z in current if z.status in status.ZPOD_TERMINAL_SUCCESS]
        kept_failed = [z.name for z in current if z.status in status.ZPOD_TERMINAL_FAILURE]
    else:
        deletable = [z.name for z in terminal]
        kept_failed = []

    removed["zpods"] = deletable
    if kept_failed:
        removed["zpods (DEPLOY_FAILED/DESTROY_FAILED - kept for inspection)"] = kept_failed
    if still_deploying:
        removed["zpods (still deploying - left in place)"] = still_deploying
    if not dry_run:
        for name in deletable:
            client.zpods_delete.sync(id=f"name={name}")


def sweep_e2e_resources(
    client: ZpodClient, prefix: str, *, dry_run: bool = False, keep_failed: bool = True
) -> dict[str, list[str]]:
    if not prefix.strip():
        raise ValueError("refusing to sweep with an empty prefix: it would match every resource")

    def matching(items, name_attr: str):
        return [item for item in items if getattr(item, name_attr).startswith(prefix)]

    removed: dict[str, list[str]] = {}

    _sweep_zpods(client, matching(client.zpods_get_all.sync() or [], "name"), removed, dry_run=dry_run, keep_failed=keep_failed)

    users = matching(client.users_get_all.sync(all_=True) or [], "username")
    removed["users"] = [u.username for u in users]
    if not dry_run:
        for user in users:
            client.users_delete.sync(id=f"username={user.username}")

    profiles = matching(client.profiles_get_all.sync() or [], "name")
    # Waits for the destroys just requested above (their zPods still hold the
    # profile while DELETING); profiles of zPods left in place stay too.
    deleted, kept = delete_unused_profiles(
        client, [p.name for p in profiles], wait_seconds=SWEEP_PROFILE_WAIT_SECONDS, dry_run=dry_run
    )
    removed["profiles"] = deleted
    if kept:
        removed["profiles (still used by a zPod - left in place)"] = [
            f"{name}: {', '.join(users)}" for name, users in kept.items()
        ]

    groups = matching(client.permission_groups_get_all.sync() or [], "name")
    removed["permission_groups"] = [g.name for g in groups]
    if not dry_run:
        for group in groups:
            client.permission_groups_delete.sync(id=f"name={group.name}")

    return removed


def print_sweep_result(removed: dict[str, list[str]]) -> None:
    total = sum(len(v) for v in removed.values())
    if not total:
        console.print("[green]Nothing to clean up.[/green]")
        return
    for kind, names in removed.items():
        if names:
            console.print(f"[yellow]Removed {len(names)} {kind}:[/yellow] {', '.join(names)}")
