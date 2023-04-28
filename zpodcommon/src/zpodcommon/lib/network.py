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


def get_mgmt_ip(instance: M.Instance, network_component: str):
    subnet = IPv4Network(instance.networks[0].cidr)
    ix = {"gw": 0, "zbox": 1, "vyos": -1}[network_component]
    return str(list(subnet.hosts())[ix])


def get_mgmt_cidr(instance: M.Instance, network_component: str):
    subnet = IPv4Network(instance.networks[0].cidr)
    ip = get_mgmt_ip(instance=instance, network_component=network_component)
    return f"{ip}/{subnet.prefixlen}"


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
        f.write(f"address=/{instance_domain}/{instance_dns_ip}\n")


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
