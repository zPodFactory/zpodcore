"""The routing flow end to end, in-process, with every external call faked.

What the single tests of the tasks cannot show: the order that matters (fabric read,
checks and route write in one locked task; masquerade dropped only after the route is
realized), the dry run leaving the row at its previous value, and the on_failure hook
putting the row back when a check fails.
"""

from contextlib import contextmanager

import pytest
from prefect.testing.utilities import prefect_test_harness
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from test_nsx_routes import BASE, FakeNsx, FakeResponse

from zpodcommon import models as M
from zpodengine.lib import database as engine_database
from zpodengine.lib import nsx_routes
from zpodengine.zpod_network_routing import (
    zpod_network_routing_1_checks as checks_mod,
)
from zpodengine.zpod_network_routing import (
    zpod_network_routing_3_route as route_mod,
)
from zpodengine.zpod_network_routing import (
    zpod_network_routing_4_masquerade as masq_mod,
)
from zpodengine.zpod_network_routing.flow_zpod_network_routing import (
    flow_zpod_network_routing,
)

T1 = "zpod-demo-tier1"
CALLS: list = []  # every external effect, in order: ("nsx", url) / ("zbox", method, url)


class RecordingNsx(FakeNsx):
    def get(self, url, params=None):
        url = url.split("?")[
            0
        ]  # the realization poll carries the intent path as a query
        CALLS.append(("nsx", "GET", url))
        return super().get(url, params)

    def patch(self, url, json):
        CALLS.append(("nsx", "PATCH", url))
        return super().patch(url, json)

    def delete(self, url):
        CALLS.append(("nsx", "DELETE", url))
        return super().delete(url)

    def search(self, **terms):
        CALLS.append(("nsx", "SEARCH", terms["resource_type"]))
        return super().search(**terms)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class FakeZbox:
    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def get(self, url):
        CALLS.append(("zbox", "GET", url))
        return FakeResponse(
            {"vlan": 111, "interface": "eth1.111", "status": "up", "masquerade": True}
        )

    def put(self, url, json=None):
        CALLS.append(("zbox", "PUT", url, json))
        return FakeResponse({"vlan": 111, "masquerade": json["enabled"]})


@pytest.fixture(scope="module")
def prefect():
    with prefect_test_harness():
        yield


@pytest.fixture
def db(monkeypatch):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)

    @contextmanager
    def ctx():
        with Session(engine) as session:
            yield session

    monkeypatch.setattr(engine_database, "get_session_ctx", ctx)
    with Session(engine) as session:
        endpoint = M.Endpoint(
            name="ep",
            endpoints={"network": {"t0": "t0-site", "networks": "10.60.0.0/16"}},
            status="ACTIVE",
        )
        session.add(endpoint)
        session.flush()
        zpod = M.Zpod(
            name="demo",
            domain="demo.example.com",
            endpoint_id=endpoint.id,
            profile="p",
            status="ACTIVE",
            password="pw",
        )
        from ipaddress import IPv4Network

        for subnet in IPv4Network("10.60.194.0/24").subnets(new_prefix=26):
            zpod.networks.append(M.ZpodNetwork.deploy_row(subnet))
        zpod.networks.append(
            M.ZpodNetwork(
                cidr="10.42.111.0/24",
                name="LOCALNET111",
                vlan_id=111,
                gateway="10.42.111.1/24",
                kind="user",
                masquerade=True,
                routing="PENDING",  # as the API sets it before scheduling the flow
            )
        )
        session.add(zpod)
        session.commit()
        ids = (zpod.id, zpod.networks[-1].id)
    return engine, ids


def fabric(tier0_entries):
    route_url = f"{BASE}/infra/tier-1s/{T1}/static-routes/demo-LOCALNET111"
    return RecordingNsx(
        gets={
            f"{BASE}/infra/tier-0s/t0-site/routing-table": {
                "results": [{"route_entries": tier0_entries}]
            },
            f"{BASE}/infra/tier-1s": {"results": [{"id": T1}]},
            f"{BASE}/infra/tier-1s/{T1}/static-routes": {"results": []},
            ("search", "Segment"): [],
            f"{BASE}/infra/realized-state/realized-entities": {
                "results": [{"state": "REALIZED"}]
            },
            route_url: None,  # not there yet
        }
    )


@pytest.fixture
def fakes(monkeypatch):
    CALLS.clear()
    nsx = fabric([{"network": "10.96.0.0/16", "route_type": "t1c", "next_hop": "x"}])
    monkeypatch.setattr(
        route_mod.NsxClient, "auth_by_endpoint", staticmethod(lambda endpoint: nsx)
    )
    monkeypatch.setattr(
        checks_mod.ZboxApiClient, "by_zpod", staticmethod(lambda zpod: FakeZbox())
    )
    monkeypatch.setattr(
        masq_mod.ZboxApiClient, "by_zpod", staticmethod(lambda zpod: FakeZbox())
    )
    # a fake time module for the realization poll only (patching time.sleep itself
    # would also stop Prefect's own waits)
    import time as _time
    from types import SimpleNamespace

    monkeypatch.setattr(
        nsx_routes,
        "time",
        SimpleNamespace(
            sleep=lambda s: None, time=_time.time, monotonic=_time.monotonic
        ),
    )
    return nsx


def routing_of(engine, network_id):
    with Session(engine) as session:
        n = session.get(M.ZpodNetwork, network_id)
        return n.routing, n.masquerade


def run(zpod_id, network_id, target, dry_run=False, previous=None):
    return flow_zpod_network_routing(
        zpod_id=zpod_id,
        network_id=network_id,
        target=target,
        previous=previous or ("LOCAL" if target == "GLOBAL" else "GLOBAL"),
        requested_by="timo",
        zpod_name="demo",
        network_name="LOCALNET111",
        verb="advertise" if target == "GLOBAL" else "withdraw",
        dry_run=dry_run,
    )


def test_advertise_reads_checks_writes_in_one_locked_task_then_drops_masquerade(
    prefect, db, fakes
):
    engine, (zpod_id, network_id) = db
    run(zpod_id, network_id, "GLOBAL")
    kinds = [c[:2] for c in CALLS]
    # fabric reads (zcore VLAN, T0 table, T1 list, T1 routes, segments) ...
    first_write = kinds.index(("nsx", "PATCH"))
    assert ("zbox", "GET") in kinds[:first_write]
    assert all(
        k in (("nsx", "GET"), ("nsx", "SEARCH"), ("zbox", "GET"))
        for k in kinds[:first_write]
    )
    # ... then the route write, its realization read, and only then masquerade off
    masq_off = kinds.index(("zbox", "PUT"))
    assert first_write < masq_off
    assert CALLS[masq_off][3] == {"enabled": False}
    assert routing_of(engine, network_id) == ("GLOBAL", False)
    # the locked task holds the engine's shared lock
    assert "atomic_operation" in route_mod.zpod_network_routing_route.tags


def test_dry_run_checks_but_writes_nothing_and_restores_the_row(prefect, db, fakes):
    engine, (zpod_id, network_id) = db
    run(zpod_id, network_id, "GLOBAL", dry_run=True)
    kinds = [c[:2] for c in CALLS]
    assert ("nsx", "GET") in kinds and ("nsx", "PATCH") not in kinds
    assert ("zbox", "PUT") not in kinds
    assert routing_of(engine, network_id) == ("LOCAL", True)


def test_failed_check_writes_nothing_and_the_hook_restores_the_row(
    prefect, db, fakes, monkeypatch
):
    engine, (zpod_id, network_id) = db
    overlapping = fabric(
        [{"network": "10.42.0.0/16", "route_type": "b", "next_hop": "r"}]
    )
    monkeypatch.setattr(
        route_mod.NsxClient,
        "auth_by_endpoint",
        staticmethod(lambda endpoint: overlapping),
    )
    with pytest.raises(Exception, match="overlaps 10.42.0.0/16"):
        run(zpod_id, network_id, "GLOBAL")
    kinds = [c[:2] for c in CALLS]
    assert ("nsx", "PATCH") not in kinds and ("zbox", "PUT") not in kinds
    assert routing_of(engine, network_id) == ("LOCAL", True)


def test_withdraw_deletes_our_route_only(prefect, db, fakes):
    engine, (zpod_id, network_id) = db
    route_url = f"{BASE}/infra/tier-1s/{T1}/static-routes/demo-LOCALNET111"
    fakes.gets[route_url] = {
        "id": "demo-LOCALNET111",
        "network": "10.42.111.0/24",
        "description": "advertised by timo on 2026-10-13 via zPodFactory",
    }
    run(zpod_id, network_id, "LOCAL")
    assert ("nsx", "DELETE", route_url) in CALLS
    assert ("zbox", "PUT") not in [
        c[:2] for c in CALLS
    ]  # masquerade untouched on withdraw
    assert routing_of(engine, network_id) == ("LOCAL", True)


def test_dry_run_on_an_already_global_network_passes_and_keeps_global(
    prefect, db, fakes
):
    """The T0 table lists our own advertisement (t1s, same prefix): not an overlap,
    and the row goes back to GLOBAL, not to the other state."""
    engine, (zpod_id, network_id) = db
    route_url = f"{BASE}/infra/tier-1s/{T1}/static-routes/demo-LOCALNET111"
    fakes.gets[route_url] = {
        "id": "demo-LOCALNET111",
        "network": "10.42.111.0/24",
        "description": "advertised by timo on 2026-10-13 via zPodFactory",
    }
    fakes.gets[f"{BASE}/infra/tier-0s/t0-site/routing-table"] = {
        "results": [
            {
                "route_entries": [
                    {
                        "network": "10.42.111.0/24",
                        "route_type": "t1s",
                        "next_hop": "100.64.0.29",
                    }
                ]
            }
        ]
    }
    run(zpod_id, network_id, "GLOBAL", dry_run=True, previous="GLOBAL")
    kinds = [c[:2] for c in CALLS]
    assert ("nsx", "PATCH") not in kinds and ("zbox", "PUT") not in kinds
    assert routing_of(engine, network_id) == ("GLOBAL", True)
