"""zcli read commands and API refusals not covered elsewhere.

Cheap checks on things that already exist (the endpoint, the shared zcore
zPod): no deploy, nothing left behind. Each read is compared with what the
API or zcore itself says, each refusal checks that nothing was created.
"""

import httpx
import pytest

from e2e.insight import Insight

LONG_HOSTNAME = "e2e-" + "h" * 41  # zcore zPod FQDN: 45 + len(".e2e-zcore.zpod.io") > 56

INSIGHTS = {
    "test_fqdn_too_long_is_refused": Insight(
        why="Linux caps the system hostname at 64 characters, even for a full FQDN. DNS would "
            "accept a longer name, the guest would then fail to set its hostname during "
            "customization - a deploy that breaks halfway. zpodapi refuses it up front, with a "
            "safety margin (zpodfactory_fqdn_reserved_chars).",
        expected="400 naming the setting, for a component add and for a zPod create; nothing created.",
    ),
}


def _api(e2e_config) -> httpx.Client:
    return httpx.Client(base_url=e2e_config.api_base_url, headers={"access_token": e2e_config.superadmin_token}, timeout=60)


def _keys(obj, prefix="") -> list[str]:
    if isinstance(obj, dict):
        return [k for key, value in obj.items() for k in [f"{prefix}{key}", *_keys(value, f"{prefix}{key}.")]]
    if isinstance(obj, list):
        return [k for item in obj for k in _keys(item, prefix)]
    return []


def test_endpoint_info_hides_credentials(zcli_as, endpoint):
    """`endpoint info --json` shows the endpoint's compute and network config, and no password field anywhere."""
    info = zcli_as("superadmin").run_json("endpoint", "info", endpoint.name).json
    assert info["name"] == endpoint.name and info["id"] == endpoint.id, f"wrong endpoint: {info.get('name')}"
    assert {"compute", "network"} <= set(info["endpoints"]), f"endpoint config: {list(info['endpoints'])}"
    leaked = [k for k in _keys(info) if "pass" in k.lower() or "secret" in k.lower() or "token" in k.lower()]
    assert not leaked, f"endpoint info exposes credential fields: {leaked}"


def test_endpoint_permission_list_matches_api(zcli_as, endpoint, e2e_config):
    """`endpoint permission list --json` lists the same permissions, users and groups as the API."""
    rows = zcli_as("superadmin").run_json("endpoint", "permission", "list", endpoint.name).json
    with _api(e2e_config) as api:
        resp = api.get(f"/endpoints/name={endpoint.name}/permissions")
    assert resp.status_code == 200, resp.text

    def summary(items):
        return sorted(
            (r["permission"], tuple(sorted(u["username"] for u in r["users"])),
             tuple(sorted(g["name"] for g in r["permission_groups"])))
            for r in items
        )

    assert rows, "no permission rows for the endpoint the suite deploys on"
    assert summary(rows) == summary(resp.json()), f"zcli {summary(rows)} != API {summary(resp.json())}"


def test_zpod_dns_list_matches_components(zcli_as, zcore_zpod, superadmin_client):
    """`zpod dns list --json` has zcore's short name and FQDN, both on the IP the API gives zcore."""
    rows = zcli_as("superadmin").run_json("zpod", "dns", "list", zcore_zpod).json
    zcore = next(c for c in superadmin_client.zpods_components_get_all.sync(id=f"name={zcore_zpod}") or []
                 if c.hostname == "zcore")
    records = {(r["hostname"], r["ip"]) for r in rows}
    assert ("zcore", zcore.ip) in records, f"zcore not in dns list: {sorted(records)}"
    assert (zcore.fqdn, zcore.ip) in records, f"{zcore.fqdn} not in dns list: {sorted(records)}"


def test_zpod_permission_list_shows_owner(zcli_as, zcore_zpod, superadmin_client):
    """`zpod permission list --json` shows the creator (the superadmin identity) as OWNER."""
    me = superadmin_client.users_get_me.sync()
    rows = zcli_as("superadmin").run_json("zpod", "permission", "list", zcore_zpod).json
    owners = {u["username"] for r in rows if r["permission"] == "OWNER" for u in r["users"]}
    assert me.username in owners, f"{me.username} not OWNER of {zcore_zpod}: {rows}"


def test_group_update_and_endpoint_group_permission(zcli_as, namer, endpoint, _role_identities):
    """A group is renamed with `group update`, then given and denied the endpoint through `endpoint permission add/remove -g`."""
    runner = zcli_as("superadmin")
    name, new_name = namer("grp-upd"), namer("grp-renamed")
    member = _role_identities["test_user"]["username"]
    runner("group", "delete", name, check=False)
    runner("group", "delete", new_name, check=False)
    runner("group", "create", name)
    try:
        runner("group", "user", "add", name, "--username", member)
        runner("group", "update", name, "--newname", new_name)
        groups = {g["name"] for g in runner.run_json("group", "list").json}
        assert new_name in groups and name not in groups, f"rename not applied: {sorted(groups)}"

        runner("endpoint", "permission", "add", endpoint.name, "--group", new_name)
        rows = runner.run_json("endpoint", "permission", "list", endpoint.name).json
        granted = {g["name"] for r in rows for g in r["permission_groups"]}
        assert new_name in granted, f"group not on the endpoint: {rows}"

        runner("endpoint", "permission", "remove", endpoint.name, "--group", new_name)
        rows = runner.run_json("endpoint", "permission", "list", endpoint.name).json
        assert new_name not in {g["name"] for r in rows for g in r["permission_groups"]}, "group still on the endpoint"
    finally:
        runner("endpoint", "permission", "remove", endpoint.name, "--group", new_name, check=False)
        runner("group", "delete", new_name, check=False)
        runner("group", "delete", name, check=False)


def test_zpod_patch_description(zcore_zpod, superadmin_client, e2e_config, api_check):
    """PATCH /zpods/{id} (no zcli command, answers 201) changes the description, and it reads back; the original comes back after."""
    original = superadmin_client.zpods_get.sync(id=f"name={zcore_zpod}").description
    with _api(e2e_config) as api:
        try:
            resp = api.patch(f"/zpods/name={zcore_zpod}", json={"description": "e2e patched description"})
            # zpodapi answers 201 on every PATCH route (its convention, declared in the OpenAPI spec).
            api_check("PATCH", "/zpods/{id}", "change the description", expected=201, actual=resp.status_code,
                      note=resp.text[:200])
            assert resp.status_code == 201, resp.text
            assert superadmin_client.zpods_get.sync(id=f"name={zcore_zpod}").description == "e2e patched description"
        finally:
            api.patch(f"/zpods/name={zcore_zpod}", json={"description": original or ""})
    assert (superadmin_client.zpods_get.sync(id=f"name={zcore_zpod}").description or "") == (original or "")


def test_fqdn_too_long_is_refused(zcli_as, zcore_zpod, zcore_profile, endpoint, namer, superadmin_client, e2e_config, api_check):
    """A component or zPod whose FQDN goes past the limit is refused with 400 naming the setting; nothing is created."""
    with _api(e2e_config) as api:
        resp = api.post(f"/zpods/name={zcore_zpod}/components",
                        json={"component_uid": e2e_config.zbox_component_uid, "hostname": LONG_HOSTNAME, "host_id": 60})
    api_check("POST", "/zpods/{id}/components", f"hostname of {len(LONG_HOSTNAME)} chars", expected=400,
              actual=resp.status_code, note=resp.text[:200])
    assert resp.status_code == 400 and "zpodfactory_fqdn_reserved_chars" in resp.text, f"{resp.status_code}: {resp.text}"
    hostnames = {c.hostname for c in superadmin_client.zpods_components_get_all.sync(id=f"name={zcore_zpod}") or []}
    assert LONG_HOSTNAME not in hostnames, "refused component was added"

    long_name = namer("fqdn-" + "z" * 40)
    result = zcli_as("superadmin")("zpod", "create", long_name, "--endpoint", endpoint.name,
                                   "--profile", zcore_profile, check=False)
    assert result.returncode != 0, f"zpod create with a {len(long_name)}-char name was accepted:\n{result.stdout}"
    assert "too long" in (result.stdout + result.stderr).lower(), f"no FQDN reason:\n{result.stdout}\n{result.stderr}"
    names = {z.name for z in superadmin_client.zpods_get_all.sync() or []}
    if long_name in names:
        zcli_as("superadmin")("zpod", "destroy", long_name, check=False)
        pytest.fail(f"refused zPod {long_name} was created")
