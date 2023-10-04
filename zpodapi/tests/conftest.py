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
        creation_date="2022-01-01T00:00:00",
        superadmin=True,
        status="ENABLED",
    )
    session.add(superadmin_user)

    normal_user = M.User(
        username="normaluser",
        email="normaluser@zpodfactory.io",
        api_token="APITOKEN_NORMALUSER",
        creation_date="2022-01-01T00:00:00",
        superadmin=False,
        status="ENABLED",
    )
    session.add(normal_user)
    session.commit()
