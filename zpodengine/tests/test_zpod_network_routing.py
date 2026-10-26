"""Advertisement guardrails, the artifact and the route step, without NSX or a database."""

import ipaddress
from types import SimpleNamespace

import pytest

from zpodengine.zpod_network_routing import guardrails as g
from zpodengine.zpod_network_routing.common import FACTORY_MARK
from zpodengine.zpod_network_routing.zpod_network_routing_2_artifact import (
    artifact_key,
    render_markdown,
)
from zpodengine.zpod_network_routing.zpod_network_routing_3_route import (
    advertise,
    withdraw,
)

CANDIDATE = ipaddress.ip_network("10.10.100.0/24")
T1 = "zpod-demo-tier1"
ROUTE = "demo-wld01"


def ok(result):
    assert result.ok, result.detail
    return result


# --- T0 routing table -----------------------------------------------------------


def test_tier0_passes_when_nothing_overlaps():
    entries = [
        {"network": "10.96.50.0/26", "route_type": "t1c", "next_hop": "100.64.0.1"},
        {"network": "172.16.0.0/12", "route_type": "b", "next_hop": "172.16.1.1"},
    ]
    result = ok(g.check_tier0_routes(CANDIDATE, entries, "t0-site"))
    assert result.count == 2
    assert result.inventory[0] == "10.96.50.0/26 type=t1c next_hop=100.64.0.1"


def test_tier0_fails_on_overlap_naming_the_route():
    entries = [{"network": "10.0.0.0/8", "route_type": "b", "next_hop": "172.16.1.1"}]
    result = g.check_tier0_routes(CANDIDATE, entries, "t0-site")
    assert not result.ok
    assert result.detail == (
        "FAIL: 10.10.100.0/24 overlaps 10.0.0.0/8 from the routing table of T0 t0-site "
        "(route_type b, next hop 172.16.1.1)"
    )


def test_tier0_skips_our_own_advertisement_only_when_told():
    own = {"network": "10.10.100.0/24", "route_type": "t1s", "next_hop": "100.64.0.9"}
    assert not g.check_tier0_routes(CANDIDATE, [own], "t0").ok
    result = ok(g.check_tier0_routes(CANDIDATE, [own], "t0", self_advertised=True))
    assert result.count == 0
    # a connected or BGP route with the same prefix is never ours
    other = {"network": "10.10.100.0/24", "route_type": "t0c", "next_hop": ""}
    assert not g.check_tier0_routes(CANDIDATE, [other], "t0", self_advertised=True).ok


def test_tier0_ignores_ipv6_entries():
    ok(g.check_tier0_routes(CANDIDATE, [{"network": "::/0", "route_type": "b"}], "t0"))


# --- T1 static routes -----------------------------------------------------------


def route(tier1, route_id, network, description=None):
    return {
        "tier1": tier1,
        "route_id": route_id,
        "network": network,
        "next_hops": ["10.96.50.2"],
        "description": description,
    }


def test_tier1_excludes_this_networks_own_route_on_a_rerun():
    routes = [
        route(T1, ROUTE, "10.10.100.0/24", "advertised by admin via zPodFactory"),
        route(T1, "demo-vlan64", "10.96.50.64/26"),
    ]
    result = ok(g.check_tier1_static_routes(CANDIDATE, routes, T1, ROUTE))
    assert result.count == 1


def test_tier1_fails_on_another_zpods_route():
    routes = [
        route(
            "zpod-other-tier1",
            "other-lab",
            "10.10.0.0/16",
            "advertised by bob via zPodFactory",
        )
    ]
    result = g.check_tier1_static_routes(CANDIDATE, routes, T1, ROUTE)
    assert result.detail == (
        "FAIL: 10.10.100.0/24 overlaps 10.10.0.0/16 from static route other-lab on T1 "
        "zpod-other-tier1 (advertised by bob via zPodFactory)"
    )


def test_tier1_same_route_id_on_another_tier1_is_not_self():
    routes = [route("zpod-other-tier1", ROUTE, "10.10.100.0/24")]
    assert not g.check_tier1_static_routes(CANDIDATE, routes, T1, ROUTE).ok


# --- segments -------------------------------------------------------------------


def test_segments_fail_on_overlap():
    segments = [
        {"segment": "zpod-a-segment", "network": "10.96.50.0/26"},
        {"segment": "transit", "network": "10.10.100.128/25"},
    ]
    result = g.check_segment_subnets(CANDIDATE, segments)
    assert (
        result.detail
        == "FAIL: 10.10.100.0/24 overlaps 10.10.100.128/25 from segment transit"
    )
    ok(g.check_segment_subnets(CANDIDATE, segments[:1]))


# --- database -------------------------------------------------------------------


def db_row(zpod, status, network, network_id, cidr):
    return {
        "zpod": zpod,
        "zpod_status": status,
        "network": network,
        "network_id": network_id,
        "cidr": cidr,
    }


def test_db_skips_deleted_zpods_and_self():
    rows = [
        db_row("demo", "ACTIVE", "wld01", 7, "10.10.100.0/24"),  # self
        db_row("gone", "DELETED", "lab", 3, "10.10.100.0/24"),
        db_row("live", "ACTIVE", "mgmt", 4, "10.96.51.0/26"),
    ]
    result = ok(g.check_db_networks(CANDIDATE, rows, self_network_id=7))
    assert result.count == 1


def test_db_fails_on_a_live_zpod():
    rows = [db_row("live", "ACTIVE", "wld01", 9, "10.10.0.0/16")]
    result = g.check_db_networks(CANDIDATE, rows, self_network_id=7)
    assert result.detail == (
        "FAIL: 10.10.100.0/24 overlaps 10.10.0.0/16 from network wld01 of zPod live (database)"
    )


# --- prefix length --------------------------------------------------------------


@pytest.mark.parametrize(
    ("cidr", "fragment"),
    [
        ("10.0.0.0/7", "larger than the /8"),
        ("10.10.100.0/31", "smaller than the /30"),
        ("224.0.0.0/24", "multicast"),
        ("127.0.0.0/24", "loopback"),
        ("169.254.1.0/24", "link-local"),
        ("0.0.0.0/16", "unspecified"),
    ],
)
def test_prefix_length_failures(cidr, fragment):
    result = g.check_prefix_length(ipaddress.ip_network(cidr))
    assert not result.ok
    assert fragment in result.detail


@pytest.mark.parametrize("cidr", ["10.0.0.0/8", "10.10.100.0/24", "10.10.100.0/30"])
def test_prefix_length_bounds_are_inclusive(cidr):
    ok(g.check_prefix_length(ipaddress.ip_network(cidr)))


# --- the run --------------------------------------------------------------------


def fabric(**overrides):
    args = {
        "tier0_id": "t0-site",
        "tier0_entries": [
            {"network": "10.96.0.0/16", "route_type": "t1c", "next_hop": "100.64.0.1"}
        ],
        "tier1_routes": [route(T1, "demo-vlan64", "10.96.50.64/26")],
        "self_tier1": T1,
        "self_route_id": ROUTE,
        "segments": [{"segment": "zpod-demo-segment", "network": "10.96.50.0/26"}],
        "db_rows": [db_row("demo", "ACTIVE", "wld01", 7, "10.10.100.0/24")],
        "self_network_id": 7,
    }
    return args | overrides


def test_run_fabric_checks_returns_every_check_in_order():
    results = g.run_fabric_checks(
        CANDIDATE,
        **fabric(),
        results={
            "zcore_vlan": {"ok": True, "count": 1, "detail": "ok", "inventory": []}
        },
    )
    assert list(results) == [
        "zcore_vlan",
        "tier0_routing_table",
        "tier1_static_routes",
        "segment_subnets",
        "database_networks",
        "prefix_length",
    ]
    assert all(r["ok"] for r in results.values())
    assert set(results["tier0_routing_table"]) == {
        "name",
        "ok",
        "count",
        "detail",
        "inventory",
    }


def test_run_fabric_checks_raises_the_first_failure():
    args = fabric(tier1_routes=[route("zpod-x-tier1", "x-lab", "10.10.100.0/25")])
    with pytest.raises(ValueError, match="static route x-lab on T1 zpod-x-tier1"):
        g.run_fabric_checks(CANDIDATE, **args)


# --- artifact -------------------------------------------------------------------


def test_artifact_key_is_lowercase_alnum_and_dashes():
    assert artifact_key("Demo_Pod", "wld 01") == "advertisement-demo-pod-wld-01"


def test_render_markdown_lists_checks_and_inventories():
    checks = {
        "tier0_routing_table": {
            "ok": True,
            "count": 1,
            "detail": "ok",
            "inventory": ["10.96.0.0/16 type=t1c next_hop=100.64.0.1"],
        }
    }
    markdown = render_markdown(
        zpod_name="demo",
        network_name="wld01",
        target="GLOBAL",
        requested_by="admin",
        dry_run=True,
        timestamp="2026-10-10T10:00:00+00:00",
        candidate="10.10.100.0/24",
        tier1_id=T1,
        route_id=ROUTE,
        next_hop="10.96.50.2",
        checks=checks,
    )
    assert "# Advertise demo/wld01" in markdown
    assert "| tier0_routing_table | ok | 1 | ok |" in markdown
    assert "<summary>tier0_routing_table inventory (1 lines)</summary>" in markdown
    assert "10.96.0.0/16 type=t1c next_hop=100.64.0.1" in markdown
    assert "| Dry run | True |" in markdown


def test_render_markdown_for_a_withdrawal_has_no_checks():
    markdown = render_markdown(
        zpod_name="demo",
        network_name="wld01",
        target="LOCAL",
        requested_by="admin",
        dry_run=False,
        timestamp="t",
        candidate="10.10.100.0/24",
        tier1_id=T1,
        route_id=ROUTE,
        next_hop="10.96.50.2",
        checks={},
    )
    assert markdown.startswith("# Withdraw demo/wld01")
    assert "withdrawn" in markdown


# --- route step -----------------------------------------------------------------


class RouteNsx:
    """One static route slot; records writes."""

    def __init__(self, existing=None):
        self.existing = existing
        self.patches, self.deletes = [], []

    def get(self, url, params=None):
        if "realized-entities" in url:
            return SimpleNamespace(results=lambda: [{"state": "REALIZED"}])
        return SimpleNamespace(safejson=lambda: self.existing or {})

    def patch(self, url, json):
        self.patches.append((url, json))

    def delete(self, url):
        self.deletes.append(url)
        return SimpleNamespace(status_code=200, safejson=lambda: {})


def facts():
    from zpodengine.zpod_network_routing.common import RouteFacts

    return RouteFacts(
        candidate=CANDIDATE,
        tier0_id="t0-site",
        tier1_id=T1,
        route_id=ROUTE,
        base_path="/policy/api/v1",
        next_hop="10.96.50.2",
    )


def test_advertise_creates_a_marked_route_and_waits():
    nsx = RouteNsx()
    advertise(nsx, facts(), "admin")
    ((url, body),) = nsx.patches
    assert url == f"/policy/api/v1/infra/tier-1s/{T1}/static-routes/{ROUTE}"
    assert body["network"] == "10.10.100.0/24"
    assert body["next_hops"] == [{"ip_address": "10.96.50.2", "admin_distance": 1}]
    assert body["description"].startswith("advertised by admin on 20")
    assert body["description"].endswith(FACTORY_MARK)


def test_withdraw_refuses_a_route_zpodfactory_did_not_create():
    nsx = RouteNsx({"id": ROUTE, "network": "10.10.100.0/24", "description": "by hand"})
    with pytest.raises(ValueError, match="refusing to delete"):
        withdraw(nsx, facts())
    assert nsx.deletes == []


def test_withdraw_deletes_our_route_and_is_idempotent():
    nsx = RouteNsx(
        {
            "id": ROUTE,
            "network": "10.10.100.0/24",
            "description": f"advertised by admin {FACTORY_MARK}",
        }
    )
    withdraw(nsx, facts())
    assert nsx.deletes == [f"/policy/api/v1/infra/tier-1s/{T1}/static-routes/{ROUTE}"]
    nothing = RouteNsx()
    withdraw(nothing, facts())
    assert nothing.deletes == []
