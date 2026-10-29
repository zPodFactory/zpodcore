"""nested, network and vlan_id reach every step, from a profile item to ovf_deployer.

Each step is called with its tasks replaced by recorders, so a parameter dropped on
the way (which would silently deploy with the defaults) fails here.
"""

import sqlite3
from contextlib import contextmanager
from ipaddress import IPv4Address
from types import SimpleNamespace

import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from zpodcommon import models as M
from zpodengine.lib import database as engine_database
from zpodengine.zpod_component_add import (
    flow_zpod_component_add,
    zpod_component_add,
    zpod_component_add_1_prep,
    zpod_component_add_3_deploy,
)
from zpodengine.zpod_deploy import flow_zpod_deploy

OPTIONS = {"nested": True, "network": {"portgroup": "TRUNK"}, "vlan_id": 64}


class Recorder:
    """Stands in for a Prefect task: with_options(...).submit(...) or a direct call."""

    def __init__(self, result=None):
        self.calls = []
        self._result = result

    def with_options(self, **_):
        return self

    def submit(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(result=lambda: self._result)

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        return self._result


def test_flow_zpod_deploy_passes_profile_options(monkeypatch):
    profile = [
        {"component_uid": "zcore-1"},
        [
            {
                "component_uid": "esxi-1",
                "host_id": 71,
                "hostname": "esxi71",
                "vlan_id": 64,
            }
        ],
        {"component_uid": "zbox-1", "host_id": 52, "hostname": "zbox52", **OPTIONS},
    ]
    for name in (
        "zpod_datastore_floor",
        "zpod_deploy_prep",
        "zpod_deploy_dnsmasq",
        "zpod_deploy_networking",
        "zpod_deploy_vapp",
        "zpod_deploy_config_scripts",
        "zpod_deploy_finalize",
    ):
        monkeypatch.setattr(flow_zpod_deploy, name, Recorder())
    monkeypatch.setattr(flow_zpod_deploy, "zpod_deploy_get_profile", Recorder(profile))
    add = Recorder()
    monkeypatch.setattr(flow_zpod_deploy, "zpod_component_add", add)

    flow_zpod_deploy.flow_zpod_deploy.fn(
        zpod_id=1, profile="p", zpod_name="lab", enet_name=None
    )

    zcore, esxi, zbox = add.calls
    assert (zcore["nested"], zcore["network"], zcore["vlan_id"]) == (None, None, None)
    assert (esxi["host_id"], esxi["vlan_id"], esxi["nested"]) == (71, 64, None)
    assert {k: zbox[k] for k in OPTIONS} == OPTIONS


def test_flow_zpod_component_add_passes_options(monkeypatch):
    add = Recorder()
    monkeypatch.setattr(
        flow_zpod_component_add,
        "zpod_component_add",
        lambda **kw: add.submit(**kw),
    )
    flow_zpod_component_add.flow_zpod_component_add.fn(
        zpod_id=1, zpod_name="lab", component_uid="zbox-1", host_id=52, **OPTIONS
    )
    assert {k: add.calls[0][k] for k in OPTIONS} == OPTIONS


def test_zpod_component_add_sends_options_to_prep_and_deploy(monkeypatch):
    prep = Recorder(SimpleNamespace(id=7, hostname="zbox52"))
    deploy = Recorder()
    monkeypatch.setattr(zpod_component_add, "zpod_component_add_prep", prep)
    monkeypatch.setattr(zpod_component_add, "zpod_component_add_deploy", deploy)
    for name in (
        "zpod_component_add_pre_scripts",
        "zpod_component_add_post_scripts",
        "zpod_component_add_config_scripts",
        "zpod_component_add_finalize",
    ):
        monkeypatch.setattr(zpod_component_add, name, Recorder())

    zpod_component_add.zpod_component_add(
        zpod_id=1, zpod_name="lab", component_uid="zbox-1", host_id=52, **OPTIONS
    )

    # The prep task picks the address: it needs network and vlan_id.
    assert (prep.calls[0]["network"], prep.calls[0]["vlan_id"]) == (
        OPTIONS["network"],
        64,
    )
    assert {k: deploy.calls[0][k] for k in OPTIONS} == OPTIONS
    assert deploy.calls[0]["zpod_component_id"] == 7


# --- the deploy task hands them to ovf_deployer ------------------------------------


@pytest.fixture
def deploy_world(monkeypatch):
    calls = {"ovf_deployer": [], "floor": []}

    def component(name, isnested=False):
        return SimpleNamespace(
            component=SimpleNamespace(
                component_name=name,
                component_json={"component_isnested": isnested},
            ),
            zpod=SimpleNamespace(name="lab"),
            hostname="h",
            fqdn="h.lab",
        )

    current = {}

    class FakeSession:
        def get(self, model, id):
            return current["component"]

    @contextmanager
    def ctx():
        yield FakeSession()

    class FakeVc:
        def get_vm(self, name):
            return SimpleNamespace(name=name)

        def set_vm_configuration(self, **kw):
            pass

        def poweron_vm(self, vm):
            pass

    @contextmanager
    def auth(cls, zpod):
        yield FakeVc()

    mod = zpod_component_add_3_deploy
    monkeypatch.setattr(mod.database, "get_session_ctx", ctx)
    monkeypatch.setattr(
        mod, "ovf_deployer", lambda zc, **kw: calls["ovf_deployer"].append(kw)
    )
    monkeypatch.setattr(
        mod, "check_endpoint_datastore_floor", lambda *a: calls["floor"].append(a)
    )
    monkeypatch.setattr(mod.vCenter, "auth_by_zpod", classmethod(auth))
    monkeypatch.setattr(mod.vCenter, "auth_by_zpod_endpoint", classmethod(auth))

    def run(name, isnested=False, **kwargs):
        current["component"] = component(name, isnested)
        calls["ovf_deployer"].clear()
        calls["floor"].clear()
        mod.zpod_component_add_deploy.fn(zpod_component_id=1, **kwargs)
        return calls

    return run


def test_generic_branch_gets_every_option(deploy_world):
    calls = deploy_world("zbox", **OPTIONS)
    assert calls["ovf_deployer"] == [OPTIONS]
    # Nested: not on the endpoint datastore, so no floor check.
    assert calls["floor"] == []


def test_generic_branch_on_the_endpoint_checks_the_floor(deploy_world):
    calls = deploy_world("vrops", isnested=True, nested=False)
    assert calls["ovf_deployer"] == [
        {"nested": False, "network": None, "vlan_id": None}
    ]
    assert len(calls["floor"]) == 1


def test_esxi_branch_gets_vlan_id(deploy_world):
    calls = deploy_world("esxi", vlan_id=64)
    assert calls["ovf_deployer"] == [{"vlan_id": 64}]


# --- the prep task stores the resolved address ------------------------------------


@pytest.fixture
def prep_world(monkeypatch):
    # The prep task stores an IPv4Address, which psycopg adapts; SQLite needs help.
    sqlite3.register_adapter(IPv4Address, str)
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)

    @contextmanager
    def ctx():
        with Session(engine) as session:
            yield session

    monkeypatch.setattr(engine_database, "get_session_ctx", ctx)
    mod = zpod_component_add_1_prep
    monkeypatch.setattr(mod, "get_all_active_addresses", lambda zpod: set())
    monkeypatch.setattr(
        "zpodcommon.lib.component_network.DBUtils.get_setting_value",
        classmethod(lambda cls, name: None),
    )
    with Session(engine) as session:
        session.add(
            M.Component(
                component_uid="esxi-1",
                component_name="esxi",
                component_version="1",
                component_description="esxi",
                filename="esxi.ova",
                jsonfile="/library/esxi.json",
                status="ACTIVE",
                download_status="COMPLETED",
                file_checksum="abc",
            )
        )
        zpod = M.Zpod(
            name="lab",
            domain="lab.example",
            endpoint_id=1,
            profile="p",
            status="ACTIVE",
            networks=[
                M.ZpodNetwork(cidr="10.96.1.0/26", name="mgmt", gateway="10.96.1.1/26"),
                M.ZpodNetwork(
                    cidr="10.96.1.64/26",
                    name="vlan64",
                    vlan_id=64,
                    gateway="10.96.1.65/26",
                ),
            ],
        )
        session.add(zpod)
        session.commit()
        zpod_id = zpod.id

    def run(**kwargs):
        zc = mod.zpod_component_add_prep.fn(
            zpod_id=zpod_id, component_uid="esxi-1", hostname="esxi", **kwargs
        )
        return zc.ip, zc.fqdn

    return run


def test_prep_stores_the_vlan_address(prep_world):
    assert prep_world(host_id=71, vlan_id=64) == ("10.96.1.71", "esxi.lab.example")


def test_prep_stores_an_explicit_address(prep_world):
    assert prep_world(network={"ip": "192.168.50.10/24", "gateway": "192.168.50.1"})[
        0
    ] == ("192.168.50.10")


def test_prep_default_address_is_unchanged(prep_world):
    assert prep_world(host_id=11)[0] == "10.96.1.11"


def test_prep_reads_the_portgroup_vlan(prep_world, monkeypatch):
    looked_up = []

    def nested_portgroup(zpod, portgroup):
        looked_up.append(portgroup)
        return {"vlan": 64}

    monkeypatch.setattr(
        "zpodcommon.lib.component_network.nested_portgroup", nested_portgroup
    )
    ip, _ = prep_world(host_id=74, nested=True, network={"portgroup": "PG64"})
    assert (ip, looked_up) == ("10.96.1.74", ["PG64"])
