from fastapi import APIRouter, HTTPException, status

from zpodapi.lib.global_dependencies import GlobalDepends
from zpodapi.lib.route_logger import RouteLogger

from .endpoint__dependencies import EndpointAnnotations
from .endpoint__schemas import EndpointCreate, EndpointUpdate, EndpointViewFull

router = APIRouter(
    prefix="/endpoints",
    tags=["endpoints"],
    route_class=RouteLogger,
)


@router.get(
    "",
    response_model=list[EndpointViewFull],
)
def get_all(
    *,
    endpoint_service: EndpointAnnotations.EndpointService,
):
    return endpoint_service.get_all()


@router.get(
    "/{id}",
    response_model=EndpointViewFull,
)
def get(
    *,
    endpoint: EndpointAnnotations.GetEndpoint,
):
    return endpoint


@router.post(
    "",
    response_model=EndpointViewFull,
    status_code=status.HTTP_201_CREATED,
    dependencies=[GlobalDepends.OnlySuperAdmin],
)
def create(
    *,
    endpoint_service: EndpointAnnotations.EndpointService,
    endpoint: EndpointCreate,
):
    if endpoint_service.get(name_insensitive=endpoint.name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Endpoint already exists",
        )
    return endpoint_service.crud.create(item_in=endpoint)


@router.patch(
    "/{id}",
    response_model=EndpointViewFull,
    status_code=status.HTTP_201_CREATED,
    dependencies=[GlobalDepends.OnlySuperAdmin],
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
    dependencies=[GlobalDepends.OnlySuperAdmin],
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
    dependencies=[GlobalDepends.OnlySuperAdmin],
)
async def verify(
    *,
    endpoint_service: EndpointAnnotations.EndpointService,
    endpoint: EndpointAnnotations.GetEndpoint,
):
    # TODO: Add initial verification of JSON endpoint data
    return endpoint_service.verify(item=endpoint)
