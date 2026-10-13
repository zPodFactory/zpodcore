"""User networks on a zPod: /zpods/{id}/networks.

zboxapi and the Prefect engine are replaced by fakes; the four deploy-time
rows come from ZpodNetwork.deploy_row, like zpod_deploy_1_prep writes them.
"""

from ipaddress import IPv4Network

import pytest
from fastapi import HTTPException
from sqlmodel import Session

from zpodcommon import models as M
from zpodcommon.enums import ZpodNetworkRouting
from zpodcommon.lib.dbutils import DBUtils

ZPOD_SUBNET = IPv4Network("10.60.60.0/24")


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload, self.status_code = payload, status_code

    def safejson(self):
        if self.status_code >= 400:
            raise HTTPException(status_code=self.status_code, detail=self.payload)
        return self.payload


class FakeZbox:
    """What zboxapi on zcore answers; `calls` records every request."""

    vlans: list[dict] = []
    dns: list[dict] = []
    calls: list[tuple] = []
    unreachable = False
    responses: dict[tuple, FakeResponse] = {}

    @classmethod
    def reset(cls):
        cls.vlans = [
            {
                "vlan": 10,
                "gateway": "172.16.10.1/24",
                "status": "up",
                "owner": "system-default",
                "masquerade": False,
            },
            {
                "vlan": 20,
                "gateway": "172.16.20.1/24",
                "status": "up",
                "owner": "system-default",
                "masquerade": False,
            },
            {
                "vlan": 30,
                "gateway": "172.16.30.1/24",
                "status": "up",
                "owner": "system-default",
                "masquerade": False,
            },
            {
                "vlan": 64,
                "gateway": "10.60.60.65/26",
                "status": "up",
                "owner": "system-zpod",
                "masquerade": False,
            },
            {
                "vlan": 128,
                "gateway": "10.60.60.129/26",
                "status": "up",
                "owner": "system-zpod",
                "masquerade": False,
            },
            {
                "vlan": 192,
                "gateway": "10.60.60.193/26",
                "status": "up",
                "owner": "system-zpod",
                "masquerade": False,
            },
        ]
        cls.dns = []
        cls.calls = []
        cls.unreachable = False
        cls.responses = {}

    @classmethod
    def by_zpod(cls, zpod, **kwargs):
        if cls.unreachable:
            from zpodcommon.lib.zboxapi import RequestError

            raise RequestError("connection timed out")
        return cls()

    def _call(self, method, url, json=None):
        FakeZbox.calls.append((method, url, json))
        if (method, url) in FakeZbox.responses:
            return FakeZbox.responses[(method, url)]
        if method == "GET" and url == "/vlan":
            return FakeResponse(list(FakeZbox.vlans))
        if method == "GET" and url == "/dns":
            return FakeResponse(list(FakeZbox.dns))
        if method == "POST" and url == "/vlan":
            if json["vlan"] in (10, 20, 30):
                return FakeResponse(
                    f"VLAN {json['vlan']} is a system default VLAN and cannot be modified",
                    403,
                )
            if json["vlan"] in (64, 128, 192):
                return FakeResponse(
                    f"VLAN {json['vlan']} is a system zPod VLAN and cannot be modified",
                    403,
                )
            vlan = {**json, "status": "up", "owner": "user-defined"}
            if FakeZbox.vlans and "masquerade" not in FakeZbox.vlans[0]:
                vlan.pop("masquerade", None)  # zboxapi 0.1.1 ignores the field
            FakeZbox.vlans.append(vlan)
            return FakeResponse(vlan, 201)
        if method == "DELETE" and url.startswith("/vlan/"):
            vlan_id = int(url.split("/")[2])
            FakeZbox.vlans = [v for v in FakeZbox.vlans if v["vlan"] != vlan_id]
            return FakeResponse({"message": "deleted"})
        if method == "PUT" and url.endswith("/masquerade"):
            vlan_id = int(url.split("/")[2])
            for v in FakeZbox.vlans:
                if v["vlan"] == vlan_id:
                    v["masquerade"] = json["enabled"]
                    return FakeResponse(v)
            return FakeResponse("VLAN not found", 404)
        if method == "PUT" and (url.endswith("/enable") or url.endswith("/disable")):
            vlan_id = int(url.split("/")[2])
            for v in FakeZbox.vlans:
                if v["vlan"] == vlan_id:
                    v["status"] = "up" if url.endswith("/enable") else "down"
                    return FakeResponse({"message": "ok"})
            return FakeResponse("VLAN not found", 404)
        raise AssertionError(f"unexpected zboxapi call {method} {url}")

    def get(self, url):
        return self._call("GET", url)

    def post(self, url, json=None):
        return self._call("POST", url, json)

    def put(self, url, json=None):
        return self._call("PUT", url, json)

    def delete(self, url):
        return self._call("DELETE", url)


class FakeZpodEngineClient:
    calls: list[dict] = []
    runs: dict[str, dict] = {}  # id -> what get_flow_run answers

    def create_flow_run_by_name(self, flow_name, deployment_name=None, **kw):
        self.calls.append({"flow_name": flow_name, **kw})
        run_id = f"run-{len(self.calls)}"
        self.runs[run_id] = {
            "id": run_id,
            "name": kw.get("run_name"),
            "state": "SCHEDULED",
            "message": None,
            "parameters": {k: v for k, v in kw.items() if k != "run_name"},
        }
        return {"id": run_id}

    def get_flow_run(self, flow_run_id):
        return self.runs.get(flow_run_id)


@pytest.fixture(autouse=True)
def fakes(monkeypatch):
    values = {"zpodfactory_default_domain": "example.com"}
    monkeypatch.setattr(
        DBUtils, "get_setting_value", classmethod(lambda cls, name: values.get(name))
    )
    FakeZbox.reset()
    FakeZpodEngineClient.calls = []
    FakeZpodEngineClient.runs = {}
    monkeypatch.setattr("zpodapi.zpods.zpod_network__services.ZboxApiClient", FakeZbox)
    monkeypatch.setattr(
        "zpodapi.zpods.zpod_network__services.ZpodEngineClient", FakeZpodEngineClient
    )
    return values


@pytest.fixture
def lab(session: Session):
    """An ACTIVE zPod 'lab' owned by normaluser, with its four deploy rows."""
    endpoint = M.Endpoint(
        name="ep",
        endpoints={
            "network": {
                "t0": "edge-t0",
                "networks": "10.60.0.0/16",
                "hostname": "nsx",
                "username": "u",
                "password": "p",
            }
        },
        status="ACTIVE",
    )
    zcore = M.Component(
        component_uid="zcore-13.5",
        component_name="zcore",
        component_version="13.5",
        component_description="zcore",
        filename="zcore.ova",
        jsonfile="/library/zcore.json",
        status="ACTIVE",
        download_status="COMPLETED",
        file_checksum="abc",
    )
    session.add_all([endpoint, zcore])
    session.flush()
    normal_user = session.get(M.User, 2)
    zpod = M.Zpod(
        name="lab",
        domain="lab.example.com",
        endpoint_id=endpoint.id,
        profile="sddc",
        status="ACTIVE",
        password="pw",
        permissions=[M.ZpodPermission(permission="OWNER", users=[normal_user])],
    )
    for subnet in ZPOD_SUBNET.subnets(new_prefix=26):
        zpod.networks.append(M.ZpodNetwork.deploy_row(subnet))
    zpod.components.append(
        M.ZpodComponent(
            component_id=zcore.id,
            status="ACTIVE",
            ip="10.60.60.2",
            hostname="zcore",
            fqdn="zcore.lab.example.com",
        )
    )
    session.add(zpod)
    session.commit()
    return zpod


def add(client, **body):
    payload = {"name": "wld01", "vlan": 1000, "gateway": "10.10.100.1/24", **body}
    return client.post("/zpods/name=lab/networks", json=payload)


# ── list ──────────────────────────────────────────────────────────────────────


def test_list_backfilled_rows_with_live_status(normaluser_client, lab):
    r = normaluser_client.get("/zpods/name=lab/networks")
    assert r.status_code == 200, r.text
    rows = r.json()
    assert [n["name"] for n in rows] == [
        "mgmt",
        "vlan10",
        "vlan20",
        "vlan30",
        "vlan64",
        "vlan128",
        "vlan192",
    ]
    assert [n["kind"] for n in rows] == [
        "zpod",
        "zcore",
        "zcore",
        "zcore",
        "zpod",
        "zpod",
        "zpod",
    ]
    assert {n["status"] for n in rows} == {"ACTIVE"}
    assert rows[4]["vlan_id"] == 64 and rows[4]["gateway"] == "10.60.60.65/26"
    # zcore's own VLANs come live from zboxapi: no id, local, cidr from the gateway
    z = rows[1]
    assert z["id"] is None and z["vlan_id"] == 10 and z["routing"] == "LOCAL"
    assert z["cidr"] == "172.16.10.0/24" and z["gateway"] == "172.16.10.1/24"


def test_zcore_rows_follow_the_box_and_refuse_changes(normaluser_client, lab):
    FakeZbox.vlans[1]["status"] = "down"  # vlan 20 down on the box
    rows = normaluser_client.get("/zpods/name=lab/networks").json()
    assert rows[2]["name"] == "vlan20" and rows[2]["status"] == "DISABLED"
    FakeZbox.unreachable = True
    rows = normaluser_client.get("/zpods/name=lab/networks").json()
    assert [n["name"] for n in rows] == ["mgmt", "vlan64", "vlan128", "vlan192"]
    FakeZbox.unreachable = False
    r = normaluser_client.delete("/zpods/name=lab/networks/vlan20")
    assert r.status_code == 403 and "kind zcore" in r.json()["detail"]
    r = normaluser_client.put("/zpods/name=lab/networks/vlan20/disable")
    assert r.status_code == 403 and "kind zcore" in r.json()["detail"]


def test_list_status_disabled_missing_unknown(normaluser_client, lab):
    FakeZbox.vlans[3]["status"] = "down"  # vlan 64
    del FakeZbox.vlans[5]  # vlan 192 gone from the box
    rows = normaluser_client.get("/zpods/name=lab/networks").json()
    assert [n["status"] for n in rows if n["kind"] == "zpod"] == [
        "ACTIVE",
        "DISABLED",
        "ACTIVE",
        "MISSING",
    ]
    FakeZbox.unreachable = True
    rows = normaluser_client.get("/zpods/name=lab/networks").json()
    assert {n["status"] for n in rows} == {"UNKNOWN"}


def test_zcore_component_gates_every_zboxapi_call(normaluser_client, lab, session):
    # zcore ACTIVE while the zPod still builds: zboxapi is asked, add works.
    lab.status = "BUILDING"
    session.add(lab)
    session.commit()
    rows = normaluser_client.get("/zpods/name=lab/networks").json()
    assert {n["status"] for n in rows} == {"ACTIVE"}
    assert ("GET", "/vlan", None) in FakeZbox.calls
    assert add(normaluser_client).status_code == 201
    FakeZbox.calls.clear()
    # zcore still BUILDING (the deploy's first minutes): nothing is asked, 409.
    lab.components[0].status = "BUILDING"
    session.add(lab)
    session.commit()
    rows = normaluser_client.get("/zpods/name=lab/networks").json()
    assert {n["status"] for n in rows} == {"UNKNOWN"}
    r = add(normaluser_client, name="wld02", vlan=2000, gateway="10.10.200.1/24")
    assert r.status_code == 409 and "needs a running zcore" in r.json()["detail"]
    r = normaluser_client.put("/zpods/name=lab/networks/wld01/disable")
    assert r.status_code == 409
    assert FakeZbox.calls == []
    # Deleting: never asked, even with an ACTIVE zcore row.
    lab.components[0].status = "ACTIVE"
    lab.status = "DELETING"
    session.add(lab)
    session.commit()
    rows = normaluser_client.get("/zpods/name=lab/networks").json()
    assert {n["status"] for n in rows} == {"UNKNOWN"}
    assert FakeZbox.calls == []


def test_list_requires_reader(superadmin_client, normaluser_client, lab, session):
    other = M.User(
        username="stranger",
        email="s@x",
        api_token="T3",
        superadmin=False,
        status="ENABLED",
    )
    session.add(other)
    session.commit()
    normaluser_client.headers["access_token"] = "T3"
    # The zPod lookup itself is permission-scoped: a stranger never sees it.
    assert normaluser_client.get("/zpods/name=lab/networks").status_code == 404


# ── add ───────────────────────────────────────────────────────────────────────


def test_add_local_network(normaluser_client, lab):
    r = add(normaluser_client, masquerade=True)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["name"] == "wld01" and body["vlan_id"] == 1000
    assert body["cidr"] == "10.10.100.0/24" and body["gateway"] == "10.10.100.1/24"
    assert body["kind"] == "user" and body["routing"] == "LOCAL"
    assert body["masquerade"] is True and body["status"] == "ACTIVE"
    assert (
        "POST",
        "/vlan",
        {"vlan": 1000, "gateway": "10.10.100.1/24", "masquerade": True},
    ) in FakeZbox.calls
    assert FakeZpodEngineClient.calls == []
    rows = normaluser_client.get("/zpods/name=lab/networks").json()
    assert [n["name"] for n in rows][-1] == "wld01"


@pytest.mark.parametrize("vlan", [30, 10])
def test_add_system_default_vlan_refused_by_zboxapi(normaluser_client, lab, vlan):
    # zboxapi owns the reserved ids; its 403 is passed through unchanged.
    r = add(normaluser_client, vlan=vlan, gateway="10.10.64.1/24")
    assert r.status_code == 403, r.text
    assert f"VLAN {vlan} is a system default VLAN" in r.json()["detail"]
    assert (
        normaluser_client.get("/zpods/name=lab/networks").json()[-1]["name"]
        == "vlan192"
    )


@pytest.mark.parametrize("vlan", [64, 192])
def test_add_system_zpod_vlan_refused_before_zboxapi(normaluser_client, lab, vlan):
    # 64/128/192 are already rows of the zPod: the duplicate check answers first.
    r = add(normaluser_client, vlan=vlan, gateway="10.10.64.1/24")
    assert r.status_code == 409, r.text
    assert f"VLAN {vlan} is already used on this zPod" in r.json()["detail"]
    assert FakeZbox.calls == []


def test_add_native_vlan_rejected_by_schema(normaluser_client, lab):
    assert add(normaluser_client, vlan=0).status_code == 422
    assert FakeZbox.calls == []


def test_add_duplicate_vlan_and_name(normaluser_client, lab):
    assert add(normaluser_client).status_code == 201
    r = add(normaluser_client, name="again")
    assert (
        r.status_code == 409
        and "already used on this zPod by network wld01" in r.json()["detail"]
    )
    r = add(normaluser_client, vlan=1001, gateway="10.10.101.1/24")
    assert (
        r.status_code == 409
        and "Network name wld01 is already used" in r.json()["detail"]
    )


def test_add_overlap_with_own_networks(normaluser_client, lab):
    r = add(normaluser_client, name="clash", vlan=1500, gateway="10.60.60.129/26")
    assert r.status_code == 422, r.text
    assert (
        "overlaps with vlan128 (10.60.60.128/26), a zPodFactory network"
        in r.json()["detail"]
    )
    assert FakeZbox.calls == []


def test_add_overlap_with_endpoint_pool(normaluser_client, lab):
    r = add(normaluser_client, name="pool", vlan=1500, gateway="10.60.70.1/24")
    assert r.status_code == 422, r.text
    assert "endpoint's zPod pool (10.60.0.0/16)" in r.json()["detail"]


def test_add_global_requires_superadmin(normaluser_client, lab):
    r = add(normaluser_client, routing="GLOBAL")
    assert r.status_code == 403, r.text
    assert "superadmin" in r.json()["detail"]
    assert FakeZbox.calls == []  # nothing created
    assert (
        normaluser_client.get("/zpods/name=lab/networks").json()[-1]["name"]
        == "vlan192"
    )


def test_add_global_as_superadmin_schedules_the_flow(superadmin_client, lab):
    r = add(superadmin_client, routing="GLOBAL")
    assert r.status_code == 201, r.text
    assert r.json()["routing"] == "PENDING"
    assert len(FakeZpodEngineClient.calls) == 1
    call = FakeZpodEngineClient.calls[0]
    assert call["flow_name"] == "zpod_network_routing"
    assert call["target"] == "GLOBAL" and call["requested_by"] == "superuser"
    assert call["verb"] == "advertise" and call["network_name"] == "wld01"


def test_add_masquerade_on_old_zboxapi_refused_up_front(normaluser_client, lab):
    # zboxapi 0.1.1 lists VLANs without a masquerade field and would silently
    # ignore the option: refuse before creating anything.
    for v in FakeZbox.vlans:
        v.pop("masquerade", None)
    r = add(normaluser_client, masquerade=True)
    assert r.status_code == 501, r.text
    assert "needs zboxapi 0.2.0" in r.json()["detail"]
    assert not [c for c in FakeZbox.calls if c[0] == "POST"]
    # Without the option the old zcore is fine, and the row never claims masquerade.
    r = add(normaluser_client)
    assert r.status_code == 201 and r.json()["masquerade"] is False
    r = normaluser_client.put(
        "/zpods/name=lab/networks/wld01/masquerade", json={"enabled": True}
    )
    assert r.status_code == 501


def test_add_when_zcore_unreachable(normaluser_client, lab):
    FakeZbox.unreachable = True
    r = add(normaluser_client)
    assert r.status_code == 503
    assert (
        normaluser_client.get("/zpods/name=lab/networks").json()[-1]["name"]
        == "vlan192"
    )


def test_name_keeps_its_case_and_lookups_ignore_it(normaluser_client, lab):
    r = add(normaluser_client, name="LOCALNET111")
    assert r.status_code == 201 and r.json()["name"] == "LOCALNET111"
    assert (
        normaluser_client.get("/zpods/name=lab/networks/localnet111").status_code == 200
    )
    r = add(normaluser_client, name="localnet111", vlan=1001, gateway="10.10.101.1/24")
    assert r.status_code == 409


def test_add_bad_gateway(normaluser_client, lab):
    assert add(normaluser_client, gateway="10.10.100.0/24").status_code == 422
    assert add(normaluser_client, gateway="10.10.100.1").status_code == 422
    assert add(normaluser_client, gateway="10.10.100.1/31").status_code == 422


# ── remove ────────────────────────────────────────────────────────────────────


def test_remove_zpod_row_refused(superadmin_client, lab):
    r = superadmin_client.delete("/zpods/name=lab/networks/vlan64")
    assert r.status_code == 403 and "kind zpod" in r.json()["detail"]
    assert FakeZbox.calls == []


def test_remove_global_refused(superadmin_client, lab, session):
    add(superadmin_client)
    network = session.exec(
        M.ZpodNetwork.__table__.select().where(M.ZpodNetwork.name == "wld01")
    ).one()
    session.get(M.ZpodNetwork, network.id).routing = ZpodNetworkRouting.GLOBAL
    session.commit()
    r = superadmin_client.delete("/zpods/name=lab/networks/wld01")
    assert r.status_code == 409 and "routing lab wld01 local" in r.json()["detail"]


def test_remove_with_dns_records_inside(normaluser_client, lab):
    add(normaluser_client)
    FakeZbox.dns = [
        {"ip": "10.10.100.11", "hostname": "esx-w01"},
        {"ip": "10.10.100.12", "hostname": "esx-w02"},
        {"ip": "10.60.60.10", "hostname": "vcsa"},
    ]
    r = normaluser_client.delete("/zpods/name=lab/networks/wld01")
    assert r.status_code == 409, r.text
    assert (
        "2 DNS record(s) of lab point into 10.10.100.0/24 (esx-w01, esx-w02)"
        in r.json()["detail"]
    )


def test_remove_ok_and_missing_on_box(normaluser_client, lab):
    add(normaluser_client)
    r = normaluser_client.delete("/zpods/name=lab/networks/wld01")
    assert r.status_code == 204, r.text
    assert ("DELETE", "/vlan/1000", None) in FakeZbox.calls
    assert normaluser_client.get("/zpods/name=lab/networks/wld01").status_code == 404
    # Gone on the box already: the row still goes.
    add(normaluser_client)
    FakeZbox.responses[("DELETE", "/vlan/1000")] = FakeResponse(
        "VLAN 1000 not found", 404
    )
    assert normaluser_client.delete("/zpods/name=lab/networks/wld01").status_code == 204


# ── masquerade / enable / disable ─────────────────────────────────────────────


def test_masquerade_toggle(normaluser_client, lab):
    add(normaluser_client)
    r = normaluser_client.put(
        "/zpods/name=lab/networks/wld01/masquerade", json={"enabled": True}
    )
    assert r.status_code == 200 and r.json()["masquerade"] is True
    assert ("PUT", "/vlan/1000/masquerade", {"enabled": True}) in FakeZbox.calls
    r = normaluser_client.put(
        "/zpods/name=lab/networks/wld01/masquerade", json={"enabled": False}
    )
    assert r.status_code == 200 and r.json()["masquerade"] is False


def test_masquerade_refused_on_zpod_row_and_while_global(
    superadmin_client, lab, session
):
    r = superadmin_client.put(
        "/zpods/name=lab/networks/mgmt/masquerade", json={"enabled": True}
    )
    assert (
        r.status_code == 403 and "masquerading cannot be changed" in r.json()["detail"]
    )
    add(superadmin_client)
    session.exec(
        M.ZpodNetwork.__table__.update()
        .where(M.ZpodNetwork.name == "wld01")
        .values(routing="GLOBAL")
    )
    session.commit()
    r = superadmin_client.put(
        "/zpods/name=lab/networks/wld01/masquerade", json={"enabled": True}
    )
    assert r.status_code == 409 and "Set routing local first" in r.json()["detail"]


def test_enable_disable(normaluser_client, lab):
    add(normaluser_client)
    r = normaluser_client.put("/zpods/name=lab/networks/wld01/disable")
    assert r.status_code == 200 and r.json()["status"] == "DISABLED"
    r = normaluser_client.put("/zpods/name=lab/networks/wld01/enable")
    assert r.status_code == 200 and r.json()["status"] == "ACTIVE"
    r = normaluser_client.put("/zpods/name=lab/networks/vlan128/disable")
    assert r.status_code == 403 and "cannot be disabled" in r.json()["detail"]


# ── routing ───────────────────────────────────────────────────────────────────


def test_disable_is_allowed_on_a_global_user_network_only(
    superadmin_client, lab, session
):
    # user network, routing GLOBAL: disable is the deliberate blackhole (the T1
    # route stays, the interface goes down), enable brings it back.
    add(superadmin_client)
    session.exec(
        M.ZpodNetwork.__table__.update()
        .where(M.ZpodNetwork.name == "wld01")
        .values(routing="GLOBAL")
    )
    session.commit()
    r = superadmin_client.put("/zpods/name=lab/networks/wld01/disable")
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "DISABLED" and r.json()["routing"] == "GLOBAL"
    assert ("PUT", "/vlan/1000/disable", None) in FakeZbox.calls
    r = superadmin_client.put("/zpods/name=lab/networks/wld01/enable")
    assert r.status_code == 200 and r.json()["status"] == "ACTIVE"
    # the two other kinds are refused before zcore is called, superadmin or not
    FakeZbox.calls.clear()
    for name in ("vlan192", "vlan10"):
        r = superadmin_client.put(f"/zpods/name=lab/networks/{name}/disable")
        assert r.status_code == 403, name
    assert all(
        c[0] == "GET" for c in FakeZbox.calls
    )  # only live reads, no disable sent


def test_routing_requires_superadmin(normaluser_client, lab):
    add(normaluser_client)
    r = normaluser_client.put(
        "/zpods/name=lab/networks/wld01/routing", json={"routing": "GLOBAL"}
    )
    assert r.status_code == 403
    assert FakeZpodEngineClient.calls == []


def test_routing_global_then_local(superadmin_client, lab, session):
    add(superadmin_client)
    r = superadmin_client.put(
        "/zpods/name=lab/networks/wld01/routing", json={"routing": "GLOBAL"}
    )
    assert r.status_code == 202, r.text
    assert (
        r.json()["network"]["routing"] == "PENDING"
        and r.json()["flow_run_id"] == "run-1"
    )
    call = FakeZpodEngineClient.calls[0]
    assert call["flow_name"] == "zpod_network_routing" and call["target"] == "GLOBAL"
    assert call["dry_run"] is False and call["verb"] == "advertise"
    assert call["previous"] == "LOCAL"
    # A second change while pending is refused.
    r = superadmin_client.put(
        "/zpods/name=lab/networks/wld01/routing", json={"routing": "LOCAL"}
    )
    assert r.status_code == 409
    # The flow finished: GLOBAL. Same value again → no flow.
    session.exec(
        M.ZpodNetwork.__table__.update()
        .where(M.ZpodNetwork.name == "wld01")
        .values(routing="GLOBAL")
    )
    session.commit()
    r = superadmin_client.put(
        "/zpods/name=lab/networks/wld01/routing", json={"routing": "GLOBAL"}
    )
    assert r.status_code == 202 and r.json()["flow_run_id"] is None
    assert len(FakeZpodEngineClient.calls) == 1
    # Back to local: the withdraw run.
    r = superadmin_client.put(
        "/zpods/name=lab/networks/wld01/routing", json={"routing": "LOCAL"}
    )
    assert r.status_code == 202 and r.json()["network"]["routing"] == "PENDING"
    assert FakeZpodEngineClient.calls[-1]["verb"] == "withdraw"


def test_routing_dry_run_and_zpod_rows(superadmin_client, lab):
    add(superadmin_client)
    r = superadmin_client.put(
        "/zpods/name=lab/networks/wld01/routing",
        json={"routing": "GLOBAL", "dry_run": True},
    )
    assert r.status_code == 202 and FakeZpodEngineClient.calls[-1]["dry_run"] is True
    assert FakeZpodEngineClient.calls[-1]["verb"] == "advertise (dry run)"
    r = superadmin_client.put(
        "/zpods/name=lab/networks/vlan192/routing", json={"routing": "LOCAL"}
    )
    assert r.status_code == 403 and "fixed to global" in r.json()["detail"]


def test_routing_run_reports_state_and_the_failing_check(superadmin_client, lab):
    # one TestClient behind both fixtures: switch the token by hand for the reader
    normaluser_client = superadmin_client
    add(superadmin_client)
    r = superadmin_client.put(
        "/zpods/name=lab/networks/wld01/routing", json={"routing": "GLOBAL"}
    )
    assert r.status_code == 202
    run_id = r.json()["flow_run_id"]

    # still scheduled: the row is PENDING, no message (any reader may look)
    normaluser_client.headers["access_token"] = "APITOKEN_NORMALUSER"
    r = normaluser_client.get(f"/zpods/name=lab/networks/wld01/routing/{run_id}")
    assert r.status_code == 200, r.text
    assert r.json()["state"] == "SCHEDULED" and r.json()["message"] is None
    assert r.json()["network"]["routing"] == "PENDING"
    assert r.json()["name"] == "advertise lab/wld01 by superuser"

    # the engine failed a check and its hook put the row back
    FakeZpodEngineClient.runs[run_id].update(
        state="FAILED",
        message=(
            "Flow run encountered an exception: ValueError: FAIL: 10.10.100.0/24 "
            "overlaps 10.10.0.0/16 from the routing table of T0 t0 (route_type b)"
        ),
    )
    r = normaluser_client.get(f"/zpods/name=lab/networks/wld01/routing/{run_id}")
    assert r.json()["state"] == "FAILED"
    assert r.json()["message"].startswith("FAIL: 10.10.100.0/24 overlaps 10.10.0.0/16")


def test_routing_run_unknown_or_another_networks_run_is_404(superadmin_client, lab):
    add(superadmin_client)
    r = superadmin_client.put(
        "/zpods/name=lab/networks/wld01/routing", json={"routing": "GLOBAL"}
    )
    run_id = r.json()["flow_run_id"]
    r = superadmin_client.get("/zpods/name=lab/networks/wld01/routing/nope")
    assert r.status_code == 404
    # a run that exists but belongs to another network of the zPod
    r = superadmin_client.get(f"/zpods/name=lab/networks/vlan64/routing/{run_id}")
    assert r.status_code == 404
