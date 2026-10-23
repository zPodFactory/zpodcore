from datetime import datetime
from ipaddress import IPv4Network

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from zpodapi.lib.global_dependencies import get_session
from zpodapi.main import api
from zpodcommon import models as M


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    api.dependency_overrides[get_session] = get_session_override
    yield TestClient(api)
    api.dependency_overrides.clear()


@pytest.fixture(name="superadmin_client")
def superadmin_client_fixture(client: TestClient):
    client.headers["access_token"] = "APITOKEN_SUPERUSER"
    yield client


@pytest.fixture(name="normaluser_client")
def normaluser_client_fixture(client: TestClient):
    client.headers["access_token"] = "APITOKEN_NORMALUSER"
    yield client


@pytest.fixture(autouse=True, name="db_seed")
def db_seed(session: Session):
    superadmin_user = M.User(
        username="superuser",
        email="superuser@zpodfactory.io",
        api_token="APITOKEN_SUPERUSER",
        creation_date=datetime(2022, 1, 1, 0, 0, 0),
        superadmin=True,
        status="ENABLED",
    )
    session.add(superadmin_user)

    normal_user = M.User(
        username="normaluser",
        email="normaluser@zpodfactory.io",
        api_token="APITOKEN_NORMALUSER",
        creation_date=datetime(2022, 1, 1, 0, 0, 0),
        superadmin=False,
        status="ENABLED",
    )
    session.add(normal_user)
    session.commit()


ZPOD_SUBNET = IPv4Network("10.60.60.0/24")


@pytest.fixture
def lab(session: Session):
    """An ACTIVE zPod 'lab' owned by normaluser, with its four deploy rows."""
    endpoint = M.Endpoint(
        name="ep",
        endpoints={
            "network": {
                "t0": "edge-t0",
                "networks": "10.60.0.0/16",
                "hostname": "nsx",
                "username": "u",
                "password": "p",
            }
        },
        status="ACTIVE",
    )
    zcore = M.Component(
        component_uid="zcore-13.5",
        component_name="zcore",
        component_version="13.5",
        component_description="zcore",
        filename="zcore.ova",
        jsonfile="/library/zcore.json",
        status="ACTIVE",
        download_status="COMPLETED",
        file_checksum="abc",
    )
    session.add_all([endpoint, zcore])
    session.flush()
    normal_user = session.get(M.User, 2)
    zpod = M.Zpod(
        name="lab",
        domain="lab.example.com",
        endpoint_id=endpoint.id,
        profile="sddc",
        status="ACTIVE",
        password="pw",
        permissions=[M.ZpodPermission(permission="OWNER", users=[normal_user])],
    )
    for subnet in ZPOD_SUBNET.subnets(new_prefix=26):
        zpod.networks.append(M.ZpodNetwork.deploy_row(subnet))
    zpod.components.append(
        M.ZpodComponent(
            component_id=zcore.id,
            status="ACTIVE",
            ip="10.60.60.2",
            hostname="zcore",
            fqdn="zcore.lab.example.com",
        )
    )
    session.add(zpod)
    session.commit()
    return zpod
