"""What every task of the routing flow needs: the rows and the route facts."""

import ipaddress
from dataclasses import dataclass

from sqlmodel import Session

from zpodcommon import models as M
from zpodcommon.enums import ZpodNetworkKind
from zpodcommon.lib.network_utils import MgmtIp
from zpodengine.lib.nsx_routes import policy_base_for, tier1_id_for

FACTORY_MARK = "via zPodFactory"


def load_zpod_network(
    session: Session, zpod_id: int, network_id: int
) -> tuple[M.Zpod, M.ZpodNetwork]:
    zpod = session.get(M.Zpod, zpod_id)
    if zpod is None:
        raise ValueError(f"zPod {zpod_id} not found")
    network = session.get(M.ZpodNetwork, network_id)
    if network is None or network.zpod_id != zpod.id:
        raise ValueError(f"network {network_id} not found on zPod {zpod.name}")
    if network.kind != ZpodNetworkKind.USER:
        raise ValueError(
            f"network {network.name} of zPod {zpod.name} is a {network.kind} network, "
            "only user networks can change routing"
        )
    return zpod, network


@dataclass
class RouteFacts:
    candidate: ipaddress.IPv4Network
    tier0_id: str
    tier1_id: str
    route_id: str
    base_path: str
    next_hop: str


def route_facts(zpod: M.Zpod, network: M.ZpodNetwork) -> RouteFacts:
    return RouteFacts(
        candidate=ipaddress.ip_network(network.gateway, strict=False),
        tier0_id=zpod.endpoint.endpoints["network"]["t0"],
        tier1_id=tier1_id_for(zpod),
        route_id=f"{zpod.name}-{network.name}",
        base_path=policy_base_for(zpod),
        next_hop=MgmtIp.zpod(zpod, "zcore").ip,
    )
