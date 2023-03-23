from fastapi import Depends, HTTPException
from sqlmodel import Session

from zpodapi.lib import dependencies

from . import component__services
from .component__schemas import ComponentUpdate


def get_component_record(
    *,
    session: Session = Depends(dependencies.get_session),
    component_in: ComponentUpdate,
):
    if component := component__services.get(session=session, component_in=component_in):
        return component
    raise HTTPException(status_code=404, detail="Component not found")
