from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from zpodapi.lib import dependencies
from zpodapi.lib.route_logger import RouteLogger
from zpodcommon import models as M

from . import endpoint_dependencies, endpoint_services
from .endpoint_schemas import EndpointCreate, EndpointUpdate, EndpointView

router = APIRouter(
    prefix="/endpoints",
    tags=["endpoints"],
    dependencies=[Depends(dependencies.get_current_user_and_update)],
    route_class=RouteLogger,
)


@router.get(
    "",
    response_model=list[EndpointView],
)
def get_all(
    *,
    session: Session = Depends(dependencies.get_session),
):
    return endpoint_services.get_all(session)


@router.post(
    "",
    response_model=EndpointCreate,
    status_code=status.HTTP_201_CREATED,
)
def create(
    *,
    session: Session = Depends(dependencies.get_session),
    endpoint: EndpointCreate,
):
    if endpoint_services.get(session=session, name=endpoint.name):
        raise HTTPException(status_code=422, detail="Conflicting record found")
    return endpoint_services.create(session=session, endpoint_in=endpoint)


@router.patch(
    "",
    response_model=EndpointView,
    status_code=status.HTTP_201_CREATED,
)
def update(
    *,
    session: Session = Depends(dependencies.get_session),
    endpoint: M.Endpoint = Depends(endpoint_dependencies.get_endpoint_record),
    endpoint_in: EndpointUpdate,
):
    return endpoint_services.update(
        session=session, endpoint=endpoint, endpoint_in=endpoint_in
    )


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete(
    *,
    session: Session = Depends(dependencies.get_session),
    endpoint: M.Endpoint = Depends(endpoint_dependencies.get_endpoint_record),
):
    return endpoint_services.delete(session=session, endpoint=endpoint)


@router.put(
    "/{endpoint_name}/verify",
    status_code=status.HTTP_201_CREATED,
)
async def verify(
    *, session: Session = Depends(dependencies.get_session), endpoint_name: str
):
    # TODO: Add initial verification of JSON endpoint data
    if endpoint := endpoint_services.get(session=session, name=endpoint_name):
        return endpoint_services.verify(session=session, endpoint=endpoint)
    raise HTTPException(status_code=404, detail="Endpoint not found")
