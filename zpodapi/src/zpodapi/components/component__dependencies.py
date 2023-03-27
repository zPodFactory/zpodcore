from fastapi import Depends, HTTPException
from sqlmodel import Session

from zpodapi.lib import dependencies

from .component__services import ComponentService


def get_component_record(
    *,
    session: Session = Depends(dependencies.get_session),
    component_uid: str,
):
    if component := ComponentService(session=session).get(value=component_uid):
        return component
    raise HTTPException(status_code=404, detail="Component not found")
