from fastapi import Depends, HTTPException
from sqlmodel import Session

from ..lib import dependencies
from . import component_services


def get_component_record(
    *,
    session: Session = Depends(dependencies.get_session),
    filename: str | None = None,
):
    if component := component_services.get(
        session=session,
        filename=filename,
    ):
        return component
    raise HTTPException(status_code=404, detail="Component not found")
