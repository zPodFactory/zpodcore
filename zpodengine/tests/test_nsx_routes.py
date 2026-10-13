"""T1 static routes and fabric inventories against a stub NSX client."""

import pytest

from zpodengine.lib import nsx_routes

BASE = nsx_routes.POLICY_BASE
T1 = "zpod-demo-tier1"


class FakeResponse:
    def __init__(self, payload=None, status_code=200):
        self._payload, self.status_code = payload, status_code

    def safejson(self):
        # Mirrors zpodcommon.lib.nsx.safejson: 404 is {}.
        if self.status_code == 404:
            return {}
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")
        return self._payload if self._payload is not None else {}

    def results(self):
        return self.safejson().get("results", [])


class FakeNsx:
    """Answers GETs from a {url: payload | [payload per page]} table and records writes."""

    def __init__(self, gets=None, delete_status=200):
        self.gets = dict(gets or {})
        self.calls, self.patches, self.deletes = [], [], []
        self.delete_status = delete_status

    def get(self, url, params=None):
        self.calls.append((url, params))
        key = url.split("?")[0] if url.startswith(f"{BASE}/infra/tier-1s") else url
        answer = self.gets.get(key, self.gets.get(url))
        if answer is None:
            return FakeResponse(status_code=404)
        if isinstance(answer, list):
            # Paged: the cursor is the page index to serve next.
            page = int((params or {}).get("cursor") or 0)
            payload = dict(answer[page])
            if page + 1 < len(answer):
                payload["cursor"] = str(page + 1)
            return FakeResponse(payload)
        return FakeResponse(answer)

    def patch(self, url, json):
        self.patches.append((url, json))
        return FakeResponse({})

    def delete(self, url):
        self.deletes.append(url)
        return FakeResponse(status_code=self.delete_status)

    def search(self, **terms):
        return self.gets.get(("search", terms["resource_type"]), [])


def test_static_route_put_patches_the_route_with_one_next_hop():
    nsx = FakeNsx()
    nsx_routes.static_route_put(
        nsx, T1, "demo-wld01", "10.10.100.0/24", "10.96.50.2", description="by admin"
    )
    assert nsx.patches == [
        (
            f"{BASE}/infra/tier-1s/{T1}/static-routes/demo-wld01",
            {
                "network": "10.10.100.0/24",
                "next_hops": [{"ip_address": "10.96.50.2", "admin_distance": 1}],
                "description": "by admin",
            },
        )
    ]


def test_static_route_put_under_a_project_base_path():
    nsx = FakeNsx()
    base = f"{BASE}/orgs/default/projects/zpod-demo-project"
    nsx_routes.static_route_put(
        nsx, T1, "demo-vlan64", "10.96.50.64/26", "10.96.50.2", base_path=base
    )
    assert nsx.patches[0][0] == f"{base}/infra/tier-1s/{T1}/static-routes/demo-vlan64"
    assert "description" not in nsx.patches[0][1]


def test_static_route_get_returns_none_on_404():
    url = f"{BASE}/infra/tier-1s/{T1}/static-routes/demo-wld01"
    assert nsx_routes.static_route_get(FakeNsx(), T1, "demo-wld01") is None
    route = {"id": "demo-wld01", "network": "10.10.100.0/24"}
    assert nsx_routes.static_route_get(FakeNsx({url: route}), T1, "demo-wld01") == route


def test_static_route_delete_ignores_404_and_raises_otherwise():
    nsx = FakeNsx(delete_status=404)
    nsx_routes.static_route_delete(nsx, T1, "demo-wld01")
    assert nsx.deletes == [f"{BASE}/infra/tier-1s/{T1}/static-routes/demo-wld01"]
    with pytest.raises(RuntimeError, match="HTTP 500"):
        nsx_routes.static_route_delete(FakeNsx(delete_status=500), T1, "demo-wld01")


def test_static_route_wait_realized(monkeypatch):
    url = (
        f"{BASE}/infra/realized-state/realized-entities"
        f"?intent_path=/infra/tier-1s/{T1}/static-routes/demo-wld01"
    )
    answers = iter(
        [
            {"results": []},
            {"results": [{"state": "UNREALIZED"}]},
            {"results": [{"state": "REALIZED"}]},
        ]
    )
    nsx = FakeNsx()
    nsx.get = lambda url=url, params=None: FakeResponse(next(answers))
    monkeypatch.setattr(nsx_routes.time, "sleep", lambda s: None)
    nsx_routes.static_route_wait_realized(
        nsx, T1, "demo-wld01", max_wait=60, interval=0
    )


def test_static_route_wait_realized_times_out(monkeypatch):
    clock = iter(range(0, 1000, 50))
    monkeypatch.setattr(nsx_routes.time, "monotonic", lambda: next(clock))
    monkeypatch.setattr(nsx_routes.time, "sleep", lambda s: None)
    nsx = FakeNsx()
    nsx.get = lambda url, params=None: FakeResponse(
        {"results": [{"state": "UNREALIZED"}]}
    )
    with pytest.raises(TimeoutError, match="demo-wld01"):
        nsx_routes.static_route_wait_realized(nsx, T1, "demo-wld01", max_wait=120)


def test_flatten_routing_table_drops_default_and_duplicates_across_edges():
    payload = {
        "results": [
            {
                "edge_node": "edge-1",
                "route_entries": [
                    {
                        "network": "0.0.0.0/0",
                        "route_type": "t0s",
                        "next_hop": "172.16.1.1",
                    },
                    {
                        "network": "10.96.50.0/26",
                        "route_type": "t1c",
                        "next_hop": "100.64.0.1",
                    },
                    {
                        "network": "10.0.0.0/8",
                        "route_type": "b",
                        "next_hop": "172.16.1.1",
                        "admin_distance": 20,
                    },
                ],
            },
            {
                "edge_node": "edge-2",
                "route_entries": [
                    {
                        "network": "0.0.0.0/0",
                        "route_type": "t0s",
                        "next_hop": "172.16.1.1",
                    },
                    {
                        "network": "10.96.50.0/26",
                        "route_type": "t1c",
                        "next_hop": "100.64.0.1",
                    },
                    {
                        "network": "10.0.0.0/8",
                        "route_type": "b",
                        "next_hop": "172.16.1.2",
                        "admin_distance": 20,
                    },
                ],
            },
        ]
    }
    entries = nsx_routes.flatten_routing_table(payload)
    assert [(e["network"], e["route_type"], e["next_hop"]) for e in entries] == [
        ("10.96.50.0/26", "t1c", "100.64.0.1"),
        ("10.0.0.0/8", "b", "172.16.1.1"),
        ("10.0.0.0/8", "b", "172.16.1.2"),
    ]
    assert entries[1]["admin_distance"] == 20


def test_tier0_routing_table_reads_the_t0():
    nsx = FakeNsx(
        {
            f"{BASE}/infra/tier-0s/t0-site/routing-table": {
                "results": [
                    {"route_entries": [{"network": "10.0.0.0/8", "route_type": "b"}]}
                ]
            }
        }
    )
    assert nsx_routes.tier0_routing_table(nsx, "t0-site") == [
        {
            "network": "10.0.0.0/8",
            "route_type": "b",
            "next_hop": None,
            "admin_distance": None,
        }
    ]


def test_all_tier1_static_routes_paginates_tier1s_and_routes():
    nsx = FakeNsx(
        {
            f"{BASE}/infra/tier-1s": [
                {"results": [{"id": "zpod-a-tier1"}]},
                {"results": [{"id": "zpod-b-tier1"}]},
            ],
            f"{BASE}/infra/tier-1s/zpod-a-tier1/static-routes": [
                {
                    "results": [
                        {
                            "id": "a-vlan64",
                            "network": "10.96.50.64/26",
                            "next_hops": [{"ip_address": "10.96.50.2"}],
                        }
                    ]
                },
                {
                    "results": [
                        {
                            "id": "a-wld01",
                            "network": "10.10.100.0/24",
                            "next_hops": [{"ip_address": "10.96.50.2"}],
                            "description": "advertised by admin via zPodFactory",
                        }
                    ]
                },
            ],
            f"{BASE}/infra/tier-1s/zpod-b-tier1/static-routes": {"results": []},
        }
    )
    routes = nsx_routes.all_tier1_static_routes(nsx)
    assert routes == [
        {
            "tier1": "zpod-a-tier1",
            "route_id": "a-vlan64",
            "network": "10.96.50.64/26",
            "next_hops": ["10.96.50.2"],
            "description": None,
        },
        {
            "tier1": "zpod-a-tier1",
            "route_id": "a-wld01",
            "network": "10.10.100.0/24",
            "next_hops": ["10.96.50.2"],
            "description": "advertised by admin via zPodFactory",
        },
    ]
    # Both pages of the T1 list and of the first T1's routes were followed.
    assert (f"{BASE}/infra/tier-1s", {"cursor": "1"}) in nsx.calls
    assert (
        f"{BASE}/infra/tier-1s/zpod-a-tier1/static-routes",
        {"cursor": "1"},
    ) in nsx.calls


def test_all_segment_subnets_keeps_ipv4_only():
    nsx = FakeNsx(
        {
            ("search", "Segment"): [
                {
                    "display_name": "zpod-a-segment",
                    "subnets": [
                        {"network": "10.96.50.0/26"},
                        {"network": "fd00::/64"},
                        {"gateway_address": "10.96.51.1/26"},
                    ],
                },
                {"id": "no-subnets"},
            ]
        }
    )
    assert nsx_routes.all_segment_subnets(nsx) == [
        {"segment": "zpod-a-segment", "network": "10.96.50.0/26"}
    ]
