"""zPod lifecycle: create, verify, add/remove a component, delete.

Edit this if your library has no simple https-sourced component available:
"""

import pytest

from e2e import status
from e2e.insight import Beat, Insight
from e2e.profiles import profile_body

# zbox-13.7.1 only - never zcore-*: zcore is the mandatory core component
# every zpod already gets exactly one of at deploy time, so adding a second
# one would conflict with that uniqueness constraint. zbox is a regular,
# addable-more-than-once component, which is what these tests need.
ADD_COMPONENT_UID = "zbox-13.7.1"
ADD_COMPONENT_HOST_ID = 50

# Narrative metadata for the HTML report, keyed by test function name - see
# e2e.insight. Purely decorative: never read by the tests below, only
# pulled by report.py at render time.
INSIGHTS = {
    "test_create_minimal_zcore_zpod_smoke": Insight(
        why="If the fastest, simplest possible deploy doesn't work, nothing else in the suite is "
            "worth trusting - this is the canary, and it's deliberately the very first thing to run.",
        reasoning="A zpod isn't just a database row reaching ACTIVE - it's a real VM that has to "
                  "boot, get an IP, and register itself in DNS before it's actually usable. Checking "
                  "the API status alone would miss a VM that's technically ACTIVE but unreachable.",
        expected="ACTIVE status, a network, an ACTIVE component - and the component's hostname "
                 "actually resolves via real DNS to the IP the API reports. After destroy, that "
                 "same hostname stops resolving (NXDOMAIN).",
        beats=[
            Beat("zpod create --wait", "single zcore component", state="ACTIVE", color="pass"),
            Beat("DNS query", "real resolver, not just the API's opinion", state="resolves", color="pass", tag="THE PROOF"),
            Beat("zpod destroy", "same hostname, right after", state="NXDOMAIN", color="pass", tag="CLEANUP VERIFIED"),
        ],
    ),
    "test_add_component_to_zpod_creates_dns_entry": Insight(
        why="This is deliberately zbox-13.7.1, never zcore-* - discovered live: adding a *second* "
            "zcore component to a zpod that already has its mandatory one conflicts with a real "
            "uniqueness constraint and the deploy fails outright.",
        reasoning="zcore is the one core component every zpod already gets exactly one of at "
                  "create time. zbox is a regular, addable-more-than-once component - the right "
                  "tool for proving 'add a component to an existing zpod' without fighting that "
                  "constraint.",
        expected="The new component reaches ACTIVE inside the existing zpod, and its own hostname "
                 "resolves via DNS - same proof-by-real-resolution as the smoke test above.",
        beats=[
            Beat("zcore-13.7 (mandatory)", "already present from deploy", state="ACTIVE", color="pass", tag="ALREADY THERE"),
            Beat("zbox-13.7.1 add", "a second, different component", state="ACTIVE", color="pass"),
            Beat("DNS query", "the new component's own hostname", state="resolves", color="pass"),
        ],
    ),
}


@pytest.mark.smoke
def test_create_minimal_zcore_zpod_smoke(
    zcli_as, namer, zcore_profile, endpoint, superadmin_client, e2e_config, wait_dns_resolves, wait_dns_nxdomain, poll_zpod_deleted
):
    """Deploy a single minimal zcore zpod, verify it, then delete it - the suite's fastest end-to-end sanity check."""
    runner = zcli_as("superadmin")
    zpod_name = namer("smoke")
    deploy_timeout = e2e_config.deploy_timeout_seconds + 60

    result = runner(
        "zpod", "create", zpod_name,
        "--endpoint", endpoint.name,
        "--profile", zcore_profile,
        "--wait", "--no-spinner",
        check=False,
        timeout=deploy_timeout,
    )
    assert result.returncode == 0, f"zpod create failed:\n{result.stdout}\n{result.stderr}"

    # What this validates: deployment, networking, and component bring-up
    # all worked - not just that the create API call was accepted.
    zpod = superadmin_client.zpods_get.sync(id=f"name={zpod_name}")
    assert zpod.status == "ACTIVE", f"expected ACTIVE, got {zpod.status}"
    assert zpod.networks, "expected at least one network"
    assert zpod.components, "expected at least one component"
    for component in zpod.components:
        assert component.status == status.ZPOD_COMPONENT_ACTIVE, (
            f"component {component.hostname} not ACTIVE: {component.status}"
        )

    primary = zpod.components[0]
    resolved_ip = wait_dns_resolves(primary.fqdn)
    assert resolved_ip, f"expected {primary.fqdn} to resolve via DNS"
    if primary.ip:
        assert resolved_ip == primary.ip, f"DNS resolved {primary.fqdn} to {resolved_ip}, API reports ip={primary.ip}"

    result = runner("zpod", "destroy", zpod_name)
    assert result.returncode == 0, f"zpod destroy failed:\n{result.stderr}"
    poll_zpod_deleted(superadmin_client, f"name={zpod_name}")

    wait_dns_nxdomain(primary.fqdn)


def test_create_zpod_invalid_profile_name_fails_cleanly(zcli_as, namer, endpoint):
    """Creating a zpod that references a nonexistent profile name fails cleanly, not a crash."""
    runner = zcli_as("superadmin")
    result = runner(
        "zpod", "create", namer("bad-profile"),
        "--endpoint", endpoint.name,
        "--profile", namer("nonexistent-profile"),
        check=False,
        timeout=30,
    )
    assert result.returncode != 0, "creating a zpod with an unknown profile name should fail"


@pytest.fixture(scope="module")
def active_zpod(zcli_as, namer, zcore_profile_items, endpoint, superadmin_client, e2e_config, poll_zpod_deleted, keep_resources):
    """A deployed, ACTIVE minimal zcore zpod - torn down at module teardown.

    Module-scoped: both tests below add/remove a component under different
    hostnames on the same zpod, so one deploy safely covers both instead of
    a real deploy+destroy cycle per test. Uses its own throwaway profile
    (see test_users_groups_permissions.py::active_zpod for why - a
    module-scoped fixture can't depend on the function-scoped `zcore_profile`).
    """

    runner = zcli_as("superadmin")
    zpod_name = namer("zpod")
    profile_name = namer("profile-zpod-component")
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

    yield zpod_name

    if not keep_resources:
        runner("zpod", "destroy", zpod_name, check=False)
        try:
            poll_zpod_deleted(superadmin_client, f"name={zpod_name}")
        except Exception:
            pass
        try:
            superadmin_client.profiles_delete.sync(id=f"name={profile_name}")
        except Exception:
            pass


def test_add_component_to_zpod_creates_dns_entry(
    zcli_as, active_zpod, superadmin_client, poll_zpod_component_status, wait_dns_resolves
):
    """Adding a component to an existing zpod deploys it and creates a resolvable DNS entry."""
    components = superadmin_client.components_get_all.sync() or []
    candidate = next((c for c in components if c.status == "ACTIVE" and c.component_uid == ADD_COMPONENT_UID), None)
    if not candidate:
        pytest.skip(f"{ADD_COMPONENT_UID} not ACTIVE - enable it first (test_libraries_components.py does this)")

    runner = zcli_as("superadmin")
    hostname = "extra-component"
    result = runner(
        "zpod", "component", "add", active_zpod,
        "--component-uid", candidate.component_uid,
        "--hostname", hostname,
        "--host-id", str(ADD_COMPONENT_HOST_ID),
    )
    assert result.returncode == 0, f"zpod component add failed:\n{result.stderr}"

    added = poll_zpod_component_status(superadmin_client, f"name={active_zpod}", f"hostname={hostname}")
    assert added.status == status.ZPOD_COMPONENT_ACTIVE, f"expected ACTIVE, got {added.status}"

    resolved_ip = wait_dns_resolves(added.fqdn)
    assert resolved_ip, f"expected {added.fqdn} to resolve via DNS after adding the component"


def test_remove_component_from_zpod_removes_dns_entry(
    zcli_as, active_zpod, superadmin_client, poll_zpod_component_status, wait_dns_resolves, wait_dns_nxdomain
):
    """Removing a component from a zpod also removes its DNS entry."""
    components = superadmin_client.components_get_all.sync() or []
    candidate = next((c for c in components if c.status == "ACTIVE" and c.component_uid == ADD_COMPONENT_UID), None)
    if not candidate:
        pytest.skip(f"{ADD_COMPONENT_UID} not ACTIVE - enable it first (test_libraries_components.py does this)")

    runner = zcli_as("superadmin")
    hostname = "removable-component"
    runner(
        "zpod", "component", "add", active_zpod,
        "--component-uid", candidate.component_uid,
        "--hostname", hostname,
        "--host-id", str(ADD_COMPONENT_HOST_ID + 1),
    )
    added = poll_zpod_component_status(superadmin_client, f"name={active_zpod}", f"hostname={hostname}")
    wait_dns_resolves(added.fqdn)

    result = runner("zpod", "component", "remove", active_zpod, "--hostname", hostname, "--yes")
    assert result.returncode == 0, f"zpod component remove failed:\n{result.stderr}"

    wait_dns_nxdomain(added.fqdn)
