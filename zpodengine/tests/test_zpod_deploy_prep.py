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

    def primary_subnet(endpoint):
        calls.append(1)
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
    assert calls == [1]


def test_a_rerun_reuses_the_networks(world):
    engine, zpod_id, calls = world
    for _ in range(3):
        prep_mod.zpod_deploy_prep.fn(zpod_id=zpod_id)
    assert cidrs(engine, zpod_id) == [f"10.42.132.{o}/26" for o in (0, 64, 128, 192)]
    assert calls == [1]
    with Session(engine) as session:
        zpod = session.get(M.Zpod, zpod_id)
        assert zpod.status == "BUILDING"
        assert zpod.domain == "lab.zpod.example"
