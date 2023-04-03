from typing import Annotated

from fastapi import Depends, HTTPException, Path

from zpodapi.lib.global_dependencies import GlobalAnnotations
from zpodcommon import models as M

from .endpoint__services import EndpointService
from .endpoint__types import EndpointIdType


async def get_endpoint(
    *,
    session: GlobalAnnotations.GetSession,
    id: Annotated[
        EndpointIdType,
        Path(
            examples={
                "id": {"value": "1"},
                "name": {"value": "name=main"},
            },
        ),
    ],
):
    if endpoint := EndpointService(session=session).get(value=id):
        return endpoint
    raise HTTPException(status_code=404, detail="Endpoint not found")


class EndpointDepends:
    GetEndpoint = Depends(get_endpoint)


class EndpointAnnotations:
    GetEndpoint = Annotated[M.Endpoint, EndpointDepends.GetEndpoint]
