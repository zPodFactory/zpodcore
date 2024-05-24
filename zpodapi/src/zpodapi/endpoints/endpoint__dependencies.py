from typing import Annotated

from fastapi import Depends, HTTPException, Path, status

from zpodapi.lib.global_dependencies import service_init_annotation
from zpodapi.lib.types import IdNameType
from zpodcommon import models as M

from .endpoint__services import EndpointService


async def get_endpoint(
    *,
    endpoint_service: "EndpointAnnotations.EndpointService",
    id: Annotated[
        IdNameType,
        Path(
            openapi_examples={
                "id": {"value": "1"},
                "name": {"value": "name=main"},
            },
        ),
    ],
):
    if endpoint := endpoint_service.get(**id):
        return endpoint
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Endpoint not found",
    )


class EndpointDepends:
    pass


class EndpointAnnotations:
    GetEndpoint = Annotated[M.Endpoint, Depends(get_endpoint)]
    EndpointService = service_init_annotation(EndpointService)
