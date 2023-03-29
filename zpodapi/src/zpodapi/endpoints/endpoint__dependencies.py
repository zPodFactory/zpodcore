from typing import Annotated

from fastapi import Depends, HTTPException

from zpodapi.lib import dependencies
from zpodcommon import models as M

from .endpoint__services import EndpointService


async def get_endpoint(
    *,
    session: dependencies.GetSession,
    name: str | None = None,
):
    if endpoint := EndpointService(session=session).get(value=name):
        return endpoint
    raise HTTPException(status_code=404, detail="Endpoint not found")


GetEndpointDepends = Depends(get_endpoint)
GetEndpoint = Annotated[M.Endpoint, GetEndpointDepends]
