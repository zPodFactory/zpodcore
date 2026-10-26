"""The checks a user network passes before its subnet is advertised to the fabric.

Pure functions over plain lists: the task gathers the inventories (NSX, the
database, the settings) and this module compares. Each check prints its
inventory with a count, then the candidate, then the verdict; a failure names
the colliding entry and where it comes from. ``run_fabric_checks`` stops at the
first failure and raises ``ValueError`` with that verdict.
"""

import ipaddress
from dataclasses import asdict, dataclass, field

from zpodcommon.enums import ZpodStatus

# Same bounds as the API accepts at add time; the overlap checks above are the
# real guard, this one only keeps nonsense (multicast, /32, 0.0.0.0/8) out.
MIN_PREFIXLEN = 8
MAX_PREFIXLEN = 30


@dataclass
class CheckResult:
    name: str
    ok: bool
    count: int
    detail: str
    inventory: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)


def _ipv4(value) -> ipaddress.IPv4Network | None:
    try:
        network = ipaddress.ip_network(str(value), strict=False)
    except ValueError:
        return None
    return network if isinstance(network, ipaddress.IPv4Network) else None


def _report(candidate: ipaddress.IPv4Network, result: CheckResult, title: str) -> None:
    print(f"[{result.name}] {title}: {result.count} entries")
    for line in result.inventory:
        print(f"[{result.name}]   {line}")
    print(f"[{result.name}] candidate: {candidate}")
    print(f"[{result.name}] {'ok' if result.ok else result.detail}")


def _overlap_check(
    name: str,
    title: str,
    candidate: ipaddress.IPv4Network,
    entries: list[dict],
    describe,
    origin,
    cidr_of=lambda entry: entry.get("network"),
) -> CheckResult:
    """Generic overlap check: ``cidr_of(entry)`` is the entry's subnet,
    ``describe(entry)`` its inventory line and ``origin(entry)`` names where a
    colliding entry comes from."""
    inventory = [describe(entry) for entry in entries]
    result = CheckResult(
        name=name, ok=True, count=len(entries), detail="ok", inventory=inventory
    )
    for entry in entries:
        network = _ipv4(cidr_of(entry))
        if network is not None and candidate.overlaps(network):
            result.ok = False
            result.detail = f"FAIL: {candidate} overlaps {network} from {origin(entry)}"
            break
    _report(candidate, result, title)
    return result


def check_tier0_routes(
    candidate: ipaddress.IPv4Network,
    entries: list[dict],
    tier0_id: str,
    self_advertised: bool = False,
) -> CheckResult:
    """No overlap with anything the T0 already routes (the default route aside).

    ``self_advertised``: this network's own T1 static route already carries exactly
    the candidate (a re-run, or a dry run on a GLOBAL network), so the T0 entry it
    produces (route_type t1s, the same prefix) is ours, not an overlap. Any other
    T1 advertising it is still caught by the T1 static routes check."""
    if self_advertised:
        entries = [
            e
            for e in entries
            if not (
                e.get("route_type") == "t1s" and _ipv4(e.get("network")) == candidate
            )
        ]
    return _overlap_check(
        "tier0_routing_table",
        f"routing table of T0 {tier0_id}",
        candidate,
        entries,
        describe=lambda e: (
            f"{e['network']} type={e.get('route_type')} next_hop={e.get('next_hop')}"
        ),
        origin=lambda e: (
            f"the routing table of T0 {tier0_id} "
            f"(route_type {e.get('route_type')}, next hop {e.get('next_hop')})"
        ),
    )


def check_tier1_static_routes(
    candidate: ipaddress.IPv4Network,
    routes: list[dict],
    self_tier1: str,
    self_route_id: str,
) -> CheckResult:
    """No overlap with any T1 static route of the site, except this network's own
    route, which already exists when the advertisement is run again."""
    others = [
        route
        for route in routes
        if not (route["tier1"] == self_tier1 and route["route_id"] == self_route_id)
    ]
    return _overlap_check(
        "tier1_static_routes",
        "T1 static routes (every zPod)",
        candidate,
        others,
        describe=lambda r: (
            f"{r['network']} tier1={r['tier1']} route={r['route_id']} "
            f"next_hops={','.join(r.get('next_hops') or [])}"
        ),
        origin=lambda r: (
            f"static route {r['route_id']} on T1 {r['tier1']}"
            + (f" ({r['description']})" if r.get("description") else "")
        ),
    )


def check_segment_subnets(
    candidate: ipaddress.IPv4Network,
    segments: list[dict],
) -> CheckResult:
    """No overlap with any NSX segment subnet."""
    return _overlap_check(
        "segment_subnets",
        "segment subnets",
        candidate,
        segments,
        describe=lambda s: f"{s['network']} segment={s['segment']}",
        origin=lambda s: f"segment {s['segment']}",
    )


def check_db_networks(
    candidate: ipaddress.IPv4Network,
    rows: list[dict],
    self_network_id: int,
) -> CheckResult:
    """No overlap with any network of any live zPod in the database.

    ``rows`` are ``{"zpod", "zpod_status", "network", "network_id", "cidr"}``;
    deleted zPods (their rows outlive them) and this very network are skipped.
    """
    live = [
        row
        for row in rows
        if row["zpod_status"] != ZpodStatus.DELETED
        and row["network_id"] != self_network_id
    ]
    return _overlap_check(
        "database_networks",
        "zPod networks in the database (live zPods)",
        candidate,
        live,
        describe=lambda r: f"{r['cidr']} zpod={r['zpod']} network={r['network']}",
        origin=lambda r: f"network {r['network']} of zPod {r['zpod']} (database)",
        cidr_of=lambda r: r["cidr"],
    )


def check_prefix_length(candidate: ipaddress.IPv4Network) -> CheckResult:
    """A routable unicast prefix between /8 and /30."""
    detail = "ok"
    if candidate.prefixlen < MIN_PREFIXLEN:
        detail = (
            f"FAIL: {candidate} is a /{candidate.prefixlen}, larger than the "
            f"/{MIN_PREFIXLEN} allowed"
        )
    elif candidate.prefixlen > MAX_PREFIXLEN:
        detail = f"FAIL: {candidate} is a /{candidate.prefixlen}, smaller than the /{MAX_PREFIXLEN} allowed"
    elif candidate.is_multicast:
        detail = f"FAIL: {candidate} is a multicast range"
    elif candidate.is_loopback:
        detail = f"FAIL: {candidate} is the loopback range"
    elif candidate.is_link_local:
        detail = f"FAIL: {candidate} is the link-local range"
    elif candidate.is_unspecified or candidate.network_address == ipaddress.IPv4Address(
        "0.0.0.0"
    ):
        detail = f"FAIL: {candidate} is the unspecified range"
    result = CheckResult(
        name="prefix_length",
        ok=detail == "ok",
        count=1,
        detail=detail,
        inventory=[f"allowed: /{MIN_PREFIXLEN} to /{MAX_PREFIXLEN}, unicast only"],
    )
    _report(candidate, result, "prefix length")
    return result


def run_fabric_checks(
    candidate: ipaddress.IPv4Network,
    *,
    tier0_id: str,
    tier0_entries: list[dict],
    tier1_routes: list[dict],
    self_tier1: str,
    self_route_id: str,
    segments: list[dict],
    db_rows: list[dict],
    self_network_id: int,
    results: dict[str, dict] | None = None,
    self_advertised: bool = False,
) -> dict[str, dict]:
    """Run every check in order; raise ``ValueError`` with the first verdict that fails.

    ``results`` carries checks already made (the zcore VLAN check) into the
    returned mapping ``name -> {"ok", "count", "detail", "inventory"}``.
    """
    results = dict(results or {})
    for result in (
        check_tier0_routes(candidate, tier0_entries, tier0_id, self_advertised),
        check_tier1_static_routes(candidate, tier1_routes, self_tier1, self_route_id),
        check_segment_subnets(candidate, segments),
        check_db_networks(candidate, db_rows, self_network_id),
        check_prefix_length(candidate),
    ):
        results[result.name] = result.as_dict()
        if not result.ok:
            raise ValueError(result.detail)
    return results
