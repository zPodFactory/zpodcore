from rich import print
from sqlalchemy.orm.attributes import flag_modified
from sqlmodel import Session, or_, select

from zpodcommon import models as M

from .endpoint__schemas import EndpointCreate, EndpointUpdate
from .endpoint__utils import update_dictionary, zpod_endpoint_check


def get_all(session: Session):
    return session.exec(select(M.Endpoint)).all()


def get(
    session: Session,
    *,
    name: str | None = None,
):
    return session.exec(
        select(M.Endpoint).where(
            or_(
                M.Endpoint.name == name,
            )
        )
    ).first()


def create(session: Session, *, endpoint_in: EndpointCreate):
    endpoint = M.Endpoint(**endpoint_in.dict())
    session.add(endpoint)
    session.commit()
    session.refresh(endpoint)

    return endpoint


def update(session: Session, *, endpoint: M.Endpoint, endpoint_in: EndpointUpdate):
    print(endpoint)
    for key, value in endpoint_in.dict(exclude_unset=True).items():
        # specific code to handle nested dictionaries & JSON fields
        if key == "endpoints":
            update_dictionary(endpoint.endpoints, value)
            value = endpoint.endpoints

        setattr(endpoint, key, value)

    # https://stackoverflow.com/questions/42559434/updates-to-json-field-dont-persist-to-db
    flag_modified(endpoint, "endpoints")
    session.add(endpoint)
    session.commit()
    session.refresh(endpoint)

    return endpoint


def delete(session: Session, *, endpoint: M.Endpoint):
    # Delete Endpoint from DB
    print(f"Deleting {endpoint}")
    session.delete(endpoint)
    session.commit()

    return None


def verify(session: Session, *, endpoint: M.Endpoint):
    # Verify endpoint status
    print(f"Verifying Endpoint {endpoint.name}")

    return zpod_endpoint_check(endpoint)
