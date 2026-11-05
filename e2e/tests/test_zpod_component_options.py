"""Component add options: placement (nested), network and VLAN overrides, login users, extraConfig images.

Cheap part (always runs, on the shared zcore zPod, nothing deployed): every
combination the API must refuse, each with its status code and message.

Heavier part (opt-in, see .env.sample):
- E2E_EXTRACONFIG_COMPONENT_UID: deploy an extraConfig (guestinfo.*) image
  such as photon-5.0 or ubuntu-24.04, then log in with the factory key as the
  login user zcli shows for that image, and check the guest got its
  hostname from guestinfo before first boot.
- Nested placement: deploy a zPod with a vCenter (the base9 fixture, or
  E2E_NESTED_PROFILE), add a zbox nested in it on `VM Network`, check it's
  ACTIVE and reachable through zcore.
"""

from pathlib import Path

import httpx
import pytest

from e2e import status
from e2e.insight import Beat, Insight
from e2e.profiles import load_profile_items, profile_body

EXTRACONFIG_HOSTNAME = "e2e-xcfg"
EXTRACONFIG_HOST_ID = 53
NESTED_HOSTNAME = "e2e-nested"
NESTED_HOST_ID = 54
# zcore, two ESXi hosts and a vCenter: the smallest zPod a zbox can nest in.
NESTED_PROFILE_FILE = Path(__file__).parent / "fixtures" / "profiles" / "base9.json"

INSIGHTS = {
    "test_component_add_option_refusals": Insight(
        why="The placement and network options combine in ways that can't work (a VLAN on a guest "
            "that can't tag, a portgroup on an endpoint VM). Refusing them up front, with the "
            "reason, beats a deploy that fails twenty minutes later.",
        expected="422 with a message naming the option and the component, for each combination; "
                 "nothing added to the zPod.",
    ),
    "test_extraconfig_component_boots_with_guestinfo_and_key": Insight(
        why="extraConfig images (Photon, Ubuntu, Talos...) read guestinfo.* before first power-on "
            "instead of OVF properties. A wrong key name means a VM with a default hostname and no "
            "SSH key - only visible from inside the guest.",
        beats=[
            Beat("zcli zpod component add", "extraConfig image", state="ACTIVE", color="pass"),
            Beat("zcli zpod component list", "login user for that image", state="user shown", color="pass"),
            Beat("ssh <user>@vm", "factory key", state="hostname = requested", color="pass", tag="THE PROOF"),
        ],
    ),
}


def _api(e2e_config) -> httpx.Client:
    return httpx.Client(base_url=e2e_config.api_base_url, headers={"access_token": e2e_config.superadmin_token}, timeout=60)


def _require_active(superadmin_client, uid: str) -> None:
    components = superadmin_client.components_get_all.sync() or []
    if not any(c.component_uid == uid and c.status == "ACTIVE" for c in components):
        pytest.skip(f"{uid} not ACTIVE in the library - enable it first")


def test_component_list_shows_login_users(zcli_as, zcore_zpod):
    """`zpod component list --json` gives each component its own login users (zcore: root)."""
    rows = zcli_as("superadmin").run_json("zpod", "component", "list", zcore_zpod).json
    zcore = next(r for r in rows if r.get("hostname") == "zcore")
    users = [u.get("username") for u in (zcore.get("usernames") or []) if u.get("type") == "ssh"]
    assert "root" in users, f"zcore login users: {zcore.get('usernames')}"


def test_component_add_option_refusals(zcore_zpod, superadmin_client, e2e_config, api_check):
    """Impossible option combinations are refused with 422 and a reason, and nothing is added."""
    zbox = e2e_config.zbox_component_uid
    _require_active(superadmin_client, zbox)
    cases = [
        ("VLAN on a guest that can't tag (no {{zpod_vlan}})",
         {"component_uid": zbox, "hostname": "e2e-r1", "host_id": 61, "vlan_id": e2e_config.user_vlan}, "zpod_vlan"),
        ("network override on an endpoint component",
         {"component_uid": zbox, "hostname": "e2e-r2", "host_id": 62, "network": {"portgroup": "VM Network"}}, "only for nested"),
        ("vnics on a nested component",
         {"component_uid": zbox, "hostname": "e2e-r3", "host_id": 63, "nested": True, "vnics": 2}, "vnics"),
        ("VLAN id out of range",
         {"component_uid": zbox, "hostname": "e2e-r4", "host_id": 64, "vlan_id": 5000}, "1-4094"),
        ("network.ip together with vlan_id",
         {"component_uid": zbox, "hostname": "e2e-r5", "host_id": 65, "nested": True, "vlan_id": 64,
          "network": {"ip": "10.42.111.65/24"}}, "vlan_id gives the address"),
    ]
    failures = []
    with _api(e2e_config) as api:
        for label, body, needle in cases:
            resp = api.post(f"/zpods/name={zcore_zpod}/components", json=body)
            api_check("POST", "/zpods/{id}/components", label, expected=422, actual=resp.status_code, note=resp.text[:200])
            if resp.status_code != 422 or needle not in resp.text:
                failures.append(f"{label}: expected 422 mentioning '{needle}', got {resp.status_code} {resp.text[:200]}")
    hostnames = {c.hostname for c in superadmin_client.zpods_components_get_all.sync(id=f"name={zcore_zpod}") or []}
    assert not failures, "\n".join(failures)
    assert not hostnames & {"e2e-r1", "e2e-r2", "e2e-r3", "e2e-r4", "e2e-r5"}, f"a refused add left a component: {hostnames}"


def test_protected_component_placement_is_fixed(zcore_zpod, e2e_config, api_check, namer):
    """zcore's placement can't be changed: 422 on a component add, 400 on a profile."""
    uid = e2e_config.zcore_component_uid
    with _api(e2e_config) as api:
        resp = api.post(f"/zpods/name={zcore_zpod}/components",
                        json={"component_uid": uid, "hostname": "e2e-zc2", "host_id": 66, "nested": True})
        api_check("POST", "/zpods/{id}/components", "zcore nested: true", expected=422, actual=resp.status_code,
                  note=resp.text[:200])
        assert resp.status_code == 422 and "placement is fixed" in resp.text, f"{resp.status_code}: {resp.text}"

        resp = api.post("/profiles", json={"name": namer("profile-badplacement"),
                                           "profile": [{"component_uid": uid, "nested": True}]})
        api_check("POST", "/profiles", "profile with zcore nested: true", expected=400, actual=resp.status_code,
                  note=resp.text[:200])
        assert resp.status_code == 400, f"{resp.status_code}: {resp.text}"


@pytest.mark.slow
def test_extraconfig_component_boots_with_guestinfo_and_key(
    zcli_as, zcore_zpod, superadmin_client, zpod_ssh, poll_zpod_component_status, e2e_config, keep_resources
):
    """An extraConfig image deploys, gets its hostname from guestinfo, and accepts the factory key as its login user."""
    uid = e2e_config.extraconfig_component_uid
    if not uid:
        pytest.skip("E2E_EXTRACONFIG_COMPONENT_UID not set")
    _require_active(superadmin_client, uid)
    runner = zcli_as("superadmin")
    runner("zpod", "component", "add", zcore_zpod, "--component-uid", uid,
           "--hostname", EXTRACONFIG_HOSTNAME, "--host-id", str(EXTRACONFIG_HOST_ID), timeout=300)
    try:
        added = poll_zpod_component_status(superadmin_client, f"name={zcore_zpod}", f"hostname={EXTRACONFIG_HOSTNAME}")
        assert added.status == status.ZPOD_COMPONENT_ACTIVE, f"{uid} add: {added.status}"

        rows = runner.run_json("zpod", "component", "list", zcore_zpod).json
        row = next(r for r in rows if r.get("hostname") == EXTRACONFIG_HOSTNAME)
        ssh_users = [u["username"] for u in (row.get("usernames") or []) if u.get("type") == "ssh"]
        assert ssh_users, f"no SSH login user shown for {uid}: {row.get('usernames')}"

        vm = zpod_ssh(zcore_zpod, hostname=EXTRACONFIG_HOSTNAME)
        vm.user = ssh_users[0]
        vm.wait_ready(timeout_seconds=600)
        assert vm("hostname -s").stdout.strip() == EXTRACONFIG_HOSTNAME, "hostname not taken from guestinfo"
        assert added.ip in vm("ip -4 -o addr show").stdout, f"{added.ip} not configured in the guest"
    finally:
        if not keep_resources:
            runner("zpod", "component", "remove", zcore_zpod, EXTRACONFIG_HOSTNAME, "-y", check=False, timeout=300)


@pytest.fixture(scope="module")
def nested_zpod(zcli_as, namer, endpoint, superadmin_client, e2e_config, poll_zpod_deleted, keep_resources):
    """A zPod with a vCenter: E2E_NESTED_PROFILE if set, else a throwaway profile from base9.json."""
    profile_name = e2e_config.nested_profile
    if not profile_name:
        profile_name = namer("profile-nested")
        superadmin_client.profiles_create.sync(body=profile_body(profile_name, load_profile_items(NESTED_PROFILE_FILE)))
    runner = zcli_as("superadmin")
    name = namer("nested")
    result = runner("zpod", "create", name, "--endpoint", endpoint.name, "--profile", profile_name,
                    "--wait", "--no-spinner", check=False, timeout=e2e_config.deploy_timeout_seconds + 60)
    if result.returncode != 0:
        pytest.fail(f"nested-profile zPod deploy failed:\n{result.stdout}")
    yield name
    if not keep_resources:
        runner("zpod", "destroy", name, check=False)
        try:
            poll_zpod_deleted(superadmin_client, f"name={name}")
        except Exception:
            pass
        if not e2e_config.nested_profile:
            try:
                superadmin_client.profiles_delete.sync(id=f"name={profile_name}")
            except Exception:
                pass  # still used by a zPod that didn't go away; the session sweep retries


@pytest.mark.slow
def test_nested_component_on_portgroup(zcli_as, nested_zpod, superadmin_client, zpod_ssh, poll_zpod_component_status, e2e_config):
    """A zbox added with --nested true on `VM Network` deploys inside the zPod's vCenter and answers SSH through zcore."""
    _require_active(superadmin_client, e2e_config.zbox_component_uid)
    runner = zcli_as("superadmin")
    runner("zpod", "component", "add", nested_zpod, "--component-uid", e2e_config.zbox_component_uid,
           "--hostname", NESTED_HOSTNAME, "--host-id", str(NESTED_HOST_ID),
           "--nested", "true", "--portgroup", "VM Network", timeout=300)
    added = poll_zpod_component_status(superadmin_client, f"name={nested_zpod}", f"hostname={NESTED_HOSTNAME}")
    assert added.status == status.ZPOD_COMPONENT_ACTIVE, f"nested zbox add: {added.status}"

    vm = zpod_ssh(nested_zpod).jump(added.ip)
    vm.wait_ready(timeout_seconds=600)
    assert vm("hostname -s").stdout.strip() == NESTED_HOSTNAME, "nested zbox hostname"
    runner("zpod", "component", "remove", nested_zpod, NESTED_HOSTNAME, "-y", check=False, timeout=300)
