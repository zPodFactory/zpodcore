import fcntl
import ipaddress
import os
import random
import socket
import struct
from ipaddress import IPv4Network

from zpodcommon import models as M

#
# Defaults
#


INSTANCE_PUBLIC_NETWORK_PREFIXLEN = 24
INSTANCE_PUBLIC_SUB_NETWORKS_PREFIXLEN = 26
MGMT_LAST_OCTETS = dict(
    gw=1,
    zbox=2,
    vyos=0,  # vyos(0) will get the subnet's last ip
)

#
# Main Network that is validated for route advertisement.
# We defaulted this to a /24 network
#


def get_instance_primary_subnet(endpoint_supernet: str):
    endpoint_network = ipaddress.ip_network(endpoint_supernet)

    return random.choice(
        list(endpoint_network.subnets(new_prefix=INSTANCE_PUBLIC_NETWORK_PREFIXLEN))
    )


#
# All networks from the main network
# This is to provide VLAN support in every Instance for ease of use
# and better UX when simulating on-prem env.
# We defaulted each of them to a /26 network
# This means we will have 4 x /26 usable in the Instance
# The first /26 will be managed by the Native VDS/NSX-T Segment
# The last 3 x /26 will be managed by zbox/vyos through guest VLANs
# Example:
# instance_subnet = 10.96.50.0/24
# provides:
# - 10.96.50.0/26   [VDS/NSX-T on vlan 0(native no taggging)]
# - 10.96.50.64/26  [zbox/vyos on vlan 64]
# - 10.96.50.128/26 [zbox/vyos on vlan 128]
# - 10.96.50.192/26 [zbox/vyos on vlan 192]
#


def get_instance_all_subnets(instance_subnet: IPv4Network):
    return list(
        instance_subnet.subnets(new_prefix=INSTANCE_PUBLIC_SUB_NETWORKS_PREFIXLEN)
    )


def get_instance_component_mgmt_ip(instance_component: M.InstanceComponent):
    """Get assigned ip from instance_component"""
    if instance_component.data.get("last_octet"):
        last_octet = instance_component.data["last_octet"]
    elif (comp_name := instance_component.component.component_name) in MGMT_LAST_OCTETS:
        last_octet = MGMT_LAST_OCTETS[comp_name]
    return get_instance_mgmt_ip(
        instance=instance_component.instance,
        last_octet=last_octet,
    )


def get_instance_mgmt_ip(
    instance: M.Instance,
    component_name: str | None = None,
    last_octet: int | None = None,
):
    """Get requested ip from instance"""
    if last_octet is None:
        last_octet = MGMT_LAST_OCTETS[component_name]
    ipv4network = get_instance_mgmt_ipv4network(instance=instance)
    return get_ip(ipv4network=ipv4network, last_octet=last_octet)


def get_instance_mgmt_cidr(
    instance: M.Instance,
    component_name: str | None = None,
    last_octet: int | None = None,
):
    """Get requested cidr from instance"""
    ipv4network = get_instance_mgmt_ipv4network(instance=instance)
    ip = get_instance_mgmt_ip(
        instance=instance,
        component_name=component_name,
        last_octet=last_octet,
    )
    return f"{ip}/{ipv4network.prefixlen}"


def get_instance_mgmt_ipv4network(instance: M.Instance):
    """Get requested ipv4network from instance"""
    return IPv4Network(instance.networks[0].cidr)


def get_ip(ipv4network: IPv4Network, last_octet: int):
    """Get requested ip from ipv4network"""
    return str(list(ipv4network.hosts())[last_octet - 1])


#
# Create Instance dnsmasq config
# This will be the zbox VM IP by default
# This COULD be the vyos IP (future)
#


def create_dnsmasq_config(
    instance_name: str, instance_domain: str, instance_dns_ip: str
):
    print(f"Creating /etc/dnsmasq.d/{instance_name}.conf")
    with open(f"/etc/dnsmasq.d/{instance_name}.conf", "w") as f:
        f.write(f"server=/{instance_domain}/{instance_dns_ip}\n")


#
# Delete the dns configuration for Instance name
#


def delete_dnsmasq_config(instance_name: str):
    filename = f"/etc/dnsmasq.d/{instance_name}.conf"

    if os.path.exists(filename):
        os.remove(filename)
        print(f"{filename} deleted successfully")
    else:
        print(f"{filename} does not exist")


#
# Fetch Host IP address
# This will be used for sending this ip to Instances/components with:
#  - Shared ISO Read Only Datastore
#  - NTP server for all zPods
#  - xyz new things
#    - (WireGuard Global VPN potentially for DNAT Redirections)
#


def get_host_ip_address(interface_name):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        interface = bytes(interface_name, "utf-8")
        packed_interface = struct.pack("256s", interface[:15])
        info = fcntl.ioctl(sock.fileno(), 0x8915, packed_interface)  # SIOCGIFADDR
        return socket.inet_ntoa(info[20:24])
    except Exception as e:
        print(f"Error fetching IP address for {interface_name}: {e}")
        return None
