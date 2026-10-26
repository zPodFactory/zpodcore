from prefect import task

from zpodcommon.lib.zboxapi import ZboxApiClient
from zpodengine.lib import database
from zpodengine.zpod_network_routing.common import load_zpod_network


@task
def zpod_network_routing_masquerade(zpod_id: int, network_id: int) -> None:
    """A network is either masqueraded or advertised, never both: once the route
    is on the fabric, drop the source translation on zcore. Last mutating step on
    purpose: a failure here leaves a reachable network, not an unreachable one."""
    with database.get_session_ctx() as session:
        zpod, network = load_zpod_network(session, zpod_id, network_id)
        if not network.masquerade:
            print(
                f"Network {network.name} (vlan {network.vlan_id}) is not masqueraded: nothing to do"
            )
            return
        print(f"Disable masquerade for vlan {network.vlan_id} on zcore.{zpod.domain}")
        with ZboxApiClient.by_zpod(zpod) as zb:
            view = zb.put(
                url=f"/vlan/{network.vlan_id}/masquerade", json={"enabled": False}
            ).safejson()
        print(f"zboxapi: {view}")
        network.masquerade = False
        session.add(network)
        session.commit()
        print(f"Network {network.name}: masquerade off")
