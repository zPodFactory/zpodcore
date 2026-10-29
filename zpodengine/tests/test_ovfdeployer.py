"""ovf_deployer with and without component_deploy_extra_config, on both deploy paths.

govc, vCenter and the OVA staging are faked; what is checked is the order: the VM
is created powered off, then its guestinfo.* keys are set, on the direct import and
on the staging clone alike. A component without the key deploys as before.
"""

import json
from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from zpodcommon.lib.component_network import ComponentNetworkError
from zpodengine.lib import ova_staging, ovfdeployer
from zpodengine.lib.deploy_spec import ExtraConfigError

GOVC_SPEC = {
    "DiskProvisioning": "thin",
    "NetworkMapping": [{"Name": "VM Network", "Network": "{{zpod_portgroup}}"}],
    "PowerOn": True,
    "InjectOvfEnv": False,
}
EXTRA = {
    "guestinfo.metadata": {
        "format": "yaml",
        "content": {
            "instance-id": "{{zpod_hostname}}",
            "local-hostname": "{{zpod_hostname}}",
        },
    }
}


class World:
    """Records what the deployer does, in order."""

    def __init__(self):
        self.events: list[tuple] = []
        self.staging = None  # None: ff_endpoint_ova_staging off; "ok" | "fail"
        self.vm_exists = False


@pytest.fixture
def world(tmp_path, monkeypatch):
    w = World()

    settings = {
        "zpodfactory_host": "10.42.111.1",
        "zpodfactory_ssh_key": "ssh-ed25519 K",
    }
    monkeypatch.setattr(
        ovfdeployer.DBUtils,
        "get_setting_value",
        classmethod(
            lambda cls, name: (
                ("true" if w.staging else None)
                if name == "ff_endpoint_ova_staging"
                else settings.get(name)
            )
        ),
    )
    monkeypatch.setattr(
        ovfdeployer.MgmtIp,
        "zpod",
        classmethod(
            lambda cls, zpod, name: SimpleNamespace(
                ip="10.42.111.1" if name == "gw" else "10.42.111.2",
                netmask="255.255.255.0",
            )
        ),
    )

    def cmd_execute(cmd):
        options_file = cmd.split("-options=")[1].split()[0]
        with open(options_file) as f:
            options = json.load(f)
        w.options, w.cmd = options, cmd
        w.events.append(("import", options["PowerOn"]))
        w.vm_exists = True

    monkeypatch.setattr(ovfdeployer, "cmd_execute", cmd_execute)

    def deploy_from_template(**kw):
        if w.staging == "fail":
            raise RuntimeError("no template")
        w.events.append(("clone", kw["vm_name"]))
        w.vm_exists = True

    monkeypatch.setattr(ova_staging, "deploy_from_template", deploy_from_template)

    class FakeVc:
        def get_vm(self, name):
            return SimpleNamespace(name=name) if w.vm_exists else None

        def set_extra_config(self, vm, values):
            w.events.append(("extra_config", vm.name, dict(values)))

    @contextmanager
    def auth(cls, zpod):
        w.events.append(("auth",))
        yield FakeVc()

    monkeypatch.setattr(ovfdeployer.vCenter, "auth_by_zpod_endpoint", classmethod(auth))
    monkeypatch.setattr(ovfdeployer.vCenter, "auth_by_zpod", classmethod(auth))

    # The govc options file goes to /tmp/<fqdn>.json; keep it in the test's tmp dir.
    real_open = open

    def tmp_open(path, *a, **kw):
        if isinstance(path, str) and path.startswith("/tmp/"):
            path = str(tmp_path / path.removeprefix("/tmp/"))
        return real_open(path, *a, **kw)

    monkeypatch.setattr("builtins.open", tmp_open)
    return w


def zpod_component(extra=None):
    component_json = {
        "component_name": "ubuntu",
        "component_deploy_govc_spec": GOVC_SPEC,
        "component_isnested": False,
    }
    if extra is not None:
        component_json["component_deploy_extra_config"] = extra
    mgmt = SimpleNamespace(
        name="mgmt", cidr="10.42.111.0/26", gateway="10.42.111.1/26", vlan_id=0
    )
    zpod = SimpleNamespace(
        networks=[mgmt],
        mgmt_network=mgmt,
        name="lab",
        domain="lab.zpod.example",
        password="secret",
        endpoint=SimpleNamespace(
            endpoints={
                "compute": {
                    "hostname": "vcsa.example",
                    "username": "admin",
                    "password": "pw",
                    "datacenter": "DC",
                    "storage_datastore": "ds01",
                }
            }
        ),
    )
    component = SimpleNamespace(
        component_name="ubuntu",
        component_version="24.04",
        component_uid="ubuntu-24.04",
        filename="ubuntu.ova",
        component_json=component_json,
    )
    return SimpleNamespace(
        component=component,
        zpod=zpod,
        hostname="node1",
        fqdn="node1.lab.zpod.example",
        ip="10.42.111.30",
    )


def extra_event(world):
    (event,) = [e for e in world.events if e[0] == "extra_config"]
    return event


def test_without_extra_config_nothing_changes(world):
    ovfdeployer.ovf_deployer(zpod_component())
    # PowerOn stays what the library JSON says; no reconfigure, no vCenter login.
    assert world.events == [("import", True)]


def test_direct_import_powered_off_then_extra_config(world):
    ovfdeployer.ovf_deployer(zpod_component(EXTRA))
    assert [e[0] for e in world.events] == ["import", "auth", "extra_config"]
    assert world.events[0] == ("import", False)
    _, vm_name, values = extra_event(world)
    assert vm_name == "node1.lab.zpod.example"
    assert set(values) == {"guestinfo.metadata", "guestinfo.metadata.encoding"}


def test_staging_clone_then_extra_config(world):
    world.staging = "ok"
    ovfdeployer.ovf_deployer(zpod_component(EXTRA))
    assert [e[0] for e in world.events] == ["clone", "auth", "extra_config"]


def test_staging_failure_falls_back_to_import_then_extra_config(world):
    world.staging = "fail"
    ovfdeployer.ovf_deployer(zpod_component(EXTRA))
    assert [e[0] for e in world.events] == ["import", "auth", "extra_config"]
    assert world.events[0] == ("import", False)


def test_staging_without_extra_config_is_unchanged(world):
    world.staging = "ok"
    ovfdeployer.ovf_deployer(zpod_component())
    assert world.events == [("clone", "node1.lab.zpod.example")]


def test_bad_extra_config_fails_before_any_vm(world):
    with pytest.raises(ExtraConfigError):
        ovfdeployer.ovf_deployer(zpod_component({"disk.EnableUUID": "TRUE"}))
    assert world.events == []


# --- nested components: the network object ---------------------------------

NET_EXTRA = {
    "guestinfo.net": "{{zpod_ipaddress}}/{{zpod_netprefix}} via {{zpod_gateway}}"
}


@pytest.fixture
def portgroup_checks(monkeypatch):
    checked = []
    monkeypatch.setattr(
        ovfdeployer,
        "check_nested_portgroup",
        lambda zpod, portgroup: checked.append(portgroup),
    )
    return checked


def test_nested_without_network_is_unchanged(world, portgroup_checks):
    ovfdeployer.ovf_deployer(zpod_component(), nested=True)
    assert world.options["NetworkMapping"][0]["Network"] == "VM Network"
    assert "-pool=Cluster/Resources" in world.cmd
    assert portgroup_checks == []


def test_nested_network_reaches_spec_and_extra_config(world, portgroup_checks):
    zc = zpod_component(NET_EXTRA)
    zc.ip = "192.168.10.20"  # what the prep task stored from network.ip
    network = {
        "ip": "192.168.10.20/24",
        "gateway": "192.168.10.1",
        "portgroup": "VM Network",
    }
    ovfdeployer.ovf_deployer(zc, nested=True, network=network)
    assert portgroup_checks == ["VM Network"]
    assert world.options["NetworkMapping"][0]["Network"] == "VM Network"
    _, vm_name, values = extra_event(world)
    assert vm_name == "node1"
    assert values["guestinfo.net"] == "192.168.10.20/24 via 192.168.10.1"


def test_network_is_ignored_on_the_endpoint(world, portgroup_checks):
    # The API refuses it; the engine still never applies it to an L1 deploy.
    ovfdeployer.ovf_deployer(
        zpod_component(), nested=False, network={"portgroup": "pg"}
    )
    assert portgroup_checks == []
    assert world.options["NetworkMapping"][0]["Network"].endswith("-lab-segment")


# --- check_nested_portgroup ---------------------------------------------------


def net(name, path, standard=True, hosts=("esxi11", "esxi12"), vlan=0):
    return {
        "name": name,
        "path": path,
        "paths": {path},
        "standard": standard,
        "hosts": list(hosts),
        "vlan": vlan,
    }


NETWORKS = [
    net("VM Network", "/Datacenter/network/VM Network"),
    net("pg-a", "/Datacenter/network/pg-a", hosts=("esxi11",)),
    net("dup", "/Datacenter/network/DSwitch/dup", standard=False),
    net("dup", "/Datacenter/network/DSwitch2/dup", standard=False),
]


@pytest.fixture
def fake_zpod_vc(monkeypatch):
    class Vc:
        def list_networks(self):
            return NETWORKS

        def find_networks(self, name_or_path):
            if name_or_path.startswith("/"):
                return [n for n in NETWORKS if name_or_path in n["paths"]]
            return [n for n in NETWORKS if n["name"] == name_or_path]

        def get_cluster_host_names(self, name):
            assert name == "Cluster"
            return ["esxi11", "esxi12"]

    @contextmanager
    def auth(cls, zpod):
        yield Vc()

    monkeypatch.setattr(ovfdeployer.vCenter, "auth_by_zpod", classmethod(auth))
    return SimpleNamespace(domain="lab.zpod.example")


def test_portgroup_found(fake_zpod_vc):
    ovfdeployer.check_nested_portgroup(fake_zpod_vc, "VM Network")
    ovfdeployer.check_nested_portgroup(fake_zpod_vc, "/Datacenter/network/DSwitch/dup")


def test_portgroup_missing(fake_zpod_vc):
    with pytest.raises(
        ComponentNetworkError, match="'nope' not found in vcsa.lab.zpod.example"
    ):
        ovfdeployer.check_nested_portgroup(fake_zpod_vc, "nope")


def test_portgroup_ambiguous(fake_zpod_vc):
    with pytest.raises(ComponentNetworkError) as e:
        ovfdeployer.check_nested_portgroup(fake_zpod_vc, "dup")
    assert (
        "/Datacenter/network/DSwitch/dup (distributed), "
        "/Datacenter/network/DSwitch2/dup (distributed). "
        "Use the distributed portgroup's path." in str(e.value)
    )


def test_ambiguous_with_a_standard_portgroup(fake_zpod_vc):
    NETWORKS.append(net("VM Network", "/Datacenter/network/DSwitch/VM Network", False))
    try:
        with pytest.raises(ComponentNetworkError, match="rename one of them"):
            ovfdeployer.check_nested_portgroup(fake_zpod_vc, "VM Network")
    finally:
        NETWORKS.pop()


def test_standard_portgroup_missing_on_a_host(fake_zpod_vc):
    with pytest.raises(
        ComponentNetworkError, match="present on esxi11 only; missing on esxi12"
    ):
        ovfdeployer.check_nested_portgroup(fake_zpod_vc, "pg-a")


# --- vlan_id (ESXi on a tagged zPod network) ------------------------------------


def test_vlan_id_sets_zpod_vlan_and_the_vlan_network(world, monkeypatch):
    zc = zpod_component()
    zc.ip = "10.42.111.71"
    vlan64 = SimpleNamespace(
        name="vlan64", cidr="10.42.111.64/26", gateway="10.42.111.65/26", vlan_id=64
    )
    zc.zpod.networks.append(vlan64)
    zc.component.component_json["component_deploy_govc_spec"] = {
        **GOVC_SPEC,
        "PropertyMapping": [
            {"Key": "guestinfo.ipaddress", "Value": "{{zpod_ipaddress}}"},
            {"Key": "guestinfo.netmask", "Value": "{{zpod_netmask}}"},
            {"Key": "guestinfo.gateway", "Value": "{{zpod_gateway}}"},
            {"Key": "guestinfo.vlan", "Value": "{{zpod_vlan}}"},
        ],
    }
    ovfdeployer.ovf_deployer(zc, vlan_id=64)
    props = {p["Key"]: p["Value"] for p in world.options["PropertyMapping"]}
    assert props == {
        "guestinfo.ipaddress": "10.42.111.71",
        "guestinfo.netmask": "255.255.255.192",
        "guestinfo.gateway": "10.42.111.65",
        "guestinfo.vlan": "64",
    }
    # Still on the endpoint, on the zPod segment (a trunk).
    assert world.options["NetworkMapping"][0]["Network"].endswith("-lab-segment")


def test_without_vlan_id_zpod_vlan_is_empty(world):
    zc = zpod_component()
    zc.component.component_json["component_deploy_govc_spec"] = {
        **GOVC_SPEC,
        "PropertyMapping": [{"Key": "guestinfo.vlan", "Value": "{{zpod_vlan}}"}],
    }
    ovfdeployer.ovf_deployer(zc)
    assert world.options["PropertyMapping"] == [{"Key": "guestinfo.vlan", "Value": ""}]


def test_vlan_id_nested_on_a_trunk_portgroup(world, portgroup_checks):
    # A guest that tags its own frames, nested on a trunk portgroup.
    zc = zpod_component()
    zc.ip = "10.42.111.71"
    zc.zpod.networks.append(
        SimpleNamespace(
            name="vlan64", cidr="10.42.111.64/26", gateway="10.42.111.65/26", vlan_id=64
        )
    )
    zc.component.component_json["component_deploy_govc_spec"] = {
        **GOVC_SPEC,
        "PropertyMapping": [{"Key": "guestinfo.vlan", "Value": "{{zpod_vlan}}"}],
    }
    ovfdeployer.ovf_deployer(
        zc, nested=True, network={"portgroup": "TRUNK"}, vlan_id=64
    )
    assert portgroup_checks == ["TRUNK"]
    assert world.options["NetworkMapping"][0]["Network"] == "TRUNK"
    assert world.options["PropertyMapping"] == [
        {"Key": "guestinfo.vlan", "Value": "64"}
    ]
    assert "-pool=Cluster/Resources" in world.cmd
