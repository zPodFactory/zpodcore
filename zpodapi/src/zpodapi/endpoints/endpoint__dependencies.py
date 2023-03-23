from fastapi import Depends, HTTPException
from sqlmodel import Session

from zpodapi.lib import dependencies

from . import endpoint__services


async def get_endpoint_record(
    *,
    session: Session = Depends(dependencies.get_session),
    name: str | None = None,
):
    if endpoint := endpoint__services.get(
        session=session,
        name=name,
    ):
        return endpoint
    raise HTTPException(status_code=404, detail="Endpoint not found")
