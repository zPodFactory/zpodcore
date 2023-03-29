from fastapi import APIRouter, HTTPException, status

from zpodapi.lib.global_dependencies import GlobalAnnotations, GlobalDepends
from zpodapi.lib.route_logger import RouteLogger

from .endpoint__dependencies import EndpointAnnotations
from .endpoint__schemas import EndpointCreate, EndpointUpdate, EndpointView
from .endpoint__services import EndpointService

router = APIRouter(
    prefix="/endpoints",
    tags=["endpoints"],
    dependencies=[GlobalDepends.UpdateLastConnectionDate],
    route_class=RouteLogger,
)


@router.get(
    "",
    response_model=list[EndpointView],
)
def get_all(
    *,
    session: GlobalAnnotations.GetSession,
):
    return EndpointService(session=session).get_all()


@router.post(
    "",
    response_model=EndpointCreate,
    status_code=status.HTTP_201_CREATED,
)
def create(
    *,
    session: GlobalAnnotations.GetSession,
    endpoint: EndpointCreate,
):
    service = EndpointService(session=session)
    if service.get(value=endpoint.name):
        raise HTTPException(status_code=422, detail="Conflicting record found")
    return service.create(item_in=endpoint)


@router.patch(
    "",
    response_model=EndpointView,
    status_code=status.HTTP_201_CREATED,
)
def update(
    *,
    session: GlobalAnnotations.GetSession,
    endpoint: EndpointAnnotations.GetEndpoint,
    endpoint_in: EndpointUpdate,
):
    return EndpointService(session=session).update(item=endpoint, item_in=endpoint_in)


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete(
    *,
    session: GlobalAnnotations.GetSession,
    endpoint: EndpointAnnotations.GetEndpoint,
):
    EndpointService(session=session).delete(item=endpoint)


@router.put(
    "/{endpoint_name}/verify",
    status_code=status.HTTP_201_CREATED,
)
async def verify(
    *,
    session: GlobalAnnotations.GetSession,
    endpoint_name: str,
):
    # TODO: Add initial verification of JSON endpoint data
    service = EndpointService(session=session)
    if endpoint := service.get(value=endpoint_name):
        return service.verify(item=endpoint)
    raise HTTPException(status_code=404, detail="Endpoint not found")
