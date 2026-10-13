from prefect import flow

from zpodcommon import models as M
from zpodcommon.enums import ZpodNetworkRouting
from zpodengine.lib import database
from zpodengine.lib.options import task_options_setup
from zpodengine.zpod_network_routing.zpod_network_routing_2_artifact import (
    zpod_network_routing_artifact,
)
from zpodengine.zpod_network_routing.zpod_network_routing_3_route import (
    zpod_network_routing_route,
)
from zpodengine.zpod_network_routing.zpod_network_routing_4_masquerade import (
    zpod_network_routing_masquerade,
)
from zpodengine.zpod_network_routing.zpod_network_routing_5_finalize import (
    zpod_network_routing_finalize,
)


def flow_failed(flow, flow_run, state):
    from prefect.logging.loggers import flow_run_logger

    logger = flow_run_logger(flow_run, flow)
    logger.info("FAILED")

    # The API set the row to PENDING for this run: put back what it held before,
    # which the API passed as ``previous`` (a dry run may re-check a GLOBAL network).
    routing = ZpodNetworkRouting(flow_run.parameters["previous"])
    with database.get_session_ctx() as session:
        network = session.get(M.ZpodNetwork, flow_run.parameters["network_id"])
        network.routing = routing
        name = network.name
        session.add(network)
        session.commit()
    logger.info(f"Network {name} routing set back to {routing.value}")


@flow(
    name="zpod_network_routing",
    flow_run_name="{verb} {zpod_name}/{network_name} by {requested_by}",
    on_failure=[flow_failed],
    log_prints=True,
)
def flow_zpod_network_routing(
    zpod_id: int,
    network_id: int,
    target: str,
    previous: str,
    requested_by: str,
    zpod_name: str,
    network_name: str,
    verb: str,  # only read by Prefect for the run name template above
    dry_run: bool = False,
):
    """Advertise (target GLOBAL) or withdraw (target LOCAL) a user network.

    ``previous`` is what the row held before the API set it to PENDING: restored on
    a dry run and on any failure. ``verb`` is "advertise" or "withdraw", given by
    the API for the run name.
    """
    target = ZpodNetworkRouting(target)
    if target == ZpodNetworkRouting.PENDING:
        raise ValueError("target must be GLOBAL or LOCAL")
    if ZpodNetworkRouting(previous) == ZpodNetworkRouting.PENDING:
        raise ValueError("previous must be GLOBAL or LOCAL")

    options = task_options_setup(prefix=f"{zpod_name} network {network_name}")

    # One task, under the engine's shared atomic_operation lock: read the fabric,
    # run the guardrails, write the route (skipped on a dry run). Nothing else can
    # change the NSX inventory between the checks and the write.
    route = zpod_network_routing_route.with_options(
        **options(
            name="checks + route" if target == ZpodNetworkRouting.GLOBAL else "route"
        ),
    ).submit(
        zpod_id=zpod_id,
        network_id=network_id,
        target=target,
        requested_by=requested_by,
        dry_run=dry_run,
    )
    futures = [route]

    # The evidence: the check table and the inventories, as a Prefect artifact.
    futures.append(
        zpod_network_routing_artifact.with_options(
            **options(name="artifact"),
        ).submit(
            zpod_id=zpod_id,
            network_id=network_id,
            target=target,
            requested_by=requested_by,
            dry_run=dry_run,
            checks=route,
            wait_for=[futures[-1]],
        )
    )

    if not dry_run and target == ZpodNetworkRouting.GLOBAL:
        # Masquerade goes off only once the route is realized: the last mutation.
        futures.append(
            zpod_network_routing_masquerade.with_options(
                **options(name="masquerade"),
            ).submit(
                zpod_id=zpod_id,
                network_id=network_id,
                wait_for=[futures[-1]],
            )
        )

    futures.append(
        zpod_network_routing_finalize.with_options(
            **options(name="finalize"),
        ).submit(
            network_id=network_id,
            target=target,
            previous=previous,
            dry_run=dry_run,
            wait_for=[futures[-1]],
        )
    )

    # Prefect 3 does not propagate task failures to the flow: resolve every future
    # in order so the FIRST failure (the real cause, not "upstream not ready") fails
    # the flow and fires the on_failure hook.
    for future in futures:
        future.result()


if __name__ == "__main__":
    flow_zpod_network_routing(
        zpod_id=1,
        network_id=5,
        target="GLOBAL",
        previous="LOCAL",
        requested_by="admin",
        zpod_name="demo",
        network_name="LOCALNET111",
        verb="advertise",
        dry_run=True,
    )
