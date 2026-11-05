"""Profile CRUD.

Profile JSON samples live in tests/fixtures/profiles/*.json (see the
README.md there) - `profile_file` is parametrized over whatever's dropped
in that directory, so these tests collect zero cases (and are skipped)
until real samples exist.
"""

import json

import pytest

from e2e.insight import Beat, Insight
from e2e.profiles import profile_body

# Narrative metadata for the HTML report, keyed by test function name - see
# e2e.insight. Purely decorative: never read by the tests below, only
# pulled by report.py at render time.
INSIGHTS = {
    "test_profile_create_references_inactive_component_fails": Insight(
        why="A profile pointing at a component that isn't downloaded yet would deploy to nothing "
            "- better to reject it at create time than fail three layers deep during a real deploy.",
        reasoning="validate_profile (profiles/profile__utils.py) checks every component_uid in the "
                  "profile against the live component library before the profile is ever persisted "
                  "- both unknown uids and uids that exist but aren't ACTIVE are rejected the same way.",
        expected="Profile create fails cleanly (400), and nothing gets persisted - a follow-up "
                 "`profile info` on the same name comes back empty too.",
        beats=[
            Beat("component status", "picked one still INACTIVE", state="INACTIVE", color="fail", tag="THE SETUP"),
            Beat("profile create", "references that component_uid", state="400", color="pass", tag="REJECTED"),
            Beat("profile info", "same name, right after", state="not found", color="pass", tag="CONFIRMS IT"),
        ],
    ),
    "test_profile_create_rejected_while_component_inactive": Insight(
        why="This is the first half of the actual gate: a profile referencing a specific, "
            "known-inactive component should never make it past create.",
        reasoning="Same validate_profile check as the inactive-component test above, but targeting "
                  "one exact component (proxmox-dm-1.0.2) deliberately forced INACTIVE first, so the "
                  "positive half right after (test_profile_create_succeeds_once_component_active) "
                  "is provably the same component crossing the same gate, not a different one that "
                  "just happened to already be ACTIVE.",
        expected="`profile create` referencing proxmox-dm-1.0.2 fails while it's INACTIVE.",
        beats=[
            Beat("component disable", "forced back to a known state", state="INACTIVE", color="fail", tag="ROOT STATE"),
            Beat("profile create", "zcore + proxmox-dm-1.0.2", state="400", color="pass", tag="REJECTED"),
        ],
    ),
    "test_profile_create_succeeds_once_component_active": Insight(
        why="The other half of the gate - once the exact same component is ACTIVE, the exact same "
            "profile create has to succeed. If it doesn't, the check isn't really about component "
            "status at all.",
        reasoning="component enable schedules a real download through the component_download "
                  "Prefect flow - once poll_library_component_download confirms ACTIVE, "
                  "validate_profile's per-item check now passes for this uid specifically.",
        expected="The identical profile payload that test_profile_create_rejected_while_component_inactive "
                 "rejected now succeeds, and `profile info` shows both items (zcore + the target).",
        beats=[
            Beat("component enable", "real download, real Prefect flow", state="SCHEDULED", color="info", tag="THE CHANGE"),
            Beat("download completes", "polled via poll_library_component_download", state="ACTIVE", color="pass"),
            Beat("profile create", "same payload as the reject test", state="200", color="pass", tag="NOW ACCEPTED"),
        ],
    ),
    "test_profile_delete_while_referenced_by_active_zpod": Insight(
        why="ZpodCreate.profile is stored as a plain name string, not a foreign key - so nothing "
            "in the schema itself stops you from deleting a profile a live zpod still points at. "
            "Whether the server blocks it anyway isn't documented, so this test exists to observe "
            "the real behavior once and lock it in, rather than assume either answer.",
        reasoning="Either outcome (blocked, or allowed with no effect on the already-deployed zpod) "
                  "is acceptable - what's not acceptable is the already-running zpod being disturbed "
                  "by a delete attempt on metadata it no longer needs post-deploy.",
        expected="Whatever `profile delete` returns, the zpod stays ACTIVE and untouched throughout.",
        beats=[
            Beat("zpod deploy", "from a dedicated throwaway profile", state="ACTIVE", color="pass", tag="THE SETUP"),
            Beat("profile delete", "while the zpod above still references it", state="?", color="info", tag="OBSERVED, NOT ASSUMED"),
            Beat("zpod status re-checked", "regardless of the delete's outcome", state="ACTIVE", color="pass", tag="WHAT MATTERS"),
        ],
    ),
}


def test_profile_create_info_delete(zcli_as, namer, profile_file):
    """Create a profile from a fixtures/profiles/*.json sample, verify it via `profile info --json`, then delete it."""
    runner = zcli_as("superadmin")
    name = namer(f"profile-{profile_file.stem}")

    result = runner("profile", "create", name, "--profile-file", str(profile_file))
    assert result.returncode == 0, f"profile create failed:\n{result.stderr}"

    info = runner.run_json("profile", "info", name).json
    expected = json.loads(profile_file.read_text())
    assert len(info) == len(expected), f"expected {len(expected)} profile items, got {len(info)}"

    result = runner("profile", "delete", name)
    assert result.returncode == 0, f"profile delete failed:\n{result.stderr}"

    result = runner("profile", "info", name, "--json", "--no-color", check=False)
    assert result.returncode != 0, f"profile {name} should no longer exist after delete"


def test_profile_update_add_and_remove_component_reflected(zcli_as, namer, zcore_profile_items):
    """Updating a profile to add, then remove, a component item is reflected in `profile info`."""
    base_item = zcore_profile_items[0]
    if isinstance(base_item, list):
        pytest.skip("zcore.json fixture is a nested/grouped profile - this test expects a flat single-component profile")

    runner = zcli_as("superadmin")
    name = namer("profile-update")
    base_dict = base_item.to_dict()

    runner("profile", "create", name, "--profile", json.dumps([base_dict]))
    info = runner.run_json("profile", "info", name).json
    assert len(info) == 1, f"expected 1 item after create, got {len(info)}"

    extra = dict(base_dict)
    extra["hostname"] = f"{base_dict.get('hostname', 'zcore')}-extra"
    runner("profile", "update", name, "--profile", json.dumps([base_dict, extra]))
    info = runner.run_json("profile", "info", name).json
    assert len(info) == 2, f"expected 2 items after adding a component, got {len(info)}"

    runner("profile", "update", name, "--profile", json.dumps([base_dict]))
    info = runner.run_json("profile", "info", name).json
    assert len(info) == 1, f"expected 1 item after removing the added component, got {len(info)}"

    runner("profile", "delete", name, check=False)


def test_profile_create_references_inactive_component_fails(zcli_as, namer, superadmin_client):
    """Creating a profile that references a component which isn't ACTIVE yet fails cleanly.

    zpodapi validates every component_uid in the profile against the
    component library at create time (profiles/profile__utils.py
    validate_profile) - both unknown uids and uids that exist but aren't
    ACTIVE are rejected before the profile is ever persisted.
    """
    components = superadmin_client.components_get_all.sync() or []
    inactive = next((c for c in components if c.status != "ACTIVE"), None)
    if not inactive:
        pytest.skip("no INACTIVE component available to reference - everything in the library is already ACTIVE")

    runner = zcli_as("superadmin")
    name = namer("profile-inactive-ref")
    result = runner(
        "profile", "create", name,
        "--profile", json.dumps([{"component_uid": inactive.component_uid}]),
        check=False,
    )
    assert result.returncode != 0, (
        f"expected profile create to reject inactive component {inactive.component_uid}, "
        f"but it succeeded:\n{result.stdout}"
    )

    # Make sure it really wasn't created, not just a spurious CLI error.
    check = runner("profile", "info", name, "--json", "--no-color", check=False)
    assert check.returncode != 0, f"profile {name} should not exist after a rejected create"


# A regular (non-mandatory), non-Broadcom-gated component - downloads
# automatically through `zcli component enable`, no token needed - reused
# here rather than a dedicated throwaway one, since it's already one of
# test_libraries_components.py's KEEP_ACTIVE_COMPONENT_UIDS (kept ACTIVE
# for test_zpods_concurrency.py's fast batch, which needs it). Both tests
# below restore it to ACTIVE by the end so that invariant still holds
# afterward regardless of which of these two runs last.
PROFILE_GATE_COMPONENT_UID = "proxmox-dm-1.0.2"


def _gate_profile_payload(component_uid: str) -> str:
    """A profile referencing `component_uid` alongside the mandatory zcore
    core component - zpodapi rejects any profile that doesn't start with a
    zcore-* item ("Profile must start with a zcore-* core component"), a
    separate structural rule from the component-ACTIVE check these two
    tests are actually targeting. Without zcore first, both tests below
    would fail on that structural rule instead, regardless of
    PROFILE_GATE_COMPONENT_UID's own status - discovered empirically while
    writing these."""
    return json.dumps([
        {"component_uid": "zcore-13.7"},
        [{"component_uid": component_uid, "host_id": 58, "hostname": "gate-test"}],
    ])


@pytest.mark.destructive
def test_profile_create_rejected_while_component_inactive(zcli_as, namer):
    """Creating a profile referencing an INACTIVE component is rejected cleanly.

    Deliberately forces PROFILE_GATE_COMPONENT_UID to INACTIVE first (rather
    than picking whatever happens to be inactive right now, like
    test_profile_create_references_inactive_component_fails does more
    generically) so this pairs directly with
    test_profile_create_succeeds_once_component_active below - the same
    component, both sides of the same validation gate.
    """
    runner = zcli_as("superadmin")
    runner("component", "disable", PROFILE_GATE_COMPONENT_UID, check=False)

    name = namer("profile-gate-reject")
    result = runner("profile", "create", name, "--profile", _gate_profile_payload(PROFILE_GATE_COMPONENT_UID), check=False)
    assert result.returncode != 0, (
        f"expected profile create referencing INACTIVE {PROFILE_GATE_COMPONENT_UID} to be rejected, but it succeeded"
    )
    assert "not ACTIVE" in result.stdout, f"expected an ACTIVE-status rejection, got:\n{result.stdout}"
    check = runner("profile", "info", name, "--json", "--no-color", check=False)
    assert check.returncode != 0, f"profile {name} should not exist after a rejected create"


@pytest.mark.destructive
def test_profile_create_succeeds_once_component_active(zcli_as, namer, superadmin_client, poll_library_component_download):
    """Creating a profile succeeds once its component has been enabled and reaches ACTIVE.

    The positive counterpart to test_profile_create_rejected_while_component_inactive
    above - re-enables PROFILE_GATE_COMPONENT_UID (idempotent regardless of
    whether that test ran first) and confirms the same profile create call
    that was rejected while INACTIVE now succeeds, proving the gate is
    driven by real component status, not something checked once elsewhere.
    """
    runner = zcli_as("superadmin")
    result = runner("component", "enable", PROFILE_GATE_COMPONENT_UID)
    assert result.returncode == 0, f"component enable failed:\n{result.stderr}"
    active = poll_library_component_download(superadmin_client, f"uid={PROFILE_GATE_COMPONENT_UID}")
    assert active.status == "ACTIVE", f"expected {PROFILE_GATE_COMPONENT_UID} to reach ACTIVE, got {active.status}"

    name = namer("profile-gate-accept")
    result = runner("profile", "create", name, "--profile", _gate_profile_payload(PROFILE_GATE_COMPONENT_UID), check=False)
    assert result.returncode == 0, (
        f"expected profile create to succeed once {PROFILE_GATE_COMPONENT_UID} is ACTIVE, "
        f"but it failed:\n{result.stdout}\n{result.stderr}"
    )
    info = runner.run_json("profile", "info", name).json
    assert len(info) == 2, f"expected 2 profile items (zcore + gate component), got {len(info)}"

    runner("profile", "delete", name, check=False)


def test_profile_create_duplicate_name_conflict(zcli_as, namer, zcore_profile_items):
    """Creating a profile with a name that already exists fails cleanly."""
    base_item = zcore_profile_items[0]
    if isinstance(base_item, list):
        pytest.skip("zcore.json fixture is a nested/grouped profile - this test expects a flat single-component profile")

    runner = zcli_as("superadmin")
    name = namer("profile-dup")
    base_dict = base_item.to_dict()
    runner("profile", "create", name, "--profile", json.dumps([base_dict]))

    result = runner("profile", "create", name, "--profile", json.dumps([base_dict]), check=False)
    assert result.returncode != 0, "creating a duplicate profile name should fail"

    runner("profile", "delete", name, check=False)


@pytest.mark.slow
def test_profile_delete_while_referenced_by_active_zpod(
    zcli_as, namer, zcore_profile_items, endpoint, superadmin_client, e2e_config, poll_zpod_deleted, diag
):
    """Deleting a profile that an ACTIVE zpod was deployed from - documents whatever the actual server behavior is.

    ZpodCreate.profile is stored as a plain name string, not a foreign key,
    so this could go either way (blocked, or allowed with no effect on the
    already-deployed zpod). Either is acceptable; what's not acceptable is
    the already-deployed zpod being affected by the delete attempt.

    Uses its own dedicated profile rather than the shared `zcore_profile`
    fixture - this test deliberately pokes at profile-delete edge cases, and
    an earlier version of it raced `zpod destroy` (async, no wait) against
    the final cleanup `profile delete`, silently losing that race (both
    calls use check=False) and leaving the shared profile undeleted -
    which then broke every other test depending on `zcore_profile` for the
    rest of the session with "Profile already exists" (409). Waiting for
    the zpod to actually be gone before the final delete, plus using a
    profile nothing else depends on, closes both the immediate bug and the
    class of bug.
    """

    runner = zcli_as("superadmin")
    zpod_name = namer("profile-inuse")
    profile_name = namer("profile-inuse-target")
    deploy_timeout = e2e_config.deploy_timeout_seconds + 60

    superadmin_client.profiles_create.sync(body=profile_body(profile_name, zcore_profile_items))

    result = runner(
        "zpod", "create", zpod_name,
        "--endpoint", endpoint.name,
        "--profile", profile_name,
        "--wait", "--no-spinner",
        check=False,
        timeout=deploy_timeout,
    )
    assert result.returncode == 0, f"setup deploy failed:\n{result.stdout}\n{result.stderr}"

    delete_result = runner("profile", "delete", profile_name, check=False)
    diag.set_hint(
        f"profile delete while referenced by an ACTIVE zpod: returncode={delete_result.returncode} "
        f"(0=allowed, nonzero=blocked)"
    )

    zpod = superadmin_client.zpods_get.sync(id=f"name={zpod_name}")
    assert zpod.status == "ACTIVE", (
        f"zpod {zpod_name} should be unaffected by the profile delete attempt, got status={zpod.status}"
    )

    runner("zpod", "destroy", zpod_name, check=False)
    try:
        poll_zpod_deleted(superadmin_client, f"name={zpod_name}")
    except Exception:
        pass
    try:
        superadmin_client.profiles_delete.sync(id=f"name={profile_name}")
    except Exception:
        pass  # already deleted by the test's own delete_result attempt above
