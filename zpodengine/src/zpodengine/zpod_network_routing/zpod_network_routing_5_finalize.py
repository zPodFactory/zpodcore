from prefect import task

from zpodcommon import models as M
from zpodcommon.enums import ZpodNetworkRouting
from zpodengine.lib import database


@task
def zpod_network_routing_finalize(
    network_id: int, target: str, previous: str, dry_run: bool
) -> None:
    with database.get_session_ctx() as session:
        network = session.get(M.ZpodNetwork, network_id)
        if dry_run:
            # The API set PENDING for the run; nothing changed, put back what was there.
            routing = ZpodNetworkRouting(previous)
            print(f"Dry run: network {network.name} routing stays {routing.value}")
        else:
            routing = ZpodNetworkRouting(target)
            print(f"Network {network.name} routing is now {routing.value}")
        network.routing = routing.value
        session.add(network)
        session.commit()
