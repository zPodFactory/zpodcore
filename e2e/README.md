# zpodcore e2e tests

Live end-to-end test suite for [zPodFactory](https://zpodfactory.github.io). Drives
a real, already-running zPodFactory server through the real `zcli` CLI (and
the `zpodsdk` Python SDK where the CLI doesn't expose what's needed),
validating that zPod deployment, profiles, component library management,
DNS, settings, and the user/group/permission model actually work.

This directory depends on the published `zpodsdk`/`zpodcli` from PyPI,
pinned to the minor version of the server under test (`zcli X.Y.*` only
talks to an API `X.Y.*`), never on a local path into this repo, so it can
be copied into its own repository unchanged. Bump the `~=` pins in
`pyproject.toml` with each server minor release.

## On-host checks

The API answering `ACTIVE` proves a database row. The self-service modules
(`test_zcore_access.py`, `test_zpod_networks.py`, `test_zpod_storage.py`,
`test_zpod_component_options.py`) also log into the zPods they deploy and
check the real thing: the `eth1.<vlan>` interface and its address, the
nftables masquerade rule, the ext4 filesystem and its systemd mount unit,
`exportfs -v`, an NFS mount writing a file, a VM on a user VLAN reaching the
internet only with masquerade on.

They log in as root with the factory key (`E2E_ZPOD_SSH_KEY`, matching the
server's `zpodfactory_ssh_key` setting, checked at session start) and
`BatchMode=yes`, so no password can hide a broken key injection. VMs only
reachable inside a zPod are reached through zcore as a jump host. Each
remote command is a card in `report.html`.

Run them with `just selfservice` (or `just selfservice-fast`). They need a
server on 0.9 or later and a zcore image with zboxapi 0.2.1 or later
(`E2E_ZCORE_COMPONENT_UID`, default `zcore-13.7`).

## OVA staging off vs on

`test_ff_endpoint_ova_staging_toggle_both_deploy` (destructive) deploys a
profile with `ff_endpoint_ova_staging` off, then on, and puts a table in
`report.html`: each component's deploy time, the Prefect flow time and the
`zcli zpod create --wait` time, off vs on. It always runs the suite's
zcore-only profile; `E2E_OVA_STAGING_PROFILES` adds profiles from the server
(comma separated), one test each. The times are shown, not asserted. The
setting goes back to its original value afterwards.

## Quickstart

```bash
cp .env.sample .env      # fill in E2E_API_BASE_URL, E2E_SUPERADMIN_TOKEN, E2E_ENDPOINT_NAME at minimum
just sync
just preflight            # sanity-check connectivity/auth before running anything real
just smoke                # single minimal-zpod create/verify/delete cycle
```

`.python-version` pins Python 3.14, which `zpodcli` 0.9 requires. `uv sync`
downloads it if needed.

See `just --list` for all recipes.

## Markers

- `smoke`: one minimal zPod create/verify/delete, safe to run constantly.
- `slow`: at least one real deploy or download.
- `destructive`: changes shared state (settings, library components). Values
  are restored in teardown, but don't run these next to other work on the
  same server; `-m "not destructive"` leaves them out.
- `concurrency`: parallel multi-zPod batches, opt-in only.

Deploy, download and poll timeouts are `E2E_*_SECONDS` in `.env`.

## Cleanup

Every fixture tears down what it creates. A sweep at session start and end
also removes anything named with `E2E_RESOURCE_PREFIX` (default `e2e-`), so
an interrupted run leaves no orphans; `just cleanup` runs the same sweep by
hand. `E2E_KEEP_RESOURCES=1` skips teardown for post-mortem inspection.

A failed test shows its docstring, any diagnostic hint the test recorded and,
for flow failures, a Prefect UI link (`E2E_PREFECT_UI_URL`).

## Writing tests

Every test function:
- Has a one-line docstring stating what it validates - this is printed as
  the test's banner at run time, so keep it accurate.
- Keeps tunable values (profile name, component uid, timeouts) as plain
  variables near the top of the test, not buried in fixtures - it should be
  obvious what to edit to point the test at something else.
- Uses `assert x == y, "clear message"` - always include a message.
- Keeps the actual pass/fail check inline in the test body, not hidden
  inside a helper - fixtures set up state and clean up, they don't decide
  whether the test passed.

Profile JSON samples live in `tests/fixtures/profiles/*.json` - drop a file
in and profile-parametrized tests pick it up automatically, no code changes
needed.
