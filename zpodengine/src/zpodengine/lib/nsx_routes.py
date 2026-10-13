"""Tier-1 static routes and the fabric inventories the advertisement checks read.

Every function takes an ``NsxClient`` (``zpodcommon.lib.nsx``) and uses only its
``get``/``patch``/``delete`` and the ``.safejson()``/``.results()`` the client
hooks onto responses, so the tests drive them with a stub.

``base_path`` is the policy API root the zPod's T1 lives under: the global
``/policy/api/v1`` for the ``nsxt`` driver, the project's root for
``nsxt_projects`` (see :func:`policy_base_for`).
"""

import ipaddress
import time

from zpodcommon import models as M
from zpodengine import settings

POLICY_BASE = "/policy/api/v1"
DEFAULT_ROUTE = "0.0.0.0/0"


def tier1_id_for(zpod: M.Zpod) -> str:
    return f"{settings.SITE_ID}-{zpod.name}-tier1"


def policy_base_for(zpod: M.Zpod) -> str:
    """The policy root the zPod's T1 was created under at deploy time."""
    epnet = zpod.endpoint.endpoints["network"]
    if epnet.get("driver") == "nsxt_projects":
        orgid = epnet.get("orgid", "default")
        project_id = f"{settings.SITE_ID}-{zpod.name}-project"
        return f"{POLICY_BASE}/orgs/{orgid}/projects/{project_id}"
    return POLICY_BASE


def _static_route_url(base_path: str, tier1_id: str, route_id: str) -> str:
    return f"{base_path}/infra/tier-1s/{tier1_id}/static-routes/{route_id}"


def static_route_put(
    nsx,
    tier1_id: str,
    route_id: str,
    network: str,
    next_hop_ip: str,
    description: str | None = None,
    base_path: str = POLICY_BASE,
) -> None:
    """Create or update the route (PATCH: repeating it is harmless)."""
    body = {
        "network": network,
        "next_hops": [{"ip_address": next_hop_ip, "admin_distance": 1}],
    }
    if description:
        body["description"] = description
    nsx.patch(url=_static_route_url(base_path, tier1_id, route_id), json=body)


def static_route_get(
    nsx,
    tier1_id: str,
    route_id: str,
    base_path: str = POLICY_BASE,
) -> dict | None:
    """The route as NSX holds it, or None when there is none (404)."""
    data = nsx.get(url=_static_route_url(base_path, tier1_id, route_id)).safejson()
    return data or None


def static_route_delete(
    nsx,
    tier1_id: str,
    route_id: str,
    base_path: str = POLICY_BASE,
) -> None:
    """Delete the route; a route that is already gone is not an error."""
    response = nsx.delete(url=_static_route_url(base_path, tier1_id, route_id))
    if response.status_code == 404:
        return
    response.safejson()


def static_route_wait_realized(
    nsx,
    tier1_id: str,
    route_id: str,
    max_wait: int = 120,
    interval: int = 5,
    base_path: str = POLICY_BASE,
) -> None:
    """Poll the realized state until the route is REALIZED on the edge."""
    intent_path = f"{base_path[len(POLICY_BASE) :]}/infra/tier-1s/{tier1_id}/static-routes/{route_id}"
    url = f"{POLICY_BASE}/infra/realized-state/realized-entities?intent_path={intent_path}"
    print(f"Wait for static route {route_id} on {tier1_id} to realize")
    start = time.monotonic()
    while True:
        entities = nsx.get(url=url).results()
        states = [entity.get("state") for entity in entities]
        if "REALIZED" in states:
            print(f"Static route {route_id} is realized")
            return
        if time.monotonic() - start >= max_wait:
            raise TimeoutError(
                f"Static route {route_id} on {tier1_id} not realized after "
                f"{max_wait}s (states: {states or 'none'})"
            )
        print(f"Static route {route_id} not realized yet (states: {states or 'none'})")
        time.sleep(interval)


def _paginate(nsx, url: str) -> list[dict]:
    """Every result of an NSX list call, following the cursor."""
    results: list[dict] = []
    cursor = None
    while True:
        params = {"cursor": cursor} if cursor else None
        data = nsx.get(url=url, params=params).safejson()
        results.extend(data.get("results", []))
        cursor = data.get("cursor")
        if not cursor:
            return results


def flatten_routing_table(payload: dict) -> list[dict]:
    """Every route of every edge node, the default route dropped, no duplicates."""
    seen = set()
    entries = []
    for result in payload.get("results", []):
        for entry in result.get("route_entries", []):
            network = entry.get("network")
            if not network or network == DEFAULT_ROUTE:
                continue
            key = (network, entry.get("route_type"), entry.get("next_hop"))
            if key in seen:
                continue
            seen.add(key)
            entries.append(
                {
                    "network": network,
                    "route_type": entry.get("route_type"),
                    "next_hop": entry.get("next_hop"),
                    "admin_distance": entry.get("admin_distance"),
                }
            )
    return entries


def tier0_routing_table(nsx, tier0_id: str) -> list[dict]:
    payload = nsx.get(
        url=f"{POLICY_BASE}/infra/tier-0s/{tier0_id}/routing-table"
    ).safejson()
    return flatten_routing_table(payload)


def all_tier1_static_routes(nsx) -> list[dict]:
    """Every static route of every T1 (all zPods of the site)."""
    routes = []
    for tier1 in _paginate(nsx, f"{POLICY_BASE}/infra/tier-1s"):
        tier1_id = tier1["id"]
        for route in _paginate(
            nsx, f"{POLICY_BASE}/infra/tier-1s/{tier1_id}/static-routes"
        ):
            routes.append(
                {
                    "tier1": tier1_id,
                    "route_id": route["id"],
                    "network": route["network"],
                    "next_hops": [
                        hop.get("ip_address") for hop in route.get("next_hops", [])
                    ],
                    "description": route.get("description"),
                }
            )
    return routes


def all_segment_subnets(nsx) -> list[dict]:
    """Every IPv4 subnet of every segment."""
    subnets = []
    for segment in nsx.search(resource_type="Segment"):
        for subnet in segment.get("subnets", []):
            network = subnet.get("network")
            if not network:
                continue
            if not isinstance(
                ipaddress.ip_network(network, strict=False), ipaddress.IPv4Network
            ):
                continue
            subnets.append(
                {
                    "segment": segment.get("display_name", segment.get("id")),
                    "network": network,
                }
            )
    return subnets
