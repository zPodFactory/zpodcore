"""Concurrent multi-zpod deploy batches.

Split into two tiers so an operator doesn't have to wait ~1h for
vcsa/nsx-heavy profiles just to get concurrency coverage on everything
else:
- `test_concurrent_batch_deploy_fast` (FAST_PROFILES): zcore, proxmox,
  kubernetes, vcf902, vcf910 - no vcsa/nsx component, deploys in minutes.
  Runs by default (`just full` / `just concurrency`).
- `test_concurrent_batch_deploy_slow` (SLOW_PROFILES): vcd-prod, base8 -
  vcsa/nsx-heavy, ~1h per zpod. Opt-in only (`just concurrency-slow`),
  excluded from `just full` via the `slow` marker.

Both are deliberately SDK-direct, not CLI: N simultaneous `zcli`
subprocesses would race on the local factory config file, which would test
a client-side bug instead of the server/Prefect concurrency this test
exists to catch.

Edit FAST_PROFILES/SLOW_PROFILES/REPLICAS_PER_PROFILE/REPLICA_OVERRIDES to
change which profile fixtures are used or how many replicas are deployed
at once.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pytest

from e2e import status
from e2e.cleanup import delete_unused_profiles
from e2e.console import console
from e2e.insight import Beat, Insight
from e2e.polling import (
    PollFailureError,
    PollTimeoutError,
    poll_zpod_deleted,
    poll_zpod_status,
)
from e2e.profiles import load_profile_items, profile_body

REPLICAS_PER_PROFILE = 3
FAST_PROFILES = ["zcore", "proxmox", "kubernetes", "vcf902", "vcf910"]
SLOW_PROFILES = ["vcd-prod", "base8"]
# Per-profile override for REPLICAS_PER_PROFILE - vcf902/vcf910 each deploy
# 3x nested esxi-9.x hosts (real VMs, not lightweight VMs like zcore/proxmox),
# and 3 concurrent replicas of both at once was enough to blow past
# vCenter's real per-host vCPU ceiling (vim.fault.NumVirtualCpusExceedsLimit,
# maxSupportedVcpus=160) - confirmed live. One replica each is still real
# concurrency coverage (interleaved with the other profiles' replicas)
# without exceeding host capacity.
REPLICA_OVERRIDES = {"vcf902": 1, "vcf910": 1}


def _select_profile_files(available_profile_files: list[Path], stems: list[str]) -> dict[str, Path]:
    by_stem = {p.stem: p for p in available_profile_files}
    return {stem: by_stem[stem] for stem in stems if stem in by_stem}


def _run_concurrent_batch(
    stems: list[str],
    superadmin_client, endpoint, available_profile_files, namer, e2e_config, keep_resources,
    deploy_timeout_seconds: int,
) -> None:
    """Shared implementation for both tiers: create one throwaway Profile
    per selected fixture, deploy REPLICAS_PER_PROFILE zpods per profile
    (or REPLICA_OVERRIDES[stem], if set) all at once, and assert every one
    reached a terminal success state."""
    from zpodsdk.models.zpod_create import ZpodCreate

    selected = _select_profile_files(available_profile_files, stems)
    missing = [s for s in stems if s not in selected]
    if missing:
        pytest.skip(f"missing profile fixture(s) {missing} in tests/fixtures/profiles/")

    deploy_timeout = deploy_timeout_seconds
    poll_interval = e2e_config.poll_interval_seconds

    # One throwaway Profile record per selected fixture.
    profile_names = {}
    for stem, path in selected.items():
        name = namer(f"profile-{stem}")
        superadmin_client.profiles_create.sync(body=profile_body(name, load_profile_items(path)))
        profile_names[stem] = name

    jobs = [
        (stem, i)
        for stem in profile_names
        for i in range(1, REPLICA_OVERRIDES.get(stem, REPLICAS_PER_PROFILE) + 1)
    ]

    def deploy_one(stem: str, idx: int):
        zpod_name = namer(f"{stem}-{idx:02d}")
        try:
            superadmin_client.zpods_create.sync(
                body=ZpodCreate(name=zpod_name, endpoint_id=endpoint.id, profile=profile_names[stem])
            )
            poll_zpod_status(
                superadmin_client, f"name={zpod_name}", timeout_seconds=deploy_timeout, interval_seconds=poll_interval
            )
            return ("ok", zpod_name, None)
        except PollFailureError as e:
            # Reached a real terminal failure state (DEPLOY_FAILED) - safe to delete.
            return ("failed", zpod_name, str(e))
        except PollTimeoutError as e:
            # Timed out without confirming a terminal state - NOT safe to
            # blind-delete, it may still be mid-deploy. _teardown re-checks
            # status before deciding what to do with these.
            return ("timeout", zpod_name, str(e))
        except Exception as e:  # noqa: BLE001 - a worker exception must never abort the other workers
            return ("timeout", zpod_name, str(e))

    max_workers = min(e2e_config.concurrency_max_workers, len(jobs))
    results: dict[str, tuple[str, str | None]] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(deploy_one, stem, i): (stem, i) for stem, i in jobs}
        for future in as_completed(futures):
            outcome, zpod_name, detail = future.result()
            results[zpod_name] = (outcome, detail)

    if not keep_resources:
        _teardown(
            results, superadmin_client, profile_names, deploy_timeout, poll_interval, max_workers,
            keep_failed=e2e_config.keep_failed_resources,
        )

    failures = {name: detail for name, (outcome, detail) in results.items() if outcome in ("failed", "timeout")}
    if failures:
        breakdown = "\n".join(f"  {name}: {detail}" for name, detail in failures.items())
        pytest.fail(f"{len(failures)}/{len(jobs)} concurrent deploys failed:\n{breakdown}")

    assert len(results) == len(jobs), f"expected {len(jobs)} deploy results, got {len(results)}"


# Narrative metadata for the HTML report, keyed by test function name - see
# e2e.insight. Purely decorative: never read by the tests below, only
# pulled by report.py at render time.
INSIGHTS = {
    "test_concurrent_batch_deploy_fast": Insight(
        why="Deploying zpods one at a time can never catch a race - DB contention, dnsmasq "
            "config-file writes, or NSX/vCenter resource limits that only bite when several deploy "
            "flows run at the exact same moment.",
        reasoning="REPLICA_OVERRIDES exists because this test found a real one: at "
                  "REPLICAS_PER_PROFILE=3 for every profile including vcf902/vcf910 (each running "
                  "3x nested esxi-9.x hosts), 15 simultaneous deploys pushed one physical host over "
                  "vCenter's real 160-vCPU ceiling. Confirmed live via the flow run's own Prefect "
                  "logs, not guessed - see the cascade below.",
        expected="All FAST_PROFILES deploy to ACTIVE concurrently, within the real vCPU budget the "
                 "reduced replica counts leave headroom for.",
        beats=[
            Beat("15 zpods at once", "REPLICAS_PER_PROFILE=3 for all 5 profiles", state="", color="info", tag="WHAT WE TRIED FIRST"),
            Beat("5/15 DEPLOY_FAILED", "vcf902/vcf910/kubernetes zpods", state="FAILED", color="fail", tag="WHAT YOU SEE"),
            Beat("Prefect flow logs", "vim.fault.NumVirtualCpusExceedsLimit", state="maxSupportedVcpus=160", color="fail", tag="ROOT CAUSE"),
            Beat("REPLICA_OVERRIDES", "vcf902/vcf910 down to 1 replica each", state="11 zpods", color="pass", tag="THE FIX"),
        ],
    ),
}


@pytest.mark.concurrency
def test_concurrent_batch_deploy_fast(superadmin_client, endpoint, available_profile_files, namer, e2e_config, keep_resources):
    """Deploy REPLICAS_PER_PROFILE zpods for each of FAST_PROFILES, all at once.

    What this validates: the server correctly handles many simultaneous
    `flow_zpod_deploy` runs without cross-talk - DB races, dnsmasq
    config-file races, NSX/vCenter resource contention, etc. - using
    profiles with no vcsa/nsx component, so the whole batch deploys in
    minutes. Runs by default; see test_concurrent_batch_deploy_slow for the
    vcsa/nsx-heavy tier, which is opt-in only.
    """
    _run_concurrent_batch(
        FAST_PROFILES, superadmin_client, endpoint, available_profile_files, namer, e2e_config, keep_resources,
        e2e_config.deploy_timeout_seconds,
    )


@pytest.mark.concurrency
@pytest.mark.slow
def test_concurrent_batch_deploy_slow(superadmin_client, endpoint, available_profile_files, namer, e2e_config, keep_resources):
    """Deploy REPLICAS_PER_PROFILE zpods for each of SLOW_PROFILES, all at once.

    Same coverage as test_concurrent_batch_deploy_fast, but for the
    vcsa/nsx-heavy profiles (~1h per zpod) - kept opt-in
    (`just concurrency-slow`) and excluded from `just full` so a normal run
    doesn't have to wait an hour for this tier. Each deploy gets
    E2E_SLOW_DEPLOY_TIMEOUT_SECONDS instead of E2E_DEPLOY_TIMEOUT_SECONDS.
    """
    _run_concurrent_batch(
        SLOW_PROFILES, superadmin_client, endpoint, available_profile_files, namer, e2e_config, keep_resources,
        e2e_config.slow_deploy_timeout_seconds,
    )


def _teardown(
    results: dict[str, tuple[str, str | None]], client, profile_names, deploy_timeout, poll_interval, max_workers,
    *, keep_failed: bool,
) -> None:
    """Best-effort parallel teardown for every zpod, regardless of overall
    pass/fail - one stuck delete must not block cleanup of the rest.

    Always re-checks live status rather than trusting `deploy_one`'s
    recorded outcome, since a "timeout" outcome means the poll gave up
    without confirming a terminal state - deleting it outright would race
    an in-progress deploy flow with a destroy flow on the same zpod.

    When `keep_failed` is true (the default - see
    e2e_config.keep_failed_resources), a zpod that reached DEPLOY_FAILED or
    DESTROY_FAILED is left in place for an operator to actually inspect
    (vCenter console, Prefect logs) instead of being torn down like a
    successful one - only ACTIVE zpods get deleted.

    A zpod still deploying when its own poll gave up is waited on (up to
    another `deploy_timeout`) instead of skipped, so its Profile isn't
    pulled out from under it. Each throwaway Profile is deleted only once
    no zpod references it (`delete_unused_profiles`): the server would
    accept the delete anyway, since `DELETE /profiles` has no in-use check.
    A profile still used by a kept-back failed zpod, or by one that never
    finished, stays for the session sweep.
    """

    def teardown_one(zpod_name: str) -> None:
        try:
            current = client.zpods_get.sync(id=f"name={zpod_name}")
            if current.status not in status.ZPOD_TERMINAL:
                # Still deploying: wait for it to finish rather than leave it
                # (and its profile) behind mid-build.
                try:
                    current = poll_zpod_status(
                        client, f"name={zpod_name}", timeout_seconds=deploy_timeout, interval_seconds=poll_interval
                    )
                except PollFailureError:
                    current = client.zpods_get.sync(id=f"name={zpod_name}")
                except PollTimeoutError:
                    return  # never finished - left in place, the session sweep re-checks it
            if keep_failed and current.status in status.ZPOD_TERMINAL_FAILURE:
                return  # left in place for inspection
            client.zpods_delete.sync(id=f"name={zpod_name}")
            poll_zpod_deleted(client, f"name={zpod_name}", timeout_seconds=deploy_timeout, interval_seconds=poll_interval)
        except Exception:
            pass

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        list(pool.map(teardown_one, results.keys()))

    _, kept = delete_unused_profiles(
        client, profile_names.values(), wait_seconds=deploy_timeout, poll_interval=poll_interval
    )
    for profile_name, users in kept.items():
        console.print(f"[yellow]profile {profile_name} left in place, still used by: {', '.join(users)}[/yellow]")
