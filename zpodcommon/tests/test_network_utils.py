"""Smoke tests for zpodcommon.lib.network_utils.MgmtIp — pure IP arithmetic."""

from ipaddress import IPv4Network

from zpodcommon.lib.network_utils import MgmtIp


def test_mgmt_ip_arithmetic():
    ip = MgmtIp(ipv4network=IPv4Network("10.0.0.0/24"), host_id=1)
    assert ip.ip == "10.0.0.1"
    assert ip.netmask == "255.255.255.0"
    assert ip.prefixlen == "24"
    assert ip.cidr == "10.0.0.1/24"


def test_mgmt_ip_known_host_ids():
    assert MgmtIp.MGMT_HOST_IDS["gw"] == 1
    assert MgmtIp.MGMT_HOST_IDS["zcore"] == 2
    assert MgmtIp.MGMT_HOST_IDS["vcsa"] == 10
    assert MgmtIp.MGMT_HOST_IDS["nsxt"] == 20
