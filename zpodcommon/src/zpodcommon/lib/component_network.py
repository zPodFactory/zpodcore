"""The network a component is deployed with: address, gateway, DNS, portgroup.

By default every value comes from the zPod: an address in the mgmt network
(host_id, or the component's fixed id), its gateway, zcore as DNS (the
zPodFactory host for zcore and vyos themselves) and the placement's portgroup.

A nested component can override them with a ``network`` object:

- ``portgroup``: a portgroup of the zPod's vCenter, by name or inventory path.
  It must already exist: zPodFactory never creates one. Its VLAN picks the zPod
  network the address comes from (untagged: mgmt; VLAN N: the zPod network on
  VLAN N), so host_id is the address on the network the portgroup carries.
- ``ip``: an explicit address with its prefix, "192.168.10.20/24", for a subnet
  the portgroup's VLAN can't give (an isolated lab, an NSX segment); the gateway
  comes from the zPod network holding it, or must be given.
- ``gateway``, ``dns``: replace the defaults.

Any component whose library JSON uses ``{{zpod_vlan}}`` (ESXi's guestinfo.vlan)
can be put on a tagged zPod network with ``vlan_id`` instead: the address is
host_id in the zPod network with that VLAN, and the guest tags its interface.
Its portgroup must carry the tag: the zPod segment on the endpoint trunks 0-4094;
a nested component needs ``portgroup`` set to a trunk (it can combine with
``gateway`` and ``dns``, not with ``ip``).

host_id is the last octet in the /24 that holds the network, so the deploy
networks keep the zPod's /24 numbering (vlan64 holds host ids 66 to 126); a
network bigger than a /24 counts it from its own start.
"""

from dataclasses import dataclass
from ipaddress import IPv4Address, IPv4Interface, IPv4Network

from zpodcommon import models as M
from zpodcommon.lib.dbutils import DBUtils
from zpodcommon.lib.network_utils import MgmtIp

NETWORK_FIELDS = ("ip", "gateway", "dns", "portgroup")

# The nested vCenter's only cluster, where nested components are deployed.
NESTED_CLUSTER = "Cluster"
# The portgroup a nested component lands on by default (untagged, the mgmt network).
DEFAULT_NESTED_PORTGROUP = "VM Network"
# resolve_component_network was not given the portgroup's VLAN.
NOT_LOOKED_UP = object()


class ComponentNetworkError(ValueError):
    """The network object can't be resolved for this zPod."""


@dataclass(frozen=True)
class ComponentNetwork:
    ip: str
    prefixlen: int
    gateway: str
    dns: str
    # None: the placement's default ("VM Network" nested, the zPod segment on L1).
    portgroup: str | None = None
    # The VLAN the guest tags its interface with (zpod_vlan); None: untagged.
    vlan_id: int | None = None

    @property
    def netmask(self) -> str:
        return str(IPv4Network(f"0.0.0.0/{self.prefixlen}").netmask)


def clean_network(network: dict | None) -> dict | None:
    """The fields that are set, or None: a stored profile item keeps nulls."""
    cleaned = {k: v for k, v in (network or {}).items() if v not in (None, "")}
    return cleaned or None


def network_static_error(network: dict | None, host_id: int | None) -> str | None:
    """What is wrong with a network object on its own, without its zPod.

    Used for profiles, whose zPod (and its networks) does not exist yet.
    """
    network = clean_network(network)
    if not network:
        return None
    if network.get("ip") and host_id is not None:
        return "network: ip gives the address, host_id can't be set with it"
    parsed = {}
    for field, kind in (
        ("ip", IPv4Interface),
        ("gateway", IPv4Address),
        ("dns", IPv4Address),
    ):
        if value := network.get(field):
            try:
                parsed[field] = kind(value)
            except ValueError:
                return f"network: {field} {value!r} is not an IPv4 address"
    iface, gateway = parsed.get("ip"), parsed.get("gateway")
    if iface:
        if "/" not in network["ip"]:
            return f"network: ip needs its prefix, like {iface.ip}/24"
        if iface.ip in (iface.network.network_address, iface.network.broadcast_address):
            return f"network: {iface.ip} is not a host address of {iface.network}"
        if gateway and gateway not in iface.network:
            return f"network: gateway {gateway} is not in {iface.network}"
        if gateway == iface.ip:
            return f"network: {iface.ip} is the gateway"
    return None


def default_dns(zpod: M.Zpod, component_name: str) -> str:
    # zPodFactory is the main DNS server of every zPod and delegates the zPod's
    # subdomain to zcore/vyos: those two use it, everything else uses zcore.
    if component_name in ("zcore", "vyos"):
        return DBUtils.get_setting_value("zpodfactory_host")
    return MgmtIp.zpod(zpod, "zcore").ip


def _gateway_ip(network_row: M.ZpodNetwork) -> str:
    return network_row.gateway.split("/")[0]


def host_id_range(subnet: IPv4Network, gateway: str) -> tuple[int, int]:
    """The host_ids that give a host address of `subnet`, its gateway left out."""
    base = subnet.supernet(new_prefix=24) if subnet.prefixlen > 24 else subnet
    offset = int(base.network_address)
    first, last = int(subnet.network_address) + 1, int(subnet.broadcast_address) - 1
    gw = int(IPv4Address(gateway))
    first += gw == first
    last -= gw == last
    return first - offset, last - offset


# Every zPod's /24 is split the same way (zpod_deploy): the native mgmt /26 and three
# /26s on these VLANs, so their host_id ranges are known before the zPod exists.
DEPLOY_NETWORKS = {0: "mgmt", 64: "vlan64", 128: "vlan128", 192: "vlan192"}


def deploy_network_host_id_error(
    host_id: int | None, vlan_id: int | None, network: dict | None
) -> str | None:
    """A host_id outside the deploy network it targets, checked without the zPod.

    For profiles: the address of an item on mgmt, vlan64, vlan128 or vlan192 can be
    checked when the profile is saved. A portgroup's VLAN, and user networks, are
    only known at deploy.
    """
    network = clean_network(network) or {}
    if host_id is None or network.get("ip"):
        return None
    if vlan_id is not None:
        base = vlan_id if vlan_id in DEPLOY_NETWORKS else None
    elif network.get("portgroup", DEFAULT_NESTED_PORTGROUP) == DEFAULT_NESTED_PORTGROUP:
        base = 0
    else:
        base = None
    if base is None:
        return None
    subnet = IPv4Network(f"10.0.0.{base}/26")
    lo, hi = host_id_range(subnet, str(subnet.network_address + 1))
    if lo <= host_id <= hi:
        return None
    where = (
        "the mgmt network" if base == 0 else f"{DEPLOY_NETWORKS[base]} (VLAN {base})"
    )
    return f"host_id {host_id} is outside {where}, which takes host_id {lo} to {hi}"


def host_address(cidr: str, host_id: int) -> IPv4Address:
    """host_id as the last octet in the /24 holding `cidr` (its own start if larger)."""
    subnet = IPv4Network(cidr)
    base = subnet.supernet(new_prefix=24) if subnet.prefixlen > 24 else subnet
    return base.network_address + int(host_id)


# --- the portgroup, in the zPod's own vCenter ------------------------------------


def select_portgroup(vc, portgroup: str, where: str) -> dict:
    """The one network `portgroup` designates in that vCenter (see
    vCenter.list_networks), present on every host of the cluster when it is a
    standard vSwitch portgroup. Never created: it must already exist."""
    matches = vc.find_networks(portgroup)
    if not matches:
        available = ", ".join(sorted({n["name"] for n in vc.list_networks()}))
        raise ComponentNetworkError(
            f"portgroup {portgroup!r} not found in {where}; available: {available}"
        )
    if len(matches) > 1:
        found = ", ".join(
            sorted(
                f"{n['path']} ({'standard' if n['standard'] else 'distributed'})"
                for n in matches
            )
        )
        # A distributed portgroup has a unique /<dc>/network/<vds>/<name> path;
        # a standard one only has /<dc>/network/<name>, shared by its namesakes.
        hint = "Use the distributed portgroup's path"
        if any(n["standard"] for n in matches):
            hint += (
                "; a standard portgroup can't be told apart from a network "
                "with the same name: rename one of them"
            )
        raise ComponentNetworkError(
            f"portgroup {portgroup!r} matches several networks in {where}: "
            f"{found}. {hint}."
        )
    (match,) = matches
    if match["standard"]:
        cluster_hosts = set(vc.get_cluster_host_names(NESTED_CLUSTER))
        missing = sorted(cluster_hosts - set(match["hosts"]))
        if missing:
            raise ComponentNetworkError(
                f"portgroup {portgroup!r} is a standard vSwitch portgroup "
                f"present on {', '.join(sorted(match['hosts']))} only; "
                f"missing on {', '.join(missing)}"
            )
    return match


def nested_portgroup(zpod: M.Zpod, portgroup: str) -> dict:
    """select_portgroup in the zPod's own vCenter."""
    from zpodcommon.lib.vmware import vCenter

    where = f"vcsa.{zpod.domain}"
    try:
        with vCenter.auth_by_zpod(zpod=zpod) as vc:
            return select_portgroup(vc, portgroup, where)
    except ComponentNetworkError:
        raise
    except Exception as e:
        raise ComponentNetworkError(
            f"portgroup {portgroup!r}: can't read the zPod's vCenter ({where}): {e}"
        ) from e


def needs_portgroup_vlan(
    network: dict | None, vlan_id: int | None, isnested: bool
) -> bool:
    """Whether the address depends on the portgroup's VLAN, read in the vCenter."""
    network = clean_network(network) or {}
    return bool(
        isnested
        and network.get("portgroup")
        and not network.get("ip")
        and vlan_id is None
    )


# --- resolution -----------------------------------------------------------------


def resolve_component_network(
    zpod: M.Zpod,
    component_name: str,
    *,
    network: dict | None = None,
    host_id: int | None = None,
    ip: str | None = None,
    vlan_id: int | None = None,
    portgroup_vlan=NOT_LOOKED_UP,
) -> ComponentNetwork:
    """The component's network: the overrides in `network`, else the defaults.

    `ip` is the address already chosen (the component row's), so a later call
    gives the same answer as the one that picked it. `portgroup_vlan` is the VLAN
    of network.portgroup (vCenter.portgroup_vlan), required when the address
    comes from it (needs_portgroup_vlan).
    """
    network = clean_network(network) or {}
    if vlan_id is not None and network.get("ip"):
        raise ComponentNetworkError("vlan_id gives the address: set it, or network.ip")
    # With `ip` given, the request was already checked when that address was picked.
    if ip is None and (error := network_static_error(network, host_id)):
        raise ComponentNetworkError(error)

    portgroup = network.get("portgroup")
    if network.get("ip"):
        iface = IPv4Interface(network["ip"])
        subnet, address = iface.network, iface.ip
        row = next((n for n in zpod.networks if address in IPv4Network(n.cidr)), None)
        gateway = network.get("gateway") or (row and _gateway_ip(row))
        where = None  # an explicit address: no host_id to suggest
        if not gateway:
            raise ComponentNetworkError(
                f"network: gateway is required, {address} is not in a zPod network"
            )
    elif vlan_id is not None:
        row = _row_on_vlan(zpod, vlan_id, f"vlan_id: zPod {zpod.name}")
        if ip is None and host_id is None:
            raise ComponentNetworkError("vlan_id needs host_id, the address on it")
        subnet = IPv4Network(row.cidr)
        address = IPv4Address(ip) if ip else host_address(row.cidr, host_id)
        gateway = network.get("gateway") or _gateway_ip(row)
        where = f"VLAN {vlan_id}"
    elif ip is not None:
        # Resolved again from the stored address: the zPod network holding it.
        address = IPv4Address(ip)
        row = next(
            (n for n in zpod.networks if address in IPv4Network(n.cidr)),
            zpod.mgmt_network,
        )
        subnet = IPv4Network(row.cidr)
        gateway = network.get("gateway") or _gateway_ip(row)
        where = None
    elif portgroup and portgroup_vlan is not NOT_LOOKED_UP and portgroup_vlan != 0:
        if portgroup_vlan == "trunk":
            raise ComponentNetworkError(
                f"portgroup {portgroup!r} is a trunk: give vlan_id (a guest that "
                "tags its frames) or network.ip"
            )
        if portgroup_vlan is None:
            raise ComponentNetworkError(
                f"portgroup {portgroup!r} has no VLAN to pick a zPod network from "
                "(an NSX segment?): give network.ip and network.gateway"
            )
        row = _row_on_vlan(
            zpod,
            portgroup_vlan,
            f"portgroup {portgroup!r} is on VLAN {portgroup_vlan}, and zPod {zpod.name}",
            hint="add it with zcli zpod network add, or give network.ip and "
            "network.gateway",
        )
        component_id = MgmtIp.MGMT_HOST_IDS.get(component_name)
        if host_id is None and component_id is None:
            raise ComponentNetworkError(
                f"portgroup {portgroup!r}: host_id is needed, the address on VLAN "
                f"{portgroup_vlan}"
            )
        subnet = IPv4Network(row.cidr)
        address = host_address(
            row.cidr, host_id if host_id is not None else component_id
        )
        gateway = network.get("gateway") or _gateway_ip(row)
        where = f"portgroup {portgroup} (VLAN {portgroup_vlan})"
    else:
        if portgroup and portgroup_vlan is NOT_LOOKED_UP:
            raise ComponentNetworkError(
                f"portgroup {portgroup!r}: its VLAN must be read first"
            )
        # The mgmt network: no portgroup, or an untagged one.
        subnet = IPv4Network(zpod.mgmt_network.cidr)
        address = MgmtIp.zpod(
            zpod, component_name=component_name, host_id=host_id
        ).ipv4address
        gateway = network.get("gateway") or MgmtIp.zpod(zpod, "gw").ip
        where = "the mgmt network"

    bad_host = address not in subnet or address in (
        subnet.network_address,
        subnet.broadcast_address,
    )
    if bad_host or str(address) == gateway:
        problem = (
            f"{address} is not a host address of {subnet}"
            if bad_host
            else f"{address} is the gateway"
        )
        # The address came from a host_id: say which ones fit.
        if where and IPv4Address(gateway) in subnet:
            lo, hi = host_id_range(subnet, gateway)
            problem += f"; {where} takes host_id {lo} to {hi}"
        raise ComponentNetworkError(f"network: {problem}")
    if IPv4Address(gateway) not in subnet:
        raise ComponentNetworkError(f"network: gateway {gateway} is not in {subnet}")

    return ComponentNetwork(
        ip=str(address),
        prefixlen=subnet.prefixlen,
        gateway=gateway,
        dns=network.get("dns") or default_dns(zpod, component_name),
        portgroup=portgroup or None,
        vlan_id=vlan_id,
    )


def _row_on_vlan(zpod: M.Zpod, vlan: int, subject: str, hint: str = ""):
    row = next((n for n in zpod.networks if n.vlan_id == vlan), None)
    if row is None or vlan == 0:
        vlans = ", ".join(str(n.vlan_id) for n in zpod.networks if n.vlan_id)
        raise ComponentNetworkError(
            f"{subject} has no network on VLAN {vlan} (it has: {vlans})"
            + (f"; {hint}" if hint else "")
        )
    return row


def resolve_new_component_network(
    zpod: M.Zpod,
    component: M.Component,
    *,
    network: dict | None = None,
    host_id: int | None = None,
    vlan_id: int | None = None,
    nested: bool | None = None,
) -> ComponentNetwork:
    """resolve_component_network for a component about to be added: reads the
    portgroup's VLAN in the zPod's vCenter when the address comes from it."""
    from zpodcommon.lib.component_placement import component_isnested

    portgroup_vlan = NOT_LOOKED_UP
    # The library JSON is only read when the address could come from a portgroup.
    if needs_portgroup_vlan(network, vlan_id, True) and (
        nested
        if nested is not None
        else component_isnested(component.component_json, None)
    ):
        portgroup_vlan = nested_portgroup(zpod, network["portgroup"])["vlan"]
    return resolve_component_network(
        zpod,
        component.component_name,
        network=network,
        host_id=host_id,
        vlan_id=vlan_id,
        portgroup_vlan=portgroup_vlan,
    )
