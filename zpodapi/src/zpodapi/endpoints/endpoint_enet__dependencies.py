from typing import Annotated

from fastapi import Depends, HTTPException

from zpodapi.lib.global_dependencies import service_init_annotation

from .endpoint__dependencies import EndpointAnnotations
from .endpoint_enet__services import EndpointENetService


def get_endpoint_enet(
    *,
    enet_service: "EndpointENetAnnotations.EndpointENetService",
    endpoint: EndpointAnnotations.GetEndpoint,
    name: str,
):
    if ean := enet_service.get(endpoint=endpoint, name=name):
        return ean
    raise HTTPException(status_code=404, detail="Endpoint ENet not found")


...


class EndpointENetDepends:
    pass


class EndpointENetAnnotations:
    GetEndpointENet = Annotated[dict, Depends(get_endpoint_enet)]
    EndpointENetService = service_init_annotation(EndpointENetService)
