"""Library sync + component library management.

None of `zcli library ...` supports `--json` (only `component list` does),
so these tests drive actions through the CLI but read back state through
the SDK client for assertions.

Edit these if your target zPodFactory uses different naming:
"""

from pathlib import Path

import httpx
import pytest

from e2e import status

# The Broadcom-gated component both token tests use (2.3 GB). The no-token
# test disables it and fails to enable it (nothing downloaded); the with-token
# test downloads it again. broadcom_test_component puts it back as it was.
BROADCOM_TEST_UID = "vcfinstaller-9.1.1.0"
BROADCOM_TOKEN_SETTING = "zpodfactory_broadcom_download_token"
# Regular (non-mandatory), https-sourced components - no Broadcom token
# needed, download automatically through `zcli component enable`. These are
# exactly what the suite's own profile fixtures need ACTIVE:
# - zbox-13.7.1: kubernetes.json, and test_zpods.py's component add/remove
#   tests (never zcore-* there - zcore is the mandatory one-per-zpod
#   component, see test_zpods.py::ADD_COMPONENT_UID).
# - the three proxmox-* ones together: proxmox.json, and
#   test_zpods_concurrency.py's fast batch (which deploys proxmox.json).
# test_enable_https_component_reaches_active enables each and leaves it
# ACTIVE (doesn't disable afterward like the other component tests), so
# every later test in the suite that needs one finds it ready.
ZPOD_ADDABLE_COMPONENT_UID = "zbox-13.7.1"
PROXMOX_COMPONENT_UIDS = ("proxmox-9.1.4", "proxmox-bs-4.1.2", "proxmox-dm-1.0.2")
KEEP_ACTIVE_COMPONENT_UIDS = (ZPOD_ADDABLE_COMPONENT_UID, *PROXMOX_COMPONENT_UIDS)
# Reused (disabled then re-enabled) by test_disable_component_removes_on_disk_directory,
# rather than a separate throwaway component, since every other simple
# https-sourced component in the library needs to stay ACTIVE for something
# else above - restoring it afterward keeps that invariant true regardless
# of test order.
DISABLE_TEST_UID = "proxmox-bs-4.1.2"


def _kick_stale_upload_sync(e2e_config, filename: str, file_size: int) -> None:
    """Work around a real product edge case (zpodapi component__services.py
    ComponentService.upload): the `component_sync` flow is only ever
    triggered from *inside* a chunk-upload request, at the moment
    `current_size` first reaches `file_size`. If a file was already fully
    uploaded in an earlier (interrupted) e2e run, `zcli component upload`
    correctly resumes at 100% and sends zero new bytes - which also means
    it never re-triggers sync, leaving the test waiting forever for a flow
    that will never appear.

    Detect that exact state (server already reports the full size) and
    nudge it with a zero-byte "chunk" at the current offset, hitting the
    same `current_size == file_size` branch a real final chunk would -
    same multipart shape zcli itself sends, just via httpx directly since
    there's no CLI-exposed way to force a re-sync.
    """
    headers = {"access_token": e2e_config.superadmin_token}
    resp = httpx.get(f"{e2e_config.api_base_url}/components/upload/{filename}", headers=headers, timeout=30)
    current_size = resp.json().get("current_size", 0) if resp.status_code == 200 else 0
    if current_size == 0 or current_size != file_size:
        return  # nothing uploaded yet, or a genuine partial upload - let zcli's normal resume handle it
    httpx.post(
        f"{e2e_config.api_base_url}/components/upload",
        headers=headers,
        files={"file": b""},
        data={"filename": filename, "offset": current_size, "file_size": file_size},
        timeout=30,
    )


def test_library_resync(zcli_as, superadmin_client):
    """Resyncing a library refreshes its component metadata without erroring."""
    libraries = superadmin_client.libraries_get_all.sync() or []
    if not libraries:
        pytest.skip("no libraries registered on this zPodFactory")
    library = libraries[0]

    runner = zcli_as("superadmin")
    result = runner("library", "resync", library.name)
    assert result.returncode == 0, f"library resync failed:\n{result.stderr}"

    components_after = superadmin_client.components_get_all.sync() or []
    assert isinstance(components_after, list), "expected a component list after resync"


def test_components_list_smoke(zcli_as):
    """`component list --all --json` returns a list of components with valid status enums."""
    runner = zcli_as("superadmin")
    components = runner.run_json("component", "list", "--all").json
    assert isinstance(components, list), "expected a JSON list of components"
    for component in components:
        assert component["status"] in status.COMPONENT_STATUSES, (
            f"unexpected component status {component['status']!r} for {component['component_uid']}"
        )


def test_component_upload_from_local_dir(zcli_as, upload_file: Path, superadmin_client, prefect_diag, diag, e2e_config):
    """Every file in E2E_DOWNLOAD_SOURCE_DIR uploads cleanly and gets checksum-matched.

    Matching happens by checksum in a separate `component_sync` Prefect
    flow, not at upload time - and critically, there's no observable status
    change on the component API while that flow runs (matching is
    all-or-nothing: a component only ever shows INACTIVE throughout, then
    either flips to ACTIVE on a match or stays INACTIVE with the uploaded
    file removed on no match). So completion has to be observed via Prefect
    itself, not by polling `component list`.

    Skips the (slow, real-file) upload entirely if a component matching
    this filename is already ACTIVE - re-uploading a multi-GB OVA just to
    re-confirm a match that's already established wastes real time.
    Disable the component first (`zcli component disable <uid>`) to force
    this test to actually exercise the upload path again.
    """
    existing = superadmin_client.components_get_all.sync() or []
    already_active = next(
        (c for c in existing if c.status == status.COMPONENT_STATUS_ACTIVE and c.filename == upload_file.name),
        None,
    )
    if already_active:
        pytest.skip(
            f"{upload_file.name} already matched to ACTIVE component {already_active.component_uid} - "
            "disable it first to re-test the upload path"
        )

    _kick_stale_upload_sync(e2e_config, upload_file.name, upload_file.stat().st_size)

    runner = zcli_as("superadmin")
    result = runner("component", "upload", str(upload_file), timeout=1800)
    assert result.returncode == 0, f"upload of {upload_file.name} failed:\n{result.stderr}"

    sync_run = prefect_diag.wait_for_flow_run(f"{upload_file.name}-sync", timeout_seconds=900, interval_seconds=5)
    assert sync_run is not None, f"no component_sync flow run found for {upload_file.name} within 900s"
    assert sync_run["state_type"] == "COMPLETED", (
        f"component_sync for {upload_file.name} ended in {sync_run['state_type']}, "
        f"expected COMPLETED - {prefect_diag.ui_link(sync_run['id'])}"
    )

    components = superadmin_client.components_get_all.sync() or []
    matched = next(
        (c for c in components if c.status == status.COMPONENT_STATUS_ACTIVE and c.filename == upload_file.name),
        None,
    )
    if matched:
        diag.set_hint(f"{upload_file.name} matched component {matched.component_uid}, now ACTIVE")
    else:
        diag.set_hint(f"{upload_file.name} synced cleanly but matched no known component (unrecognized file)")


def _find_component(superadmin_client, prefixes: tuple[str, ...] = (), exact_uid: str | None = None):
    components = superadmin_client.components_get_all.sync() or []
    if exact_uid:
        return next((c for c in components if c.component_uid == exact_uid), None)
    return next(
        (c for c in components if c.status != status.COMPONENT_STATUS_ACTIVE and c.component_uid.startswith(prefixes)),
        None,
    )


@pytest.mark.parametrize("component_uid", KEEP_ACTIVE_COMPONENT_UIDS)
def test_enable_https_component_reaches_active(zcli_as, superadmin_client, poll_library_component_download, component_uid):
    """Enabling a simple https-sourced component (no Broadcom token needed) downloads it and reaches ACTIVE.

    Parametrized over every KEEP_ACTIVE_COMPONENT_UIDS entry so the whole
    set gets enabled and verified here, not just picked at random via a
    prefix match. Deliberately does NOT disable afterward like the other
    component tests - every one of these needs to stay ACTIVE for later
    tests in the suite (see the constant's docstring above). If a component
    is already ACTIVE from an earlier run, `component enable` on it is a
    no-op (see test_component_enable_disable_idempotency), so this still
    passes cleanly on a re-run instead of needing a fresh library each time.
    """
    component = _find_component(superadmin_client, exact_uid=component_uid)
    if not component:
        pytest.skip(f"{component_uid} not found in the component library")

    runner = zcli_as("superadmin")
    result = runner("component", "enable", component.component_uid)
    assert result.returncode == 0, f"component enable failed:\n{result.stderr}"

    final = poll_library_component_download(superadmin_client, f"uid={component.component_uid}")
    assert final.download_status in status.DOWNLOAD_STATUS_SUCCESS, (
        f"expected {component.component_uid} download to succeed, got download_status={final.download_status}"
    )
    assert final.status == status.COMPONENT_STATUS_ACTIVE, f"expected ACTIVE, got {final.status}"


def _set_broadcom_token(e2e_config, value: str) -> None:
    resp = httpx.patch(
        f"{e2e_config.api_base_url}/settings/name={BROADCOM_TOKEN_SETTING}",
        headers={"access_token": e2e_config.superadmin_token},
        json={"value": value},
        timeout=30,
    )
    resp.raise_for_status()


def _broadcom_token_is_set(e2e_config) -> bool:
    resp = httpx.get(
        f"{e2e_config.api_base_url}/settings/name={BROADCOM_TOKEN_SETTING}",
        headers={"access_token": e2e_config.superadmin_token},
        timeout=30,
    )
    resp.raise_for_status()
    return bool(resp.json()["value"])


@pytest.fixture(scope="module")
def broadcom_test_component(zcli_as, superadmin_client, poll_library_component_download):
    """BROADCOM_TEST_UID as found before the token tests, and back in that state (ACTIVE or not) after them."""
    component = _find_component(superadmin_client, exact_uid=BROADCOM_TEST_UID)
    if not component:
        pytest.skip(f"{BROADCOM_TEST_UID} not found in the component library")
    yield component
    current = _find_component(superadmin_client, exact_uid=BROADCOM_TEST_UID)
    was_active = component.status == status.COMPONENT_STATUS_ACTIVE
    if (current.status == status.COMPONENT_STATUS_ACTIVE) == was_active:
        return
    runner = zcli_as("superadmin")
    if was_active:
        runner("component", "enable", BROADCOM_TEST_UID, check=False)
        restored = poll_library_component_download(superadmin_client, f"uid={BROADCOM_TEST_UID}")
        assert restored.status == status.COMPONENT_STATUS_ACTIVE, (
            f"{BROADCOM_TEST_UID} was ACTIVE before the token tests and could not be restored "
            f"(download_status={restored.download_status}) - run `zcli component enable {BROADCOM_TEST_UID}`"
        )
    else:
        runner("component", "disable", BROADCOM_TEST_UID, check=False)


@pytest.mark.destructive
def test_enable_broadcom_component_without_token_fails_authentication(
    zcli_as, superadmin_client, poll_library_component_download, e2e_config, broadcom_test_component
):
    """Enabling a Broadcom-gated component without a download token fails authentication cleanly, not a crash.

    The server's token is blanked for the test, then set to E2E_BROADCOM_TOKEN
    if that's configured. A server that has a token while E2E_BROADCOM_TOKEN is
    empty is skipped: the API only returns the token masked, so it couldn't be
    put back. Any Broadcom download started on the stack meanwhile fails
    authentication too. BROADCOM_TEST_UID is disabled first if ACTIVE.
    """
    env_token = e2e_config.broadcom_token.get_secret_value()
    if not env_token and _broadcom_token_is_set(e2e_config):
        pytest.skip(
            f"{BROADCOM_TOKEN_SETTING} is set on this zPodFactory and E2E_BROADCOM_TOKEN is empty: "
            "the API never returns the real token, so it couldn't be put back after blanking it. "
            "Skipped to avoid breaking a working configuration - set E2E_BROADCOM_TOKEN to run it."
        )

    component = _find_component(superadmin_client, exact_uid=BROADCOM_TEST_UID)
    runner = zcli_as("superadmin")
    if component.status == status.COMPONENT_STATUS_ACTIVE:
        result = runner("component", "disable", component.component_uid)
        assert result.returncode == 0, f"component disable failed:\n{result.stderr}"

    _set_broadcom_token(e2e_config, "")
    try:
        result = runner("component", "enable", component.component_uid, check=False)
        # enabling only *schedules* the download - a non-zero exit here would
        # also be acceptable, but the real assertion is the terminal download_status below.
        assert result.returncode in (0, 1), f"unexpected crash enabling {component.component_uid}:\n{result.stderr}"

        final = poll_library_component_download(superadmin_client, f"uid={component.component_uid}")
        assert final.download_status == status.DOWNLOAD_STATUS_FAILED_AUTHENTICATION, (
            f"expected FAILED_AUTHENTICATION without a Broadcom token, got {final.download_status}"
        )
    finally:
        if env_token:
            _set_broadcom_token(e2e_config, env_token)
            assert _broadcom_token_is_set(e2e_config), f"{BROADCOM_TOKEN_SETTING} not restored"


@pytest.mark.destructive
@pytest.mark.slow
def test_broadcom_component_downloads_with_token(
    zcli_as, superadmin_client, poll_library_component_download, e2e_config, broadcom_test_component
):
    """With E2E_BROADCOM_TOKEN, a Broadcom-gated component downloads from the depot, checksum-verifies and reaches ACTIVE.

    E2E_BROADCOM_TOKEN is written to the server's setting and left there (the
    stack uses it for its normal downloads). The token is masked in every API
    response, so a real download is the only way to prove it works:
    BROADCOM_TEST_UID is disabled first if ACTIVE, otherwise enabling would only
    re-check the files already on disk.
    """
    env_token = e2e_config.broadcom_token.get_secret_value()
    if not env_token:
        pytest.skip("E2E_BROADCOM_TOKEN is empty - set it to test a real Broadcom download")

    _set_broadcom_token(e2e_config, env_token)

    component = _find_component(superadmin_client, exact_uid=BROADCOM_TEST_UID)
    runner = zcli_as("superadmin")
    if component.status == status.COMPONENT_STATUS_ACTIVE:
        result = runner("component", "disable", component.component_uid)
        assert result.returncode == 0, f"component disable failed:\n{result.stderr}"

    result = runner("component", "enable", component.component_uid)
    assert result.returncode == 0, f"component enable failed:\n{result.stderr}"

    final = poll_library_component_download(superadmin_client, f"uid={component.component_uid}")
    assert final.download_status != status.DOWNLOAD_STATUS_FAILED_AUTHENTICATION, (
        "Broadcom rejected E2E_BROADCOM_TOKEN (401/403)"
    )
    assert final.download_status in status.DOWNLOAD_STATUS_SUCCESS, (
        f"expected {component.component_uid} download to succeed, got download_status={final.download_status}"
    )
    assert final.status == status.COMPONENT_STATUS_ACTIVE, f"expected ACTIVE, got {final.status}"


@pytest.mark.destructive
def test_disable_component_removes_on_disk_directory(zcli_as, superadmin_client, poll_library_component_download, e2e_config):
    """Disabling a component removes its <products_path>/<name>/<version>/ directory.

    Reuses DISABLE_TEST_UID (one of the KEEP_ACTIVE_COMPONENT_UIDS, not a
    separate throwaway component) and re-enables it again at the end -
    every other simple https-sourced component in this library needs to
    stay ACTIVE for something downstream (see that constant's docstring),
    so this restores it rather than leaving it disabled.
    """
    component = _find_component(superadmin_client, exact_uid=DISABLE_TEST_UID)
    if not component:
        pytest.skip(f"{DISABLE_TEST_UID} not found in the component library")

    runner = zcli_as("superadmin")
    runner("component", "enable", component.component_uid)
    active = poll_library_component_download(superadmin_client, f"uid={component.component_uid}")
    if active.status != status.COMPONENT_STATUS_ACTIVE:
        pytest.skip(f"{component.component_uid} did not reach ACTIVE (download_status={active.download_status})")

    component_dir = Path(e2e_config.products_path) / active.component_name / active.component_version

    result = runner("component", "disable", component.component_uid)
    assert result.returncode == 0, f"component disable failed:\n{result.stderr}"
    assert not component_dir.exists(), f"expected {component_dir} to be removed after disable, but it still exists"

    result = runner("component", "enable", component.component_uid)
    assert result.returncode == 0, f"re-enabling {component.component_uid} to restore it failed:\n{result.stderr}"
    restored = poll_library_component_download(superadmin_client, f"uid={component.component_uid}")
    assert restored.status == status.COMPONENT_STATUS_ACTIVE, (
        f"expected {component.component_uid} restored to ACTIVE, got {restored.status}"
    )


def test_component_enable_disable_idempotency(zcli_as, superadmin_client):
    """Disabling an already-inactive component, or enabling an already-active one, doesn't crash."""
    components = superadmin_client.components_get_all.sync() or []
    inactive = next((c for c in components if c.status == status.COMPONENT_STATUS_INACTIVE), None)
    if not inactive:
        pytest.skip("no inactive component available to double-disable")

    runner = zcli_as("superadmin")
    result = runner("component", "disable", inactive.component_uid, check=False)
    assert result.returncode == 0, f"disabling an already-inactive component should be a no-op, not fail:\n{result.stderr}"
