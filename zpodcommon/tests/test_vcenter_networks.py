"""vCenter.list_networks / find_networks / get_cluster_host_names on fake vSphere objects.

The real ones decide which portgroup a nested VM lands on: every network type, the
paths govc accepts, VDS uplinks left out, the hosts of a standard portgroup.
"""

from types import SimpleNamespace

import pytest

from zpodcommon.lib import vmware


class Obj:
    def __init__(self, name, parent=None, **kw):
        self.name, self.parent = name, parent
        self.__dict__.update(kw)


class Network(Obj):
    pass


class DistributedVirtualPortgroup(Network):
    pass


class OpaqueNetwork(Network):
    pass


class Datacenter(Obj):
    pass


class ClusterComputeResource(Obj):
    pass


@pytest.fixture
def vc(monkeypatch):
    monkeypatch.setattr(
        vmware,
        "vim",
        SimpleNamespace(
            Network=Network,
            OpaqueNetwork=OpaqueNetwork,
            Datacenter=Datacenter,
            ClusterComputeResource=ClusterComputeResource,
            dvs=SimpleNamespace(
                DistributedVirtualPortgroup=DistributedVirtualPortgroup
            ),
        ),
    )
    root = Obj("Datacenters")
    dc = Datacenter("Datacenter", root)
    folder = Obj("network", dc)
    # A standard portgroup's VLAN lives in each host's spec.
    host_pgs = [
        SimpleNamespace(spec=SimpleNamespace(name="DUP", vlanId=109)),
        SimpleNamespace(spec=SimpleNamespace(name="STD", vlanId=4095)),
    ]
    hosts = [
        Obj(
            "esxi11.lab",
            config=SimpleNamespace(network=SimpleNamespace(portgroup=host_pgs)),
        ),
        Obj(
            "esxi12.lab",
            config=SimpleNamespace(network=SimpleNamespace(portgroup=host_pgs)),
        ),
    ]

    def dvpg(name, switch="DSwitch", uplink=False, vlan=0, backing="standard"):
        # VlanIdSpec carries an int, TrunkVlanSpec a list of ranges.
        return DistributedVirtualPortgroup(
            name,
            folder,
            config=SimpleNamespace(
                uplink=uplink,
                backingType=backing,
                distributedVirtualSwitch=SimpleNamespace(name=switch),
                defaultPortConfig=SimpleNamespace(vlan=SimpleNamespace(vlanId=vlan)),
            ),
        )

    networks = [
        dvpg("VM Network"),
        dvpg("DSwitch-DVUplinks-17", uplink=True),
        dvpg("TESTNET", vlan=109),
        dvpg("TRUNK", vlan=[SimpleNamespace(start=0, end=4094)]),
        dvpg("SEGMENT", backing="nsx"),
        dvpg("DUP", switch="DSwitch2", vlan=64),
        Network("DUP", folder, host=hosts[:1]),
        Network("STD", folder, host=hosts),
        OpaqueNetwork("segment-1", folder),
    ]
    cluster = ClusterComputeResource("Cluster", host=hosts)

    v = object.__new__(vmware.vCenter)
    v.get_obj_list = lambda vimtype, **kw: networks
    v.get_obj = lambda vimtype, attr, value, **kw: (
        cluster if value == "Cluster" else None
    )
    return v


def test_list_networks(vc):
    by = {(n["name"], n["path"]): n for n in vc.list_networks()}
    assert set(by) == {
        ("VM Network", "/Datacenter/network/DSwitch/VM Network"),
        ("TESTNET", "/Datacenter/network/DSwitch/TESTNET"),
        ("TRUNK", "/Datacenter/network/DSwitch/TRUNK"),
        ("SEGMENT", "/Datacenter/network/DSwitch/SEGMENT"),
        ("DUP", "/Datacenter/network/DSwitch2/DUP"),
        ("DUP", "/Datacenter/network/DUP"),
        ("STD", "/Datacenter/network/STD"),
        ("segment-1", "/Datacenter/network/segment-1"),
    }, "the VDS uplink portgroup is left out"
    vm_network = by[("VM Network", "/Datacenter/network/DSwitch/VM Network")]
    # A VDS portgroup answers to both paths govc takes.
    assert vm_network["paths"] == {
        "/Datacenter/network/VM Network",
        "/Datacenter/network/DSwitch/VM Network",
    }
    assert vm_network["standard"] is False
    std = by[("STD", "/Datacenter/network/STD")]
    assert (std["standard"], std["hosts"]) == (True, ["esxi11.lab", "esxi12.lab"])
    assert by[("segment-1", "/Datacenter/network/segment-1")]["standard"] is False


@pytest.mark.parametrize(
    "query, paths",
    [
        ("VM Network", ["/Datacenter/network/DSwitch/VM Network"]),
        ("/Datacenter/network/VM Network", ["/Datacenter/network/DSwitch/VM Network"]),
        (
            "/Datacenter/network/DSwitch/TESTNET",
            ["/Datacenter/network/DSwitch/TESTNET"],
        ),
        ("DUP", ["/Datacenter/network/DSwitch2/DUP", "/Datacenter/network/DUP"]),
        # The bare inventory path is shared: still ambiguous, as it is for govc.
        (
            "/Datacenter/network/DUP",
            ["/Datacenter/network/DSwitch2/DUP", "/Datacenter/network/DUP"],
        ),
        ("/Datacenter/network/DSwitch2/DUP", ["/Datacenter/network/DSwitch2/DUP"]),
        ("DSwitch-DVUplinks-17", []),
        ("nope", []),
    ],
)
def test_find_networks(vc, query, paths):
    assert sorted(n["path"] for n in vc.find_networks(query)) == sorted(paths)


def test_get_cluster_host_names(vc):
    assert vc.get_cluster_host_names("Cluster") == ["esxi11.lab", "esxi12.lab"]
    assert vc.get_cluster_host_names("Other") == []


def test_portgroup_vlans(vc):
    vlans = {
        n["path"].rsplit("/", 2)[-2] + "/" + n["name"]: n["vlan"]
        for n in vc.list_networks()
    }
    assert vlans == {
        "DSwitch/VM Network": 0,
        "DSwitch/TESTNET": 109,
        "DSwitch/TRUNK": "trunk",
        "DSwitch/SEGMENT": None,  # NSX-backed: no VLAN to read
        "DSwitch2/DUP": 64,
        "network/DUP": 109,  # standard, read from the host
        "network/STD": "trunk",  # standard, VLAN 4095
        "network/segment-1": None,  # NSX opaque network
    }
