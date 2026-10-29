"""nested on POST /zpods/{id}/components and on profile items."""

import json

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from zpodcommon import models as M
from zpodcommon.lib.component_network import ComponentNetworkError
from zpodcommon.lib.dbutils import DBUtils


class FakeZpodEngineClient:
    """Stand-in for the Prefect client so no flow run is scheduled."""

    calls: list[dict] = []

    def create_flow_run_by_name(self, flow_name, deployment_name=None, **kw):
        self.calls.append({"flow_name": flow_name, **kw})


@pytest.fixture(autouse=True)
def settings_and_engine(monkeypatch):
    values = {"zpodfactory_default_domain": "example.com"}
    monkeypatch.setattr(
        DBUtils,
        "get_setting_value",
        classmethod(lambda cls, name: values.get(name)),
    )
    FakeZpodEngineClient.calls = []
    monkeypatch.setattr(
        "zpodapi.zpods.zpod_component__services.ZpodEngineClient",
        FakeZpodEngineClient,
    )
    monkeypatch.setattr(
        "zpodapi.zpods.zpod_component__services.get_all_active_addresses",
        lambda zpod: set(),
    )


MAPPING = {"NetworkMapping": [{"Name": "nic", "Network": "{{zpod_portgroup}}"}]}
ESXI_SPEC = {
    **MAPPING,
    "PropertyMapping": [{"Key": "guestinfo.vlan", "Value": "{{zpod_vlan}}"}],
}
COMPONENTS = {
    # name: (component_isnested, govc spec)
    "zcore": (False, MAPPING),
    "esxi": (False, ESXI_SPEC),
    "vrops": (True, MAPPING),
    "ubuntu": (False, MAPPING),
    "legacy": (True, {}),
}


@pytest.fixture
def zpod(session: Session, tmp_path):
    """An ACTIVE zPod with a user network, and library components on disk."""
    endpoint = M.Endpoint(name="ep", endpoints={}, status="ACTIVE")
    components = []
    for name, (isnested, spec) in COMPONENTS.items():
        jsonfile = tmp_path / f"{name}.json"
        jsonfile.write_text(
            json.dumps(
                {
                    "component_name": name,
                    "component_isnested": isnested,
                    "component_deploy_govc_spec": spec,
                }
            )
        )
        components.append(
            M.Component(
                component_uid=f"{name}-1.0",
                component_name=name,
                component_version="1.0",
                component_description=name,
                filename=f"{name}.ova",
                jsonfile=str(jsonfile),
                status="ACTIVE",
                download_status="COMPLETED",
                file_checksum="abc",
            )
        )
    session.add_all([endpoint, *components])
    session.commit()
    zpod = M.Zpod(
        name="demo",
        domain="demo.example.com",
        endpoint_id=endpoint.id,
        profile="base",
        status="ACTIVE",
        networks=[
            M.ZpodNetwork(cidr="10.96.1.0/26", name="mgmt", gateway="10.96.1.1/26"),
            M.ZpodNetwork(
                cidr="10.96.1.64/26", name="vlan64", vlan_id=64, gateway="10.96.1.65/26"
            ),
            M.ZpodNetwork(
                cidr="10.42.111.0/24",
                name="LOCALNET111",
                vlan_id=111,
                gateway="10.42.111.1/24",
                kind="user",
            ),
        ],
    )
    session.add(zpod)
    session.commit()
    return zpod


def add(client, zpod, **body):
    return client.post(f"/zpods/{zpod.id}/components", json=body)


@pytest.mark.parametrize("nested", [True, False, None])
def test_component_add_forwards_nested(superadmin_client, zpod, nested):
    body = {"component_uid": "vrops-1.0"}
    if nested is not None:
        body["nested"] = nested
    response = superadmin_client.post(f"/zpods/{zpod.id}/components", json=body)
    assert response.status_code == 201, response.text
    assert FakeZpodEngineClient.calls[0]["nested"] is nested


def test_component_add_refuses_nested_on_fixed_placement(superadmin_client, zpod):
    response = superadmin_client.post(
        f"/zpods/{zpod.id}/components",
        json={
            "component_uid": "esxi-1.0",
            "host_id": 11,
            "hostname": "esxi11",
            "nested": True,
        },
    )
    assert response.status_code == 422, response.text
    assert response.json()["detail"] == (
        "nested can't be set to true on esxi: its placement is fixed (on the endpoint)"
    )
    assert FakeZpodEngineClient.calls == []


def test_component_add_accepts_a_fixed_components_own_default(superadmin_client, zpod):
    response = add(
        superadmin_client,
        zpod,
        component_uid="esxi-1.0",
        host_id=11,
        hostname="esxi11",
        nested=False,
    )
    assert response.status_code == 201, response.text


def test_profile_nested(superadmin_client: TestClient, zpod):
    response = superadmin_client.post(
        "/profiles",
        json={
            "name": "nestedvrops",
            "profile": [
                {"component_uid": "zcore-1.0"},
                {"component_uid": "vrops-1.0", "nested": False},
            ],
        },
    )
    assert response.status_code == 201, response.text
    assert response.json()["profile"][1]["nested"] is False

    response = superadmin_client.post(
        "/profiles",
        json={
            "name": "nestedzcore",
            "profile": [{"component_uid": "zcore-1.0", "nested": True}],
        },
    )
    assert response.status_code == 400, response.text
    assert (
        "zcore-1.0: nested can't be set to true on zcore" in response.json()["detail"]
    )


# --- network (nested components only) ----------------------------------------


def test_network_explicit_ip_with_hostname_only(superadmin_client, zpod):
    network = {"ip": "10.42.111.20/24", "portgroup": "VM Network"}
    response = add(
        superadmin_client,
        zpod,
        component_uid="ubuntu-1.0",
        hostname="web01",
        nested=True,
        network=network,
    )
    assert response.status_code == 201, response.text
    call = FakeZpodEngineClient.calls[0]
    assert call["network"] == network
    assert (call["hostname"], call["host_id"]) == ("web01", None)


@pytest.fixture
def portgroups(monkeypatch):
    """The zPod vCenter's portgroups, by name: their VLAN, as vCenter reports it."""
    vlans = {"VM Network": 0, "PG111": 111, "PG64": 64, "PG300": 300, "TRUNK": "trunk"}
    looked_up = []

    def nested_portgroup(zpod, portgroup):
        looked_up.append(portgroup)
        if portgroup not in vlans:
            raise ComponentNetworkError(f"portgroup {portgroup!r} not found")
        return {"vlan": vlans[portgroup]}

    monkeypatch.setattr(
        "zpodcommon.lib.component_network.nested_portgroup", nested_portgroup
    )
    return looked_up


def test_network_portgroup_vlan_gives_the_address(superadmin_client, zpod, portgroups):
    response = add(
        superadmin_client,
        zpod,
        component_uid="vrops-1.0",
        hostname="vrops",
        host_id=20,
        network={"portgroup": "PG111"},
    )
    assert response.status_code == 201, response.text
    assert portgroups == ["PG111"]
    # The flow gets the request; the prep task resolves 10.42.111.20 the same way.
    assert FakeZpodEngineClient.calls[0]["network"] == {"portgroup": "PG111"}


@pytest.mark.parametrize(
    "portgroup, host_id, error",
    [
        ("NOPE", 20, "portgroup 'NOPE' not found"),
        ("PG300", 20, "is on VLAN 300, and zPod demo has no network on VLAN 300"),
        ("TRUNK", 20, "is a trunk: give vlan_id"),
        ("PG64", 20, "portgroup PG64 (VLAN 64) takes host_id 66 to 126"),
    ],
)
def test_network_portgroup_refused(
    superadmin_client, zpod, portgroups, portgroup, host_id, error
):
    response = add(
        superadmin_client,
        zpod,
        component_uid="vrops-1.0",
        hostname="vrops",
        host_id=host_id,
        network={"portgroup": portgroup},
    )
    assert response.status_code == 422, response.text
    assert error in response.json()["detail"]
    assert FakeZpodEngineClient.calls == []


def test_network_explicit_ip_skips_the_lookup(superadmin_client, zpod, portgroups):
    response = add(
        superadmin_client,
        zpod,
        component_uid="vrops-1.0",
        hostname="vrops",
        network={"ip": "10.42.111.21/24", "portgroup": "PG111"},
    )
    assert response.status_code == 201, response.text
    assert portgroups == []


@pytest.mark.parametrize(
    "body, error",
    [
        (
            {"component_uid": "ubuntu-1.0", "network": {"ip": "10.42.111.20/24"}},
            "network is only for nested components: ubuntu deploys on the endpoint",
        ),
        (
            {
                "component_uid": "vrops-1.0",
                "nested": False,
                "network": {"dns": "1.1.1.1"},
            },
            "network is only for nested components",
        ),
        (
            {"component_uid": "vrops-1.0", "vnics": 2},
            "vnics can't be set on a nested component",
        ),
        (
            {"component_uid": "legacy-1.0", "network": {"portgroup": "VM Network"}},
            "its library JSON has no NetworkMapping",
        ),
        (
            {
                "component_uid": "esxi-1.0",
                "host_id": 11,
                "hostname": "esxi11",
                "network": {"dns": "1.1.1.1"},
            },
            "network can't be set on esxi: component is protected",
        ),
        (
            {
                "component_uid": "vrops-1.0",
                "hostname": "vrops",
                "network": {"ip": "192.168.10.20/24"},
            },
            "gateway is required",
        ),
        (
            {
                "component_uid": "vrops-1.0",
                "hostname": "vrops",
                "host_id": 30,
                "network": {"ip": "10.42.111.20/24"},
            },
            "host_id can't be set",
        ),
    ],
)
def test_network_refused(superadmin_client, zpod, body, error):
    response = add(superadmin_client, zpod, **body)
    assert response.status_code == 422, response.text
    assert error in response.json()["detail"]
    assert FakeZpodEngineClient.calls == []


def test_profile_network(superadmin_client: TestClient, zpod):
    def create(name, item):
        return superadmin_client.post(
            "/profiles",
            json={"name": name, "profile": [{"component_uid": "zcore-1.0"}, item]},
        )

    item = {
        "component_uid": "ubuntu-1.0",
        "hostname": "web01",
        "host_id": 20,
        "nested": True,
        "network": {"portgroup": "VM Network"},
    }
    response = create("netok", item)
    assert response.status_code == 201, response.text
    assert response.json()["profile"][1]["network"]["portgroup"] == "VM Network"

    response = create("netl1", {**item, "nested": None})
    assert response.status_code == 400, response.text
    assert "ubuntu-1.0: network is only for nested" in response.json()["detail"]

    response = create(
        "netstatic", {**item, "host_id": None, "network": {"ip": "10.42.111.20"}}
    )
    assert response.status_code == 400, response.text
    assert "needs its prefix" in response.json()["detail"]


def test_unknown_component_is_404(superadmin_client, zpod):
    response = add(superadmin_client, zpod, component_uid="nope-1.0")
    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "No ACTIVE component nope-1.0"


def test_profile_force_false_still_validates(superadmin_client: TestClient, zpod):
    # zcli/zpodsdk always send ?force=false: the query string must not skip checks.
    response = superadmin_client.post(
        "/profiles?force=false",
        json={
            "name": "forcefalse",
            "profile": [
                {"component_uid": "zcore-1.0"},
                {"component_uid": "ubuntu-1.0", "network": {"dns": "1.1.1.1"}},
            ],
        },
    )
    assert response.status_code == 400, response.text


# --- vlan_id ----------------------------------------------------------------------


def test_vlan_id_on_esxi(superadmin_client, zpod):
    response = add(
        superadmin_client,
        zpod,
        component_uid="esxi-1.0",
        hostname="esxi71",
        host_id=71,
        vlan_id=64,
    )
    assert response.status_code == 201, response.text
    assert FakeZpodEngineClient.calls[0]["vlan_id"] == 64


@pytest.mark.parametrize(
    "body, error",
    [
        (
            {"component_uid": "esxi-1.0", "host_id": 11, "vlan_id": 64},
            "10.96.1.11 is not a host address of 10.96.1.64/26",
        ),
        (
            {"component_uid": "esxi-1.0", "host_id": 71, "vlan_id": 65},
            "no network on VLAN 65",
        ),
        (
            {"component_uid": "ubuntu-1.0", "host_id": 71, "vlan_id": 64},
            "doesn't use {{zpod_vlan}}",
        ),
        ({"component_uid": "esxi-1.0", "host_id": 71, "vlan_id": 5000}, "not a VLAN"),
    ],
)
def test_vlan_id_refused(superadmin_client, zpod, body, error):
    response = add(superadmin_client, zpod, hostname="h71", **body)
    assert response.status_code == 422, response.text
    assert error in response.json()["detail"]


def test_profile_vlan_id(superadmin_client: TestClient, zpod):
    item = {
        "component_uid": "esxi-1.0",
        "host_id": 71,
        "hostname": "esxi71",
        "vlan_id": 64,
    }
    response = superadmin_client.post(
        "/profiles",
        json={"name": "vlanok", "profile": [{"component_uid": "zcore-1.0"}, item]},
    )
    assert response.status_code == 201, response.text
    assert response.json()["profile"][1]["vlan_id"] == 64
    response = superadmin_client.post(
        "/profiles",
        json={
            "name": "vlanko",
            "profile": [{"component_uid": "zcore-1.0"}, {**item, "host_id": None}],
        },
    )
    assert response.status_code == 400, response.text
    assert "vlan_id needs host_id" in response.json()["detail"]
