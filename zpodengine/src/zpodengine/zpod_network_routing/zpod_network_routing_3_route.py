from datetime import UTC, datetime

from prefect import task

from zpodcommon.enums import ZpodNetworkRouting
from zpodcommon.lib.nsx import NsxClient
from zpodengine.lib import database
from zpodengine.lib.nsx_routes import (
    all_segment_subnets,
    all_tier1_static_routes,
    static_route_delete,
    static_route_get,
    static_route_put,
    static_route_wait_realized,
    tier0_routing_table,
)
from zpodengine.zpod_network_routing.common import (
    FACTORY_MARK,
    RouteFacts,
    load_zpod_network,
    route_facts,
)
from zpodengine.zpod_network_routing.guardrails import run_fabric_checks
from zpodengine.zpod_network_routing.zpod_network_routing_1_checks import (
    check_zcore_vlan,
    fetch_zpod_network_rows,
)


def advertise(nsx, facts: RouteFacts, requested_by: str) -> None:
    existing = static_route_get(
        nsx, facts.tier1_id, facts.route_id, base_path=facts.base_path
    )
    wanted_hops = [facts.next_hop]
    if existing:
        hops = [hop.get("ip_address") for hop in existing.get("next_hops", [])]
        if existing.get("network") == str(facts.candidate) and hops == wanted_hops:
            print(
                f"Static route {facts.route_id} already advertises {facts.candidate}: nothing to do"
            )
        else:
            print(
                f"Static route {facts.route_id} exists with {existing.get('network')} -> {hops}, "
                f"updating to {facts.candidate} -> {wanted_hops}"
            )
    else:
        print(
            f"Create static route {facts.route_id}: {facts.candidate} -> {facts.next_hop}"
        )
    date = datetime.now(UTC).strftime("%Y-%m-%d")
    static_route_put(
        nsx,
        tier1_id=facts.tier1_id,
        route_id=facts.route_id,
        network=str(facts.candidate),
        next_hop_ip=facts.next_hop,
        description=f"advertised by {requested_by} on {date} {FACTORY_MARK}",
        base_path=facts.base_path,
    )
    static_route_wait_realized(
        nsx, facts.tier1_id, facts.route_id, base_path=facts.base_path
    )


def withdraw(nsx, facts: RouteFacts) -> None:
    existing = static_route_get(
        nsx, facts.tier1_id, facts.route_id, base_path=facts.base_path
    )
    if not existing:
        print(
            f"Static route {facts.route_id} is not on {facts.tier1_id}: nothing to do"
        )
        return
    description = existing.get("description") or ""
    if FACTORY_MARK not in description:
        raise ValueError(
            f"Static route {facts.route_id} on {facts.tier1_id} was not created by zPodFactory "
            f"(description {description!r}), refusing to delete it"
        )
    print(
        f"Delete static route {facts.route_id} ({existing.get('network')}) from {facts.tier1_id}"
    )
    static_route_delete(nsx, facts.tier1_id, facts.route_id, base_path=facts.base_path)


@task(tags=["atomic_operation"])
def zpod_network_routing_route(
    zpod_id: int, network_id: int, target: str, requested_by: str, dry_run: bool
) -> dict:
    """Read the fabric, run the guardrails and write the route in ONE task under the
    engine's shared ``atomic_operation`` lock (the one deploy prep, networking deploy
    and destroy already take), so no deploy, destroy or other advertisement can change
    the NSX inventory between the checks and the write. Returns the check results for
    the artifact task; a dry run stops after the checks."""
    with database.get_session_ctx() as session:
        zpod, network = load_zpod_network(session, zpod_id, network_id)
        facts = route_facts(zpod, network)
        if ZpodNetworkRouting(target) == ZpodNetworkRouting.LOCAL:
            print(f"Withdraw {network.name} from the fabric: no advertisement checks")
            if dry_run:
                print("Dry run: the route is left as it is")
                return {}
            with NsxClient.auth_by_endpoint(endpoint=zpod.endpoint) as nsx:
                withdraw(nsx, facts)
            return {}

        print(
            f"Advertise {facts.candidate} (zPod {zpod.name}, network {network.name}, "
            f"vlan {network.vlan_id}) as {facts.route_id} on {facts.tier1_id} -> {facts.next_hop}"
        )
        results = {"zcore_vlan": check_zcore_vlan(zpod, network.vlan_id)}
        db_rows = fetch_zpod_network_rows(session)
        with NsxClient.auth_by_endpoint(endpoint=zpod.endpoint) as nsx:
            # reads and the write share this client, inside the lock
            existing = static_route_get(
                nsx, facts.tier1_id, facts.route_id, base_path=facts.base_path
            )
            self_advertised = bool(existing) and existing.get("network") == str(
                facts.candidate
            )
            if self_advertised:
                print(
                    f"{facts.route_id} already advertises {facts.candidate}: its own "
                    "entry in the T0 routing table is not an overlap"
                )
            tier0_entries = tier0_routing_table(nsx, facts.tier0_id)
            tier1_routes = all_tier1_static_routes(nsx)
            segments = all_segment_subnets(nsx)
            results = run_fabric_checks(
                facts.candidate,
                tier0_id=facts.tier0_id,
                tier0_entries=tier0_entries,
                tier1_routes=tier1_routes,
                self_tier1=facts.tier1_id,
                self_route_id=facts.route_id,
                self_advertised=self_advertised,
                segments=segments,
                db_rows=db_rows,
                self_network_id=network.id,
                results=results,
            )
            if dry_run:
                print("Dry run: every check passed, the route is not written")
                return results
            advertise(nsx, facts, requested_by)
        return results
