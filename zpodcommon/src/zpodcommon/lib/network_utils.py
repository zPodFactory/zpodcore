from ipaddress import IPv4Address, IPv4Network

from zpodcommon import models as M
from zpodcommon.enums import ZpodComponentStatus
from zpodcommon.lib.zboxapi import RequestError, ZboxApiClient


class MgmtIp:
    MGMT_HOST_IDS = {
        "gw": 1,
        "zbox": 2,
        "zrdp": 3,
        "hcx-cloud": 7,
        "hcx-connector": 8,
        "nsxv": 9,
        "vcsa": 10,
        "nsx": 20,
        "nsxt": 20,
        "cloudbuilder": 25,
        "vcfinstaller": 25,
        "vrops": 30,
        "vrli": 31,
        "vcd": 40,
        "vcda": 41,
        "vyos": 0,  # vyos(0) will get the subnet's last ip
    }

    def __init__(self, ipv4network: IPv4Network, host_id: int):
        # sourcery skip: remove-unnecessary-cast
        self.ipv4network = ipv4network
        self.ipv4address = ipv4network.network_address + int(host_id)

    @classmethod
    def zpod_component(
        cls,
        zpod_component: M.ZpodComponent,
        host_id: int | None = None,
    ):
        """Load from zpod_component"""
        return cls.zpod(
            zpod=zpod_component.zpod,
            component_name=zpod_component.component.component_name,
            host_id=host_id,
        )

    @classmethod
    def zpod(
        cls,
        zpod: M.Zpod,
        component_name: str | None = None,
        host_id: int | None = None,
    ):
        """Load from zpod"""
        if host_id is None:
            host_id = cls.MGMT_HOST_IDS[component_name]
        ipv4network = IPv4Network(zpod.networks[0].cidr)
        return cls(ipv4network=ipv4network, host_id=host_id)

    @property
    def ip(self):
        return str(self.ipv4address)

    @property
    def netmask(self):
        return str(self.ipv4network.netmask)

    @property
    def prefixlen(self):
        return str(self.ipv4network.prefixlen)

    @property
    def cidr(self):
        return f"{self.ip}/{self.ipv4network.prefixlen}"


def get_zpod_reserved_addresses(zpod: M.Zpod) -> set:
    reserved_ips = set()
    for network in zpod.networks:
        ipv4network = IPv4Network(network.cidr)
        reserved_ips.update(
            {
                ipv4network.network_address,
                ipv4network.network_address + 1,
                ipv4network.broadcast_address,
            }
        )
    return reserved_ips


def get_all_active_addresses(zpod: M.Zpod) -> set:
    zb = ZboxApiClient.by_zpod(zpod)

    # Gather ips from db
    ips = {
        IPv4Address(component.ip)
        for component in zpod.components
        if component.status
        in (ZpodComponentStatus.ACTIVE, ZpodComponentStatus.BUILDING)
    }

    # Gather ips from DNS
    try:
        response = zb.get(url="/dns")
    except RequestError as e:
        print(f"{e.request.url} failure.  Skipping DNS lookup...")
        return ips
    records = response.safejson()
    ips.update({IPv4Address(record["ip"]) for record in records})
    return ips
