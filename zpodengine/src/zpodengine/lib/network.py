import fcntl
import ipaddress
import random
import socket
import struct
import time
from datetime import datetime
from ipaddress import ip_network, IPv4Network

from zpodcommon.lib.nsx import NsxClient

#
# Defaults
#
ZPOD_PUBLIC_NETWORK_PREFIXLEN = 24
ZPOD_PUBLIC_SUB_NETWORKS_PREFIXLEN = 26


#
# Main Network that is validated for route advertisement.
# We defaulted this to a /24 network
#


def get_zpod_primary_subnet(endpoint: str):
    endpoint_network = ipaddress.ip_network(endpoint.endpoints["network"]["networks"])
    with NsxClient(endpoint=endpoint) as nsx:
        segments = nsx.search(resource_type="Segment")

        # Get all in use IPv4 subnets only
        in_use_subnets = [
            IPv4Network(subnet["network"])
            for segment in segments
            for subnet in segment.get("subnets", [])
            if subnet.get("network") and isinstance(ip_network(subnet["network"], strict=False), IPv4Network)
        ]

        # Get all possible subnets
        possible_subnets = list(
            endpoint_network.subnets(new_prefix=ZPOD_PUBLIC_NETWORK_PREFIXLEN)
        )

        # Randomize possible subnet list
        random.shuffle(possible_subnets)

        # Walk through possible subnets until an unused one is found
        for subnet in possible_subnets:
            # If subnet is not in use anywhere, return subnet
            if all(not subnet.overlaps(x) for x in in_use_subnets):
                return subnet

    raise ValueError("No networks available")


#
# All networks from the main network
# This is to provide VLAN support in every zPod for ease of use
# and better UX when simulating on-prem env.
# We defaulted each of them to a /26 network
# This means we will have 4 x /26 usable in the zPod
# The first /26 will be managed by the Native VDS/NSX-T Segment
# The last 3 x /26 will be managed by zbox/vyos through guest VLANs
# Example:
# zpod_subnet = 10.96.50.0/24
# provides:
# - 10.96.50.0/26   [VDS/NSX-T on native vlan (no tagging)]
# - 10.96.50.64/26  [zbox/vyos on vlan 64]
# - 10.96.50.128/26 [zbox/vyos on vlan 128]
# - 10.96.50.192/26 [zbox/vyos on vlan 192]
#


def get_zpod_all_subnets(zpod_subnet: IPv4Network):
    return list(zpod_subnet.subnets(new_prefix=ZPOD_PUBLIC_SUB_NETWORKS_PREFIXLEN))


#
# Fetch Host IP address
# This will be used for sending this ip to zpods/components with:
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


def wait_for_segment_to_be_evacuted(
    nsx,
    segment,
    SEGMENT_MAX_WAIT_FOR_EMPTY=120,
    SEGMENT_WAIT_BETWEEN_TRIES=5,
):
    """Waits for the segment to have no ports/interfaces"""

    path = f"/policy/api/v1{segment['path']}/ports"

    start = datetime.now()
    while (datetime.now() - start).seconds < SEGMENT_MAX_WAIT_FOR_EMPTY:
        ports = nsx.get(path).safejson()
        if ports["result_count"] == 0:
            print(
                f"Segment ({segment['display_name']}) has no ports / "
                "interfaces attached. Continuing."
            )
            break
        print(
            f"Segment ({segment['display_name']}) has ports / "
            "interfaces attached. Waiting..."
        )
        time.sleep(SEGMENT_WAIT_BETWEEN_TRIES)
    else:
        raise ValueError("Failed: Segment has connected ports / interfaces.")


def wait_for_segment_to_realize(
    nsx: NsxClient,
    path: str,
    segment_id: str,
    SEGMENT_MAX_WAIT_FOR_REALIZED=120,
    SEGMENT_WAIT_BETWEEN_TRIES=5,
):
    # Wait for segment to realize
    print("Wait for segment to realize")
    start = datetime.now()
    while (datetime.now() - start).seconds < SEGMENT_MAX_WAIT_FOR_REALIZED:
        if results := nsx.get(path).results():
            rls = next(
                x for x in results if x["entity_type"] == "RealizedLogicalSwitch"
            )
            if (
                rls.get("state") == "REALIZED"
                and rls.get("runtime_status") == "SUCCESS"
                and rls.get("publish_status") == "SUCCESS"
                and rls.get("operational_status") == "STATUS_GREEN"
            ):
                print(f"Segment ({segment_id}) is ready for use")
                break
            print(
                f"Segment ({segment_id}) is not ready. "
                f"State:{rls.get('state', 'N/a')}, "
                f"Runtime Status:{rls.get('runtime_status', 'N/a')}, "
                f"Publish Status:{rls.get('publish_status', 'N/a')}, "
                f"Operational Status:{rls.get('operational_status', 'N/a')}"
            )
        else:
            print("Status not readable.  Trying again...")
        time.sleep(SEGMENT_WAIT_BETWEEN_TRIES)
    else:
        raise ValueError("Failed: Segment is not realized.")
