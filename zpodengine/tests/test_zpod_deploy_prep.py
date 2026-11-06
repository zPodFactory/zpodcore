"""Deploy prep is idempotent: a re-run keeps the zPod's first /24.

Before 0.9.1, each run of the deploy flow run allocated a fresh /24 and appended
four more rows, which the (zpod_id, vlan_id) unique constraint now refuses.
"""

from contextlib import contextmanager
from ipaddress import IPv4Network

import pytest
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from zpodcommon import models as M
from zpodengine.lib import database as engine_database
from zpodengine.zpod_deploy import zpod_deploy_1_prep as prep_mod


@pytest.fixture
def world(monkeypatch):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)

    @contextmanager
    def ctx():
        with Session(engine) as session:
            yield session

    allocated = iter(["10.42.132.0/24", "10.42.181.0/24", "10.42.172.0/24"])
    calls = []

    def primary_subnet(endpoint, taken=()):
        calls.append(sorted(str(t) for t in taken))
        return IPv4Network(next(allocated))

    monkeypatch.setattr(engine_database, "get_session_ctx", ctx)
    monkeypatch.setattr(prep_mod, "get_zpod_primary_subnet", primary_subnet)
    monkeypatch.setattr(
        prep_mod.DBUtils,
        "get_setting_value",
        classmethod(
            lambda cls, name: (
                "zpod.example" if name == "zpodfactory_default_domain" else None
            )
        ),
    )
    with Session(engine) as session:
        zpod = M.Zpod(name="lab", endpoint_id=1, status="PENDING", profile="p")
        session.add(zpod)
        session.commit()
        zpod_id = zpod.id
    return engine, zpod_id, calls


def cidrs(engine, zpod_id):
    with Session(engine) as session:
        return [
            n.cidr
            for n in session.exec(
                select(M.ZpodNetwork)
                .where(M.ZpodNetwork.zpod_id == zpod_id)
                .order_by(M.ZpodNetwork.id)
            )
        ]


def test_first_run_allocates_one_slash24(world):
    engine, zpod_id, calls = world
    prep_mod.zpod_deploy_prep.fn(zpod_id=zpod_id)
    assert cidrs(engine, zpod_id) == [f"10.42.132.{o}/26" for o in (0, 64, 128, 192)]
    assert len(calls) == 1


def test_a_rerun_reuses_the_networks(world):
    engine, zpod_id, calls = world
    for _ in range(3):
        prep_mod.zpod_deploy_prep.fn(zpod_id=zpod_id)
    assert cidrs(engine, zpod_id) == [f"10.42.132.{o}/26" for o in (0, 64, 128, 192)]
    assert len(calls) == 1
    with Session(engine) as session:
        zpod = session.get(M.Zpod, zpod_id)
        assert zpod.status == "BUILDING"
        assert zpod.domain == "lab.zpod.example"


def test_other_live_zpods_subnets_are_taken(world):
    """A concurrent deploy has its rows in the database before its NSX segment
    exists: prep must hand them to the allocator. DELETED zPods free theirs."""
    engine, zpod_id, calls = world
    with Session(engine) as session:
        for name, status, cidr in (
            ("busy", "BUILDING", "10.60.40.0/26"),
            ("kept", "DEPLOY_FAILED", "10.60.41.0/26"),
            ("gone", "DELETED", "10.60.42.0/26"),
        ):
            other = M.Zpod(name=name, endpoint_id=1, status=status, profile="p")
            other.networks.append(M.ZpodNetwork.deploy_row(IPv4Network(cidr)))
            session.add(other)
        session.commit()

    prep_mod.zpod_deploy_prep.fn(zpod_id=zpod_id)
    assert calls == [["10.60.40.0/26", "10.60.41.0/26"]]


def test_allocator_skips_taken_subnets(monkeypatch):
    """With no NSX segment yet, a /24 held in the database is never handed out."""
    from zpodengine.lib import network

    class FakeNsx:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def search(self, resource_type):
            return []

    monkeypatch.setattr(
        network.NsxClient,
        "auth_by_endpoint",
        classmethod(lambda cls, endpoint: FakeNsx()),
    )
    endpoint = type(
        "E", (), {"endpoints": {"network": {"networks": "10.60.40.0/23"}}}
    )()
    for _ in range(20):  # the candidate order is random
        subnet = network.get_zpod_primary_subnet(
            endpoint, taken=[IPv4Network("10.60.40.0/26")]
        )
        assert subnet == IPv4Network("10.60.41.0/24")
