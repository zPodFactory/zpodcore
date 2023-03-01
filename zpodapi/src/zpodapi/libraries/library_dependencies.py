from fastapi import Depends, HTTPException
from sqlmodel import Session

from zpodapi.lib import dependencies

from . import library_services


async def get_library_record(
    *,
    session: Session = Depends(dependencies.get_session),
    name: str | None = None,
    git_url: str | None = None,
):
    if library := library_services.get(
        session=session,
        name=name,
        git_url=git_url,
    ):
        return library
    raise HTTPException(status_code=404, detail="Library not found")
