from fastapi import Depends, HTTPException
from sqlmodel import Session

from zpodapi.lib import dependencies

from .endpoint__services import EndpointService


async def get_endpoint_record(
    *,
    session: Session = Depends(dependencies.get_session),
    name: str | None = None,
):
    if endpoint := EndpointService(session=session).get(value=name):
        return endpoint
    raise HTTPException(status_code=404, detail="Endpoint not found")
