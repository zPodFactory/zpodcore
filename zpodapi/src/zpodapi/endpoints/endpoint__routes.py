from fastapi import APIRouter, HTTPException, status

from zpodapi.lib.global_dependencies import GlobalDepends
from zpodapi.lib.route_logger import RouteLogger

from .endpoint__dependencies import EndpointAnnotations
from .endpoint__schemas import EndpointCreate, EndpointUpdate, EndpointView

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
    endpoint_service: EndpointAnnotations.EndpointService,
):
    return endpoint_service.get_all()


@router.post(
    "",
    response_model=EndpointCreate,
    status_code=status.HTTP_201_CREATED,
)
def create(
    *,
    endpoint_service: EndpointAnnotations.EndpointService,
    endpoint: EndpointCreate,
):
    if endpoint_service.get(value=endpoint.name):
        raise HTTPException(status_code=422, detail="Conflicting record found")
    return endpoint_service.create(item_in=endpoint)


@router.patch(
    "/{id}",
    response_model=EndpointView,
    status_code=status.HTTP_201_CREATED,
)
def update(
    *,
    endpoint_service: EndpointAnnotations.EndpointService,
    endpoint: EndpointAnnotations.GetEndpoint,
    endpoint_in: EndpointUpdate,
):
    return endpoint_service.update(item=endpoint, item_in=endpoint_in)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete(
    *,
    endpoint_service: EndpointAnnotations.EndpointService,
    endpoint: EndpointAnnotations.GetEndpoint,
):
    endpoint_service.delete(item=endpoint)


@router.put(
    "/{id}/verify",
    status_code=status.HTTP_201_CREATED,
)
async def verify(
    *,

    endpoint_service: EndpointAnnotations.EndpointService,
    endpoint: EndpointAnnotations.GetEndpoint,
):
    # TODO: Add initial verification of JSON endpoint data
    return endpoint_service.verify(item=endpoint)
