import re
from types import SimpleNamespace

import pytest

from zpodcommon.lib import component_network as cn
from zpodcommon.lib.component_network import (
    ComponentNetworkError,
    network_static_error,
    resolve_component_network,
)


def row(name, cidr, gateway, vlan_id=0, kind="zpod"):
    return SimpleNamespace(
        name=name, cidr=cidr, gateway=gateway, vlan_id=vlan_id, kind=kind
    )


@pytest.fixture
def zpod(monkeypatch):
    monkeypatch.setattr(
        cn.DBUtils,
        "get_setting_value",
        classmethod(lambda cls, name: {"zpodfactory_host": "10.0.0.1"}.get(name)),
    )
    mgmt = row("mgmt", "10.96.1.0/26", "10.96.1.1/26")
    return SimpleNamespace(
        name="demo",
        networks=[
            mgmt,
            row("vlan64", "10.96.1.64/26", "10.96.1.65/26", 64),
            row("LOCALNET111", "10.42.111.0/24", "10.42.111.1/24", 111, "user"),
        ],
        mgmt_network=mgmt,
    )


def test_defaults_are_todays_values(zpod):
    net = resolve_component_network(zpod, "vrops")
    assert net == cn.ComponentNetwork("10.96.1.30", 26, "10.96.1.1", "10.96.1.2")
    assert net.netmask == "255.255.255.192"
    assert resolve_component_network(zpod, "esxi", host_id=11).ip == "10.96.1.11"
    # zcore and vyos use the zPodFactory host as DNS.
    assert resolve_component_network(zpod, "zcore").dns == "10.0.0.1"


def test_explicit_ip_in_a_zpod_network_takes_its_gateway(zpod):
    net = resolve_component_network(
        zpod, "ubuntu", network={"ip": "10.42.111.20/24", "portgroup": "VM Network"}
    )
    assert (net.ip, net.prefixlen, net.gateway, net.dns, net.portgroup) == (
        "10.42.111.20",
        24,
        "10.42.111.1",
        "10.96.1.2",
        "VM Network",
    )


def test_explicit_ip_outside_the_zpod_needs_a_gateway(zpod):
    with pytest.raises(ComponentNetworkError, match="gateway is required"):
        resolve_component_network(zpod, "ubuntu", network={"ip": "192.168.10.20/24"})
    net = resolve_component_network(
        zpod,
        "ubuntu",
        network={"ip": "192.168.10.20/24", "gateway": "192.168.10.1", "dns": "1.1.1.1"},
    )
    assert (net.gateway, net.dns) == ("192.168.10.1", "1.1.1.1")


def test_portgroup_vlan_picks_the_zpod_network(zpod):
    # host_id is the last octet in the zPod's /24: vlan64 holds 66-126.
    net = resolve_component_network(
        zpod, "ubuntu", network={"portgroup": "PG64"}, host_id=74, portgroup_vlan=64
    )
    assert (net.ip, net.prefixlen, net.gateway, net.portgroup) == (
        "10.96.1.74",
        26,
        "10.96.1.65",
        "PG64",
    )
    # A /24 user network on VLAN 111 counts from its own start.
    assert (
        resolve_component_network(
            zpod,
            "ubuntu",
            network={"portgroup": "PG111"},
            host_id=20,
            portgroup_vlan=111,
        ).ip
        == "10.42.111.20"
    )
    # Untagged (VM Network): the mgmt network.
    assert (
        resolve_component_network(
            zpod,
            "ubuntu",
            network={"portgroup": "VM Network"},
            host_id=20,
            portgroup_vlan=0,
        ).ip
        == "10.96.1.20"
    )
    # A component with a fixed id needs no host_id.
    assert (
        resolve_component_network(
            zpod, "vrops", network={"portgroup": "PG111"}, portgroup_vlan=111
        ).ip
        == "10.42.111.30"
    )


@pytest.mark.parametrize(
    "kwargs, message",
    [
        (
            {"host_id": 10, "portgroup_vlan": 64},
            "portgroup PG (VLAN 64) takes host_id 66 to 126",
        ),
        (
            {"host_id": 20, "portgroup_vlan": 300},
            "is on VLAN 300, and zPod demo has no network on VLAN 300",
        ),
        ({"host_id": 20, "portgroup_vlan": "trunk"}, "is a trunk: give vlan_id"),
        (
            {"host_id": 20, "portgroup_vlan": None},
            "has no VLAN to pick a zPod network from",
        ),
        ({"host_id": 20}, "its VLAN must be read first"),
    ],
)
def test_portgroup_vlan_errors(zpod, kwargs, message):
    with pytest.raises(ComponentNetworkError, match=re.escape(message)):
        resolve_component_network(zpod, "ubuntu", network={"portgroup": "PG"}, **kwargs)
    if kwargs.get("portgroup_vlan") == 300:
        with pytest.raises(ComponentNetworkError, match="zcli zpod network add"):
            resolve_component_network(
                zpod, "ubuntu", network={"portgroup": "PG"}, **kwargs
            )


def test_the_chosen_ip_resolves_the_same_later(zpod):
    # ovf_deployer passes the component row's ip, without host_id or the VLAN.
    first = resolve_component_network(
        zpod, "ubuntu", network={"portgroup": "PG111"}, host_id=20, portgroup_vlan=111
    )
    again = resolve_component_network(
        zpod, "ubuntu", network={"portgroup": "PG111"}, ip=first.ip
    )
    assert again == first
    assert resolve_component_network(
        zpod, "ubuntu", network={"portgroup": "pg"}, ip="10.96.1.40"
    ) == cn.ComponentNetwork("10.96.1.40", 26, "10.96.1.1", "10.96.1.2", "pg")


def test_nulls_from_a_stored_profile_are_ignored(zpod):
    stored = {"ip": None, "portgroup": None, "gateway": None, "dns": None}
    assert resolve_component_network(zpod, "vrops", network=stored).ip == "10.96.1.30"
    assert network_static_error(stored, None) is None


@pytest.mark.parametrize(
    "network, host_id, error",
    [
        ({"ip": "10.42.111.20/24"}, 20, "host_id can't be set"),
        ({"ip": "10.42.111.20"}, None, "needs its prefix"),
        ({"ip": "10.42.111.0/24"}, None, "not a host address"),
        ({"ip": "10.42.111.20/24", "gateway": "10.0.0.1"}, None, "not in"),
        ({"ip": "10.42.111.1/24", "gateway": "10.42.111.1"}, None, "is the gateway"),
        ({"dns": "zcore"}, None, "dns 'zcore' is not an IPv4 address"),
        ({"ip": "10.42.111.300/24"}, None, "ip '10.42.111.300/24' is not an IPv4"),
    ],
)
def test_static_errors(network, host_id, error):
    assert error in network_static_error(network, host_id)


def test_vlan_id(zpod):
    net = resolve_component_network(zpod, "esxi", host_id=71, vlan_id=64)
    assert net == cn.ComponentNetwork(
        "10.96.1.71", 26, "10.96.1.65", "10.96.1.2", None, 64
    )
    assert net.netmask == "255.255.255.192"
    # The user network on VLAN 111, a /24: host_id counts from its start.
    assert resolve_component_network(zpod, "esxi", host_id=20, vlan_id=111).ip == (
        "10.42.111.20"
    )
    # Resolved again later from the stored address.
    assert resolve_component_network(zpod, "esxi", ip="10.96.1.71", vlan_id=64) == net


def test_vlan_id_errors(zpod):
    with pytest.raises(
        ComponentNetworkError, match=r"no network on VLAN 65 \(it has: 64, 111\)"
    ):
        resolve_component_network(zpod, "esxi", host_id=71, vlan_id=65)
    with pytest.raises(ComponentNetworkError, match="10.96.1.11 is not a host address"):
        resolve_component_network(zpod, "esxi", host_id=11, vlan_id=64)
    with pytest.raises(ComponentNetworkError, match="needs host_id"):
        resolve_component_network(zpod, "esxi", vlan_id=64)
    with pytest.raises(ComponentNetworkError, match="vlan_id gives the address"):
        resolve_component_network(
            zpod, "esxi", host_id=71, vlan_id=64, network={"ip": "10.96.1.71/26"}
        )
    # portgroup, gateway and dns combine with it: a nested trunk portgroup.
    net = resolve_component_network(
        zpod,
        "zbox",
        host_id=71,
        vlan_id=64,
        network={"portgroup": "TRUNK", "dns": "1.1.1.1"},
    )
    assert (net.ip, net.gateway, net.dns, net.portgroup, net.vlan_id) == (
        "10.96.1.71",
        "10.96.1.65",
        "1.1.1.1",
        "TRUNK",
        64,
    )


@pytest.mark.parametrize(
    "kwargs, message",
    [
        (
            {"host_id": 60, "vlan_id": 64},
            "10.96.1.60 is not a host address of 10.96.1.64/26; "
            "VLAN 64 takes host_id 66 to 126",
        ),
        (
            {"host_id": 65, "vlan_id": 64},
            "10.96.1.65 is the gateway; VLAN 64 takes host_id 66 to 126",
        ),
        ({"host_id": 70}, "the mgmt network takes host_id 2 to 62"),
        (
            {"host_id": 300, "network": {"portgroup": "PG111"}, "portgroup_vlan": 111},
            "portgroup PG111 (VLAN 111) takes host_id 2 to 254",
        ),
    ],
)
def test_host_id_errors_name_the_range(zpod, kwargs, message):
    with pytest.raises(ComponentNetworkError, match=re.escape(message)):
        resolve_component_network(zpod, "esxi", **kwargs)


def test_explicit_ip_errors_name_no_range(zpod):
    with pytest.raises(ComponentNetworkError) as e:
        resolve_component_network(
            zpod, "ubuntu", network={"ip": "10.42.111.1/24", "gateway": "10.42.111.1"}
        )
    assert "takes host_id" not in str(e.value)


@pytest.mark.parametrize(
    "host_id, vlan_id, network, error",
    [
        (11, None, None, None),
        (71, None, None, "outside the mgmt network, which takes host_id 2 to 62"),
        (71, 64, None, None),
        (60, 64, None, "outside vlan64 (VLAN 64), which takes host_id 66 to 126"),
        (193, 192, None, "outside vlan192 (VLAN 192), which takes host_id 194 to 254"),
        (71, None, {"portgroup": "VM Network"}, "outside the mgmt network"),
        (71, None, {"portgroup": "PG64"}, None),  # its VLAN is read at deploy
        (20, 180, None, None),  # a user VLAN: checked at deploy
        (None, 64, None, None),
        (5, None, {"ip": "192.168.50.5/24"}, None),
    ],
)
def test_deploy_network_host_id_error(host_id, vlan_id, network, error):
    result = cn.deploy_network_host_id_error(host_id, vlan_id, network)
    assert result == error or (error and error in result)
