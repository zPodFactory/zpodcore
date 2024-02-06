from fastapi import APIRouter, status

from zpodapi.endpoints.endpoint__dependencies import EndpointAnnotations
from zpodapi.lib.route_logger import RouteLogger

from .endpoint_enet__dependencies import EndpointENetAnnotations
from .endpoint_enet__schemas import EndpointENetCreate, EndpointENetView

router = APIRouter(
    prefix="/endpoints/{id}/enet",
    tags=["endpoints"],
    route_class=RouteLogger,
)


@router.get(
    "",
    response_model=list[EndpointENetView],
)
def enet_get_all(
    *,
    endpoint: EndpointAnnotations.GetEndpoint,
    enet_service: EndpointENetAnnotations.EndpointENetService,
):
    return enet_service.get_all(endpoint=endpoint)


@router.get(
    "/{name}",
    response_model=EndpointENetView,
)
def enet_get(
    *,
    enet: EndpointENetAnnotations.GetEndpointENet,
):
    return enet


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
def enet_create(
    *,
    endpoint: EndpointAnnotations.GetEndpoint,
    enet_service: EndpointENetAnnotations.EndpointENetService,
    enet_in: EndpointENetCreate,
):
    enet_service.create(endpoint=endpoint, name=enet_in.name)


@router.delete(
    "/{name}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def enet_delete(
    *,
    endpoint: EndpointAnnotations.GetEndpoint,
    enet_service: EndpointENetAnnotations.EndpointENetService,
    name: str,
):
    enet_service.delete(endpoint=endpoint, name=name)
