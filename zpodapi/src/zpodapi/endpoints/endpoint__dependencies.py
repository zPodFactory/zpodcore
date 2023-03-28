from typing import Annotated

from fastapi import Depends, HTTPException

from zpodapi.lib import dependencies
from zpodcommon import models as M

from .endpoint__services import EndpointService


async def get_endpoint_record(
    *,
    session: dependencies.GetSession,
    name: str | None = None,
):
    if endpoint := EndpointService(session=session).get(value=name):
        return endpoint
    raise HTTPException(status_code=404, detail="Endpoint not found")


GetEndpointRecordDepends = Depends(get_endpoint_record)
GetEndpointRecord = Annotated[M.Endpoint, GetEndpointRecordDepends]
