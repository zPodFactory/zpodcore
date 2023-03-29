from typing import Annotated

from fastapi import Depends, HTTPException

from zpodapi.lib.global_dependencies import GlobalAnnotations
from zpodcommon import models as M

from .endpoint__services import EndpointService


async def get_endpoint(
    *,
    session: GlobalAnnotations.GetSession,
    name: str | None = None,
):
    if endpoint := EndpointService(session=session).get(value=name):
        return endpoint
    raise HTTPException(status_code=404, detail="Endpoint not found")


class EndpointDepends:
    GetEndpoint = Depends(get_endpoint)


class EndpointAnnotations:
    GetEndpoint = Annotated[M.Endpoint, EndpointDepends.GetEndpoint]
